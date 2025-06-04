stress-senario 하위의 디렉터리가 그룹으로 생성됩니다.
<br>

각 그룹 내부의 .py의 파일들이 Locust에 세팅될 시나리오 목록으로 구성됩니다.


이동을 눌러 세팅된 부하 발생기 (Locust) UI로 이동합니다.
<br>
https://stress1.example.com/

<br>

## UI 구성 및 주요 기능

> 웹 UI는 크게 다음 영역으로 나뉩니다.


### - 부하 테스트 시작 설정

- **Number of users to simulate**  
  부하를 발생시킬 가상의 사용자 수를 입력합니다. 예: `100`

- **Spawn rate (users spawned/second)**  
  초당 생성할 사용자 수를 입력합니다. 예: `10`  
  이 값이 클수록 빠르게 사용자가 증가합니다.

- **Host**  
  python 코드에 host를 명시할 경우 URL이 자동으로 세팅되어 있을 수 있습니다.
  호출 부에 host가 하드 코딩 되어 있다면 '' 를 입력합니다.
  필요 시 직접 변경 가능합니다.

### - 테스트 시작 버튼

- **Start swarming** 버튼을 클릭하면 설정한 사용자 수만큼 가상 사용자가 생성되어 테스트가 시작됩니다.

<br>

## 테스트 실행 중 모니터링

테스트가 실행되면 UI에 실시간 정보가 표시됩니다.

<br>

## 세부 요청 통계 보기

Statistics 탭에서 개별 요청 별 통계를 확인할 수 있습니다.

- 각 API 또는 URL 별 요청 건수, 성공/실패 수, 응답 시간 분포를 확인할 수 있습니다.

- **Requests**
초당 처리되는 요청 수

- **Fails**
실패한 요청 수 및 비율

- **Median**
응답 시간의 중앙값 (ms)

- **95%lie (ms) - 95th percentile response time**
95%의 요청이 이 시간 이내에 응답 받았음을 의미 (ms)

- **90%lie (ms) - 90th percentile response time**
90%의 요청이 이 시간 이내에 응답 받았음을 의미 (ms)

- **Average (ms) - Average response time**
평균 응답 시간 (ms)

- **Min (ms)**
최소 응답 시간 (ms)

- **Max (ms)**
최대 응답 시간 (ms)

- **Current RPS**
현재 초 당 Request 수

- **Current Failures/s**
현재 초 당 실패한 Request 수

<br>

## 테스트 종료 및 결과 확인

- **Stop** 버튼을 클릭하면 테스트가 종료됩니다.

- 테스트 종료 후에도 통계 데이터는 UI에 남아 있으므로 결과를 분석할 수 있습니다.

- Download Data 탭 > Download Report를 통해 리포트를 생성할 수 있습니다.

<br>

## 추가 팁

- 테스트 중간에도 사용자 수나 생성 속도를 조절할 수 있습니다.  
- 실패 요청이 발생하면 원인 분석을 위해 로그 확인이 필요합니다.  
- 여러 시나리오가 있을 경우, 스크립트 내 태스크에 따라 자동으로 분기되어 테스트 됩니다.

<br>
필요시 아래 주소에서 공식 문서를 참고하세요:  
https://docs.locust.io/en/2.20.1/
