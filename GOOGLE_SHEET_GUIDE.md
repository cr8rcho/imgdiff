# 구글 시트 & CSV 연동 가이드

이미지 비교 도구를 구글 시트 또는 CSV 파일과 연동해서 대량의 이미지를 자동으로 비교할 수 있습니다.

## 📋 CSV 파일 사용법

### 1. CSV 파일 준비

CSV 파일은 다음과 같은 형식으로 준비합니다:

```csv
image1_path,image2_path,name,description
path/to/image1.png,path/to/image2.png,테스트1,첫 번째 비교
path/to/imageA.jpg,path/to/imageB.jpg,테스트2,두 번째 비교
```

- **필수 컬럼**: 첫 번째(이미지1 경로), 두 번째(이미지2 경로)
- **선택 컬럼**: 세 번째(이름), 네 번째(설명)

### 2. CSV 비교 실행

```bash
# 가상환경 활성화
source venv/bin/activate

# CSV 파일 기반 비교 실행
python imgdiff_csv.py sample_images.csv

# 출력 디렉토리 지정
python imgdiff_csv.py sample_images.csv --output-dir my_results
```

### 3. 결과 확인

비교가 완료되면 다음 파일들이 생성됩니다:

- `summary_report.html` - 웹 브라우저로 볼 수 있는 종합 리포트
- `results.csv` - 결과 데이터 CSV 파일
- `results.json` - JSON 형식 결과 데이터
- `row_N_name/` - 각 비교별 개별 결과 폴더
  - `diff_highlight.png` - 차이 강조 이미지
  - `report.txt` - 텍스트 리포트

## 📊 구글 시트 사용법

### 1. 구글 API 설정

1. [구글 클라우드 콘솔](https://console.cloud.google.com) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. "API 및 서비스" → "라이브러리" 이동
4. "Google Sheets API" 검색 후 활성화
5. "사용자 인증 정보" → "사용자 인증 정보 만들기" → "OAuth 클라이언트 ID"
6. 애플리케이션 유형: "데스크톱"
7. `credentials.json` 다운로드

### 2. 구글 시트 준비

구글 시트를 다음과 같이 준비합니다:

#### 기본 형식 (B3:C부터 시작)
- **B3**: 첫 번째 이미지 경로
- **C3**: 두 번째 이미지 경로
- **D3~**: 결과가 자동으로 입력될 위치

예시:
|   | B열 (이미지1) | C열 (이미지2) | D열 (상태) | E열 (차이율) |
|---|--------------|--------------|-----------|-------------|
| 3 | image1.png | image2.png | (자동입력) | (자동입력) |
| 4 | v1_001.png | v2_001.png | (자동입력) | (자동입력) |

### 3. 필요 패키지 설치

```bash
# 구글 API 패키지 설치
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 4. 구글 시트 연동 실행

```bash
# 구글 시트 ID는 URL에서 확인
# https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit

# 기본 실행 (B3:C 범위 읽기, D3부터 결과 입력)
python imgdiff_googlesheet.py YOUR_SPREADSHEET_ID

# 커스텀 범위 지정
python imgdiff_googlesheet.py YOUR_SPREADSHEET_ID --range "Sheet2!E5:F"

# 결과를 구글 시트에 업데이트 (D3부터 입력)
python imgdiff_googlesheet.py YOUR_SPREADSHEET_ID --update-sheet

# 결과 입력 위치 지정
python imgdiff_googlesheet.py YOUR_SPREADSHEET_ID --update-sheet --result-column G --result-row 5
```

처음 실행시 브라우저가 열리며 구글 계정 인증을 요청합니다.

### 5. 결과 확인

- **로컬 파일**: `googlesheet_results/` 폴더에 결과 저장
- **구글 시트**: `--update-sheet` 옵션 사용시 D열부터 결과 자동 입력 (B3:C 기준)
  - D열: 상태 (성공/실패)
  - E열: 차이율 (%)
  - F열: 변경된 픽셀 (%)
  - G열: 비고/오류 메시지
  - H열: 처리 시간

## 🔧 고급 사용법

### 배치 처리 스크립트 예제

```python
from imgdiff_csv import CSVImageComparator

# CSV 파일 목록
csv_files = ['batch1.csv', 'batch2.csv', 'batch3.csv']

for csv_file in csv_files:
    comparator = CSVImageComparator(csv_file, f"results_{csv_file[:-4]}")
    image_pairs = comparator.read_csv()
    comparator.compare_images_batch(image_pairs)
    comparator.generate_summary_report()
```

### 자동화 스케줄링 (cron)

```bash
# 매일 오전 3시에 실행
0 3 * * * cd /path/to/imgdiff && source venv/bin/activate && python imgdiff_csv.py daily_images.csv
```

### 웹훅 연동 예제

```python
import requests

# 비교 실행 후 결과를 웹훅으로 전송
def send_webhook_notification(results):
    webhook_url = "YOUR_WEBHOOK_URL"

    summary = {
        'total': len(results),
        'success': sum(1 for r in results if r['status'] == 'success'),
        'failed': sum(1 for r in results if r['status'] == 'error'),
        'timestamp': datetime.now().isoformat()
    }

    requests.post(webhook_url, json=summary)
```

## 📝 주의사항

1. **경로 확인**: 이미지 경로는 절대 경로 또는 현재 디렉토리 기준 상대 경로 사용
2. **파일 크기**: 대용량 이미지는 처리 시간이 오래 걸릴 수 있음
3. **메모리 사용**: 많은 이미지를 한 번에 처리할 때 메모리 사용량 주의
4. **API 제한**: 구글 시트 API는 분당 요청 제한이 있음

## 🚀 활용 예시

- **QA 테스팅**: UI 스크린샷 자동 비교
- **버전 관리**: 디자인 시안 버전별 차이 확인
- **품질 검사**: 제품 이미지 일관성 검증
- **모니터링**: 웹사이트 스크린샷 변화 감지

## 📚 문제 해결

### "ModuleNotFoundError: No module named 'google'"
```bash
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### "FileNotFoundError: credentials.json"
구글 클라우드 콘솔에서 OAuth 2.0 클라이언트 ID를 생성하고 credentials.json 파일을 다운로드하세요.

### "HttpError 403: Request had insufficient authentication scopes"
token.pickle 파일을 삭제하고 다시 인증하세요:
```bash
rm token.pickle
python imgdiff_googlesheet.py YOUR_SPREADSHEET_ID
```