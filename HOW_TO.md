# 이미지 비교 도구 사용 가이드

구글 시트의 이미지 URL을 자동으로 비교하고 결과를 시트에 업데이트하는 도구입니다.

## ⚡ 빠른 시작 (기본 설정 완료 후)

하나의 시트를 처리하려면 다음 2개 명령어만 실행하면 됩니다:

```bash
# 1. 이미지 비교 수행
source venv/bin/activate
python imgdiff_googlesheet_url.py "YOUR_SHEET_ID"

# 2. 결과를 구글 드라이브에 업로드하고 시트 업데이트
python upload_to_drive.py "YOUR_SHEET_ID" --start 3 --end 658
```

**예시:**
```bash
# 시트 ID: 1GjpcVKjSaY7O_ouCuORuTaE7cdzyYmUQYYtGFRDBs-U
source venv/bin/activate
python imgdiff_googlesheet_url.py "1GjpcVKjSaY7O_ouCuORuTaE7cdzyYmUQYYtGFRDBs-U"
python upload_to_drive.py "1GjpcVKjSaY7O_ouCuORuTaE7cdzyYmUQYYtGFRDBs-U" --start 3 --end 658
```

**참고:**
- `--start 3`: 데이터 시작 행 (기본값: 3행)
- `--end 658`: 데이터 종료 행 (시트의 마지막 데이터 행 번호)
- 첫 실행 시 브라우저에서 Google 계정 인증 필요

---

