import os
import json
import logging
import asyncio
import paramiko
import time
from config import settings
from fastapi import FastAPI, HTTPException, Query
from contextlib import contextmanager
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

SCENARIO_BASE = settings.SCENARIO_BASE
API_BASE = settings.API_BASE
PYTHON_PATH = settings.PYTHON_PATH
LOCUST_PATH = settings.LOCUST_PATH

host = settings.SSH_HOST
user = settings.SSH_USER
master_password = settings.SSH_MASTER_PASSWORD
worker_password = settings.SSH_WORKER_PASSWORD

servers = settings.ssh_worker_ips_list
git_user = settings.GIT_USER
git_password = settings.GIT_PASSWORD
git_url = settings.GIT_URL

CURRENT_GROUP_FILE = "/tmp/group.txt"
CURRENT_EXEC_FILE = "/tmp/exec.txt"
CURRENT_SETTING_FILE = "/tmp/setting.txt"
state_lock = asyncio.Lock()

def read_file(filePath : str) -> str | None:
    try:
        with open(filePath, "r") as f:
            read= f.read().strip()
            return read if read else None
    except FileNotFoundError:
        return None

def write_file(filePath: str, content: str | None):
    if content is None:
        open(filePath, "w").close()
    else:
        with open(filePath, "w") as f:
            f.write(content)

@app.get("/")
def read_root():
    return {"message": "200 OK"}


@contextmanager
def ssh_session():
    client = create_ssh_client(
        host,
        settings.SSH_PORT,
        user,
        master_password
    )
    try:
        yield client
    finally:
        client.close()


@app.get("/pull")
def pull_git_remote():
    cmd = f"cd {API_BASE} && git pull https://{git_user}:{git_password}@{git_url}"
    with ssh_session() as client:
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read().decode()
        error = stderr.read().decode()
        logging.info(f"Update scenario: {output}, error : {error}")
        return {"output": output, "error": error}


@app.get("/scenario/list")
def get_scenario_list():
    with ssh_session() as client:
        stdin, stdout, stderr = client.exec_command(f"find {SCENARIO_BASE} -mindepth 1 -maxdepth 1 -type d -printf '%f\n'")
        output = stdout.read().decode()
        error = stderr.read().decode()
        logging.info(f"Scenario list: {output}, error : {error}")
        groups = output.strip().split()
        return {"group": groups}


@app.get("/scenario/{group}/list")
def get_scenario_group_list(group: str):
    check_group(group)
    with ssh_session() as client:
        stdin, stdout, stderr = client.exec_command(f"ls {SCENARIO_BASE}/{group}")
        output = stdout.read().decode()
        error = stderr.read().decode()
        logging.info(f"Scenario list: {output}, error : {error}")
        files = [f for f in output.strip().split() if f.endswith(".py")]
        return {"files": files}

@app.get("/run/{group}")
async def run_remote_command(group: str, fileName: str = Query(...)):
    logging.info(servers)
    check_group(group)

    async with state_lock:
        current = read_file(CURRENT_GROUP_FILE)
        isRun = read_file(CURRENT_SETTING_FILE)
        if current is not None:
            raise HTTPException(409, f"Resource busy: Group {current} is running")
        write_file(CURRENT_GROUP_FILE, group)
        write_file(CURRENT_EXEC_FILE, fileName)
        write_file(CURRENT_SETTING_FILE, "true")

    try:
        file_path = f"{SCENARIO_BASE}/{group}/{fileName}"

        with ssh_session() as client:

            client.exec_command(f"echo '{master_password}' | sudo -S pkill -f locust")
            time.sleep(3)

            for _ in range(5):
                cmd = (
                    f"echo '{master_password}' | sudo -S nohup {PYTHON_PATH} {LOCUST_PATH} -f {file_path} --web-host 0.0.0.0 -P 80 --master > /home/manageuser/stress-api/locust.log 2>&1 &"
                )

                client.exec_command(cmd)
                logging.info("Start locust master")
                time.sleep(4)
                if check_locust_running(client):
                    break
                else:
                    logging.info("Retry start locust master")

            if not check_locust_running(client):
                stdin, stdout, stderr = client.exec_command("cat /home/manageuser/stress-api/locust.log")
                log = stdout.read().decode().strip()
                logging.error(log)
                raise HTTPException(500, detail=f"\nFail to start locust master \nLocust 파이썬 코드에 문제가 있습니다. \n{log}")

        create_locust_worker(group, fileName)

        async with state_lock:
            write_file(CURRENT_SETTING_FILE, "false")

    except Exception as e:
        logging.error(f"/run/{group}: {e}")
        async with state_lock:
            write_file(CURRENT_GROUP_FILE, None)
            write_file(CURRENT_SETTING_FILE, "false")
        raise HTTPException(500, str(e))


