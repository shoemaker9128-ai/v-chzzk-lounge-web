# V-CHZZK · 실시간 버추얼 라운지

치지직(Chzzk)에서 방송 중인 버추얼 스트리머(태그: 버튜버·버츄얼)의 라이브를 모아 보여주는 비공식 팬 페이지입니다.

## 구성

- `index.html` — 라운지 웹앱 (시청자순·팔로워순·랜덤 픽 정렬, 검색, 즐겨찾기)
- `scripts/fetch_data.py` — 치지직 공개 API에서 라이브를 수집해 버추얼 방송만 골라 `data/lives.json` 생성
- `.github/workflows/update-data.yml` — GitHub Actions가 10분마다 수집 스크립트를 실행해 데이터를 갱신

치지직 API는 브라우저의 교차 출처 요청을 허용하지 않아서, 홈페이지가 API를 직접 부르지 않고
Actions가 미리 만들어 둔 JSON 파일만 읽는 방식으로 동작합니다. 그래서 표시되는 정보는 최대 10분 정도 차이가 날 수 있습니다.

## 배포 (GitHub Pages)

1. 이 저장소를 GitHub에 올립니다.
2. Settings → Pages → Build and deployment → Source를 **Deploy from a branch**, Branch를 **main / (root)** 로 설정합니다.
3. Actions 탭에서 "Update live data" 워크플로를 한 번 수동 실행하면 최신 데이터가 채워집니다.