## 📋 목차
1. [⚡ 빠른 시작](#-빠른-시작-기본-설정-완료-후)
2. [사전 준비](#사전-준비)
3. [실행 절차](#실행-절차)
4. [결과 확인](#결과-확인)
5. [문제 해결](#문제-해결)

---

## 🔧 사전 준비

### 1. Python 가상환경 설정

```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate  # Windows
```

### 2. 필요한 라이브러리 설치

```bash
pip install -r requirements.txt
```

필요한 라이브러리:
- Pillow (이미지 처리)
- numpy (수치 연산)
- matplotlib (이미지 시각화)
- requests (URL 이미지 다운로드)
- google-api-python-client (구글 API)
- google-auth-httplib2
- google-auth-oauthlib

### 3. Google Cloud Console 설정

#### 3.1 프로젝트 생성 및 API 활성화

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성
3. 다음 API를 활성화:
   - **Google Sheets API**
   - **Google Drive API**

#### 3.2 OAuth 2.0 인증 정보 생성

1. Cloud Console → "API 및 서비스" → "사용자 인증 정보"
2. "+ 사용자 인증 정보 만들기" → "OAuth 클라이언트 ID"
3. 애플리케이션 유형: "데스크톱 앱"
4. 생성된 인증 정보 다운로드
5. 다운로드한 JSON 파일을 `credentials.json`으로 이름 변경
6. 프로젝트 루트 디렉토리에 저장

### 4. 구글 시트 준비

구글 시트는 다음과 같은 구조여야 합니다:

| A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|
| 행번호 | 이미지1 URL | 이미지2 URL | (자동생성) | (자동생성) | (자동생성) | (자동생성) | (자동생성) |
| 1 | 헤더 | 헤더 | 차이 강조 | 나란히 비교 | 판정 | 차이율 (%) | 변경 픽셀 (%) |
| 2 | | | | | | | |
| 3 | =IMAGE("url1") | =IMAGE("url2") | | | | | |
| 4 | =IMAGE("url1") | =IMAGE("url2") | | | | | |

**중요**:
- B, C 열에는 `=IMAGE("URL")` 형식의 수식 또는 직접 URL이 있어야 합니다
- 데이터는 **3행부터** 시작합니다 (B3:C3부터)

---

## 🚀 실행 절차

### 단계 1: 이미지 비교 수행

구글 시트에서 이미지 URL을 읽어와 비교합니다.

```bash
source venv/bin/activate
python imgdiff_googlesheet_url.py [시트_ID] --range "B3:C10"
```

**매개변수**:
- `[시트_ID]`: 구글 시트 URL의 ID 부분
  - 예: `https://docs.google.com/spreadsheets/d/1GjpcVKj.../edit`
  - → `1GjpcVKj...` 부분만 사용
- `--range`: 비교할 범위 (기본값: B3:C)

**실행 예시**:
```bash
python imgdiff_googlesheet_url.py "1GjpcVKjSaY7O_ouCuORuTaE7cdzyYmUQYYtGFRDBs-U" --range "B3:C10"
```

**처음 실행 시**:
1. 브라우저가 자동으로 열립니다
2. Google 계정으로 로그인
3. "권한 허용" 클릭 (Google Sheets API 권한)
4. 인증 완료 후 자동으로 진행됩니다

**결과**:
- `googlesheet_url_results/` 디렉토리에 비교 결과 저장
- 각 행마다 `row_N/` 폴더 생성:
  - `diff_highlight.png`: 차이점이 강조된 이미지
  - `side_by_side.png`: 두 이미지를 나란히 비교
  - `stats.json`: 통계 정보 (차이율, 변경 픽셀 등)

---

### 단계 2: 구글 시트에 결과 업로드

비교 결과를 Google Drive에 업로드하고 시트를 업데이트합니다.

```bash
python upload_to_drive.py [시트_ID] --start 3 --end 10
```

**매개변수**:
- `[시트_ID]`: 구글 시트 ID (단계 1과 동일)
- `--start`: 시작 행 번호 (기본값: 3)
- `--end`: 종료 행 번호 (기본값: 7)

**실행 예시**:
```bash
python upload_to_drive.py "1GjpcVKjSaY7O_ouCuORuTaE7cdzyYmUQYYtGFRDBs-U" --start 3 --end 10
```

**처음 실행 시**:
1. 브라우저가 자동으로 열립니다
2. Google 계정으로 로그인
3. "권한 허용" 클릭 (Google Drive API 권한 추가 필요)
4. 인증 완료 후 자동으로 진행됩니다

**작업 내용**:
1. Google Drive에 공개 폴더 생성
2. 비교 이미지를 Drive에 업로드
3. 구글 시트 D~H열 업데이트:
   - **D열**: 차이 강조 이미지 (IMAGE 함수)
   - **E열**: 나란히 비교 이미지 (IMAGE 함수)
   - **F열**: 판정 결과 (✅/⚠️/❌)
   - **G열**: 차이율 (%)
   - **H열**: 변경된 픽셀 비율 (%)
4. 행 높이를 150px로 자동 조정
5. 헤더 행(2행) 자동 추가

---

## 📊 결과 확인

### 구글 시트 확인

```
https://docs.google.com/spreadsheets/d/[시트_ID]/edit
```

### 결과 열 설명

| 열 | 내용 | 설명 |
|---|---|---|
| D | 차이 강조 이미지 | 차이가 있는 부분을 빨간색으로 강조 |
| E | 나란히 비교 이미지 | 두 이미지를 나란히 배치 |
| F | 판정 | ✅ 거의 동일 (< 1%)<br>⚠️ 약간 차이 (1~5%)<br>❌ 큰 차이 (> 5%) |
| G | 차이율 (%) | 전체 픽셀 대비 차이 정도 (0~100%) |
| H | 변경 픽셀 (%) | 변경된 픽셀의 비율 (0~100%) |

### 로컬 결과 확인

```bash
# 결과 디렉토리 확인
ls -la googlesheet_url_results/

# 특정 행 결과 확인
open googlesheet_url_results/row_3/diff_highlight.png
open googlesheet_url_results/row_3/side_by_side.png
cat googlesheet_url_results/row_3/stats.json
```

---

## 🔄 전체 워크플로우 요약

```bash
# 1. 가상환경 활성화
source venv/bin/activate

# 2. 이미지 비교 (B, C 열의 URL에서 이미지를 다운로드하여 비교)
python imgdiff_googlesheet_url.py "YOUR_SHEET_ID" --range "B3:C10"

# 3. 결과를 구글 드라이브에 업로드하고 시트 업데이트
python upload_to_drive.py "YOUR_SHEET_ID" --start 3 --end 10

# 4. 구글 시트에서 결과 확인
# https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
```

---

## ❗ 문제 해결

### 1. `ModuleNotFoundError: No module named 'PIL'`

**해결방법**:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 2. `credentials.json` 파일을 찾을 수 없습니다

**해결방법**:
1. Google Cloud Console에서 OAuth 2.0 인증 정보 다운로드
2. 파일 이름을 `credentials.json`으로 변경
3. 프로젝트 루트 디렉토리에 저장

### 3. `Google Drive API has not been used in project`

**해결방법**:
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. "API 및 서비스" → "라이브러리"
3. "Google Drive API" 검색 후 "사용 설정" 클릭
4. 몇 분 대기 후 다시 실행

### 4. 인증 토큰 문제

**해결방법**:
```bash
# 기존 토큰 삭제
rm token.pickle
rm token_drive.pickle

# 스크립트 재실행 (새로 인증)
python imgdiff_googlesheet_url.py "YOUR_SHEET_ID"
```

### 5. 이미지가 시트에 표시되지 않음

**원인**:
- Google Drive 이미지가 비공개 상태
- IMAGE 함수의 URL이 잘못됨

**해결방법**:
1. 스크립트가 자동으로 공개 폴더를 생성합니다
2. 재실행하면 새 폴더가 생성됩니다:
   ```bash
   python upload_to_drive.py "YOUR_SHEET_ID" --start 3 --end 10
   ```

### 6. 행 높이 조정 실패 (`No grid with id: 0`)

**원인**:
- 시트 ID가 0이 아닌 경우 (여러 시트 탭이 있는 경우)

**영향**:
- 이미지와 데이터는 정상적으로 업로드됨
- 행 높이만 수동 조정 필요

**해결방법**:
- 구글 시트에서 행 3~10을 선택 후 마우스 우클릭
- "행 크기 조정" → 150px로 설정

---

## 📝 추가 정보

### 지원하는 이미지 형식
- PNG
- JPEG/JPG
- GIF
- BMP
- WEBP

### 대량 처리

여러 범위를 한 번에 처리:

```bash
# 100개 행 처리
python imgdiff_googlesheet_url.py "YOUR_SHEET_ID" --range "B3:C102"
python upload_to_drive.py "YOUR_SHEET_ID" --start 3 --end 102
```

### 스크립트 옵션

#### `imgdiff_googlesheet_url.py`
```bash
python imgdiff_googlesheet_url.py [SHEET_ID] [옵션]

옵션:
  --range RANGE        읽을 범위 (기본값: B3:C)
  --output-dir DIR     결과 저장 디렉토리 (기본값: googlesheet_url_results)
  --update-sheet       결과를 구글 시트에 업데이트 (텍스트만)
```

#### `upload_to_drive.py`
```bash
python upload_to_drive.py [SHEET_ID] [옵션]

옵션:
  --start START        시작 행 (기본값: 3)
  --end END            종료 행 (기본값: 7)
```

---

## 🎯 빠른 시작 체크리스트

- [ ] Python 3.7 이상 설치
- [ ] 가상환경 생성 및 활성화
- [ ] `pip install -r requirements.txt` 실행
- [ ] Google Cloud Console에서 프로젝트 생성
- [ ] Google Sheets API 활성화
- [ ] Google Drive API 활성화
- [ ] OAuth 2.0 인증 정보 생성
- [ ] `credentials.json` 파일 저장
- [ ] 구글 시트에 B, C 열에 이미지 URL 준비 (3행부터)
- [ ] `imgdiff_googlesheet_url.py` 실행
- [ ] `upload_to_drive.py` 실행
- [ ] 구글 시트에서 결과 확인

---

## 📞 도움말

문제가 계속되면 다음을 확인하세요:

1. Python 버전: `python --version` (3.7 이상 필요)
2. 가상환경 활성화 확인: `which python`
3. 패키지 설치 확인: `pip list | grep Pillow`
4. Google API 활성화 확인
5. 인증 파일 확인: `ls -la credentials.json`

---

**작성일**: 2025-11-08
**버전**: 1.0