@app.get("/process")
def get_process():
    return {"group" : read_file(CURRENT_GROUP_FILE), "file" : read_file(CURRENT_EXEC_FILE), "setting" : read_file(CURRENT_SETTING_FILE)}


@app.get("/stop/{group}")
async def finish(group: str):
    check_group(group)
    async with state_lock:
        current = read_file(CURRENT_GROUP_FILE)
        if current == group:
            write_file(CURRENT_GROUP_FILE, None)
            write_file(CURRENT_EXEC_FILE, None)
            return {"status": "ok", "message": f"Group {group} finished"}
        else:
            raise HTTPException(400, "Cannot finish: no matching running group")

def create_locust_worker(group: str, file: str):
    for ip in servers:
        with ssh_session() as client:
            logging.info(f"[WORKER] {ip}로 전송 및 실행 중...")

            command = f"sshpass -p '{worker_password}' scp {SCENARIO_BASE}/{group}/{file} {user}@{ip}:/home/{user}/"
            client.exec_command(command)
            logging.info(f"worker-{ip} : 파일 전송 완료")

            try:
                a_transport = client.get_transport()
                dest_addr = (ip, 22)
                local_addr = ('127.0.0.1', 0)
                channel = a_transport.open_channel("direct-tcpip", dest_addr, local_addr)
                worker_client = paramiko.SSHClient()
                worker_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                worker_client.connect(ip, port=22, username=user, password=worker_password, sock=channel)

                command = f'echo "{worker_password}" | sudo -S pkill -f locust'
                worker_client.exec_command(command)
                logging.info(f"worker-{ip} : worker 종료 성공")

                for _ in range(5):
                    command = f"echo '{worker_password}' | sudo -S lsof -iTCP:5557 -sTCP:ESTABLISHED -P -n -t  || echo none"
                    stdin, stdout, stderr = worker_client.exec_command(command)
                    pids = stdout.read().decode().strip()
                    pid = pids.splitlines()
                    count = len(pid)
                    logging.info(f"pids : {pids}, pid: {pid}, count:{count}")
                    command = f"nohup locust -f /home/{user}/{file} --worker --master-host {host} --processes 10 > /dev/null 2>&1 &"
                    if pids == 'none':
                        worker_client.exec_command(command)
                        logging.info(f"worker-{ip} : 구성 시도")
                        time.sleep(5)
                    elif 1 < count < 10:
                        logging.info(f"worker-{ip} : 구성 중")
                    elif count == 10:
                        logging.info(f"worker-{ip} : 실행 완료")
                        break

                # 최종 구동 확인
                command = f"echo '{worker_password}' | sudo -S lsof -iTCP:5557 -sTCP:ESTABLISHED -P -n -t || echo none"
                stdin, stdout, stderr = worker_client.exec_command(command)
                pid = stdout.read().decode().strip()
                err = stderr.read().decode().strip()
                logging.info(f"worker-{ip} > pid : {pid}, error: {err}")

                if pid == "none":
                    raise HTTPException(500, f"Failed to start worker : {ip}")

            except Exception as e:
                logging.error(f"B 서버 연결/명령 실행 에러: {e}")
                raise HTTPException(500, f"Failed to start worker : {ip}")
            finally:
                worker_client.close()
                channel.close()

def check_locust_running(client) -> bool:
    stdin, stdout, stderr = client.exec_command(f"echo '{master_password}' | sudo -S lsof -i :80 -sTCP:LISTEN -t || echo none")
    pid = stdout.read().decode().strip()
    logging.info(f"PID: {pid}")
    return pid != 'none'

def create_ssh_client(server, port, user, master_password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, username=user, password=master_password)
    return client


def check_group(group: str):
    groups = get_scenario_list()
    if group not in groups["group"]:
        logging.warning(f"Invalid group: {group}")
        raise HTTPException(404, "Invalid group name")