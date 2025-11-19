# 이미지 비교 도구 사용 가이드 (GCS 버전)

구글 시트의 이미지 URL을 자동으로 비교하고 결과를 Google Cloud Storage에 업로드하여 시트에 업데이트하는 도구입니다.

**🚀 주요 기능:**

- 외곽선 보정으로 미세한 차이 무시하고 중요한 변화만 강조
- Google Cloud Storage 사용으로 빠른 업로드 속도 (Google Drive 대비 4-5배 빠름)
- 병렬 업로드로 대용량 시트 처리 최적화

---

## ⚡ 빠른 시작 (GCS 업로드)

하나의 시트를 처리하려면 다음 2개 명령어만 실행하면 됩니다:

```bash
# 1. 이미지 비교 수행 (외곽선 보정 적용)
source venv/bin/activate
python imgdiff_googlesheet_url.py "YOUR_SHEET_ID" \
  --threshold 40 \
  --morphology-kernel-size 4

# 2. 결과를 Google Cloud Storage에 업로드하고 시트 업데이트
python upload_to_gcs.py "YOUR_SHEET_ID" \
  --start 3 --end 1002 \
  --workers 10 \
  --bucket imgdiff-results
```

**예시:**

```bash
# 시트 ID: 1C72J01zkiiSIDtj55DlBJBcNmL7K7mWsTTMylYlB6Js
source venv/bin/activate

# 텍스트/문서 이미지 비교 (권장 설정)
python imgdiff_googlesheet_url.py "1C72J01zkiiSIDtj55DlBJBcNmL7K7mWsTTMylYlB6Js" \
  --threshold 40 \
  --morphology-kernel-size 4

# GCS 업로드 (10개 병렬 워커로 빠른 처리)
python upload_to_gcs.py "1C72J01zkiiSIDtj55DlBJBcNmL7K7mWsTTMylYlB6Js" \
  --start 3 --end 1002 \
  --workers 10 \
  --bucket imgdiff-results-2025
```

---

## 🆕 GCS 버전의 장점

### Google Drive vs Google Cloud Storage

| 항목           | Google Drive        | Google Cloud Storage |
| -------------- | ------------------- | -------------------- |
| 업로드 속도    | 느림 (순차적)       | 빠름 (병렬)          |
| 1000개 행 처리 | ~30-40분            | ~10-15분             |
| 병렬 워커 수   | 5개 (기본)          | 10개 (기본)          |
| API 제한       | 엄격함              | 관대함               |
| 권한 설정      | 파일마다 설정       | 버킷 단위 설정       |
| 속도 개선      | -                   | 약 4-5배 빠름        |

---

## 🆕 외곽선 보정 기능

### 새로운 파라미터

#### 1. `--threshold` (차이 감지 임계값)

- **기본값**: 40
- **범위**: 0-255
- **효과**: 이 값보다 작은 픽셀 차이는 무시됨
- **높을수록**: 민감도 낮음 (미세한 차이 무시)
- **낮을수록**: 민감도 높음 (작은 차이도 감지)

```bash
# 엄격한 비교 (작은 차이도 감지)
--threshold 20

# 보통 (기본값, 권장)
--threshold 40

# 관대한 비교 (큰 차이만 감지)
--threshold 60
```

#### 2. `--morphology-kernel-size` (형태학적 연산 커널 크기)

- **기본값**: 4
- **범위**: 0 (비활성화), 3, 4, 5, 7, 9...
- **효과**: 미세한 외곽선 노이즈를 제거하고 주요 변경 영역만 강조
- **동작 방식**: Opening 연산 (Erosion → Dilation)을 통해 작은 노이즈 제거

```bash
# 비활성화 (노이즈 제거 안함)
--morphology-kernel-size 0

# 약간의 노이즈 제거 (기본값)
--morphology-kernel-size 4

# 강한 노이즈 제거 (사진/일러스트용)
--morphology-kernel-size 6
```

**형태학적 연산의 효과:**

- 안티앨리어싱으로 인한 1-2픽셀 차이 제거
- 텍스트 외곽선의 미세한 차이 무시
- JPEG 압축 아티팩트 노이즈 제거
- 의미 있는 변경 영역만 강조

#### 3. `--blur-kernel-size` (가우시안 블러 커널 크기)

- **기본값**: 0 (비활성화)
- **범위**: 0 (비활성화), 3, 5, 7, 9...
- **효과**: 외곽선을 부드럽게 처리 (선택적 기능)
- **주의**: 대부분의 경우 morphology만으로 충분하며, 이 옵션은 필요시에만 사용

```bash
# 비활성화 (권장, 기본값)
--blur-kernel-size 0

# 외곽선 부드럽게 (필요시에만)
--blur-kernel-size 5
```

---

## 🎯 이미지 유형별 권장 설정

### 텍스트/문서 (PDF, 워드 등)

```bash
python imgdiff_googlesheet_url.py "SHEET_ID" \
  --threshold 40 \
  --morphology-kernel-size 4 \
  --blur-kernel-size 0
```

- **이유**: 텍스트 외곽선의 안티앨리어싱 차이를 무시하면서 내용 변경 감지

### 사진/일러스트

```bash
python imgdiff_googlesheet_url.py "SHEET_ID" \
  --threshold 50 \
  --morphology-kernel-size 6 \
  --blur-kernel-size 0
```

- **이유**: JPEG 압축 노이즈와 미세한 색상 차이를 무시하면서 실질적인 변경만 감지

### UI/웹사이트 스크린샷

```bash
python imgdiff_googlesheet_url.py "SHEET_ID" \
  --threshold 40 \
  --morphology-kernel-size 4 \
  --blur-kernel-size 0
```

- **이유**: 안티앨리어싱과 렌더링 차이를 무시하면서 레이아웃/콘텐츠 변경 감지

### 엄격한 비교 (픽셀 퍼펙트)

```bash
python imgdiff_googlesheet_url.py "SHEET_ID" \
  --threshold 15 \
  --morphology-kernel-size 0 \
  --blur-kernel-size 0
```

- **이유**: 모든 차이를 감지해야 할 때 (디자인 검수 등)

---

## 🔄 전체 워크플로우 (GCS 버전)

```bash
# 1. 가상환경 활성화
source venv/bin/activate

# 2. 이미지 비교 (외곽선 보정 적용)
python imgdiff_googlesheet_url.py "YOUR_SHEET_ID" \
  --range "B3:C10" \
  --threshold 40 \
  --morphology-kernel-size 4

# 3. 결과를 GCS에 업로드하고 시트 업데이트 (병렬 처리)
python upload_to_gcs.py "YOUR_SHEET_ID" \
  --start 3 --end 10 \
  --workers 10 \
  --bucket imgdiff-results

# 4. 구글 시트에서 결과 확인
# https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit

# 5. GCS 버킷에서 이미지 확인
# https://console.cloud.google.com/storage/browser/imgdiff-results
```

---

## 📋 전체 명령어 옵션

### `imgdiff_googlesheet_url.py`

```bash
python imgdiff_googlesheet_url.py [SHEET_ID] [옵션]

필수 인자:
  SHEET_ID                    구글 시트 ID

선택 옵션:
  --range RANGE               읽을 범위 (기본값: B3:C)
  --output-dir DIR            결과 저장 디렉토리 (기본값: googlesheet_url_results)
  --update-sheet              결과를 구글 시트에 업데이트 (텍스트만)

  외곽선 보정 옵션:
  --threshold INT             차이 감지 임계값 (기본값: 40, 높을수록 민감도 낮음)
  --morphology-kernel-size INT 형태학적 연산 커널 크기 (기본값: 4, 0이면 비활성화)
  --blur-kernel-size INT      가우시안 블러 커널 크기 (기본값: 0, 0이면 비활성화)
```

### `upload_to_gcs.py` (GCS 버전)

```bash
python upload_to_gcs.py [SHEET_ID] [옵션]

필수 인자:
  SHEET_ID                    구글 시트 ID

선택 옵션:
  --bucket BUCKET             GCS 버킷 이름 (기본값: imgdiff-results)
  --start START               시작 행 (기본값: 3)
  --end END                   종료 행 (기본값: 7)
  --workers WORKERS           병렬 워커 수 (기본값: 10)
```

**병렬 워커 수 권장:**

- 소규모 (< 100개): `--workers 5`
- 중규모 (100-500개): `--workers 10`
- 대규모 (> 500개): `--workers 15-20`

---

## 💡 사용 팁

### 1. 최적의 설정 찾기

먼저 몇 개 행으로 테스트해보세요:

```bash
# 3-10행만 테스트
python imgdiff_googlesheet_url.py "SHEET_ID" --range "B3:C10" \
  --threshold 40 --morphology-kernel-size 4

# 테스트 결과를 GCS에 업로드
python upload_to_gcs.py "SHEET_ID" --start 3 --end 10 --workers 5
```

결과를 확인하고 다음과 같이 조정:

- **빨간색이 너무 많다면**: threshold를 높이거나 morphology-kernel-size를 증가
- **변경사항을 놓친다면**: threshold를 낮추거나 morphology-kernel-size를 감소

### 2. 대용량 시트 처리

1000개 이상의 행을 처리할 때:

```bash
# 이미지 비교 (백그라운드 실행 권장)
nohup python imgdiff_googlesheet_url.py "SHEET_ID" \
  --threshold 40 --morphology-kernel-size 4 > imgdiff.log 2>&1 &

# 완료 후 GCS 업로드 (높은 병렬성)
python upload_to_gcs.py "SHEET_ID" \
  --start 3 --end 1002 \
  --workers 15 \
  --bucket imgdiff-results
```

### 3. 배치별 처리

시트가 너무 클 경우 여러 배치로 나누어 처리:

```bash
# 배치 1: 3-250행
python upload_to_gcs.py "SHEET_ID" --start 3 --end 250 --workers 10

# 배치 2: 251-500행
python upload_to_gcs.py "SHEET_ID" --start 251 --end 500 --workers 10

# 배치 3: 501-750행
python upload_to_gcs.py "SHEET_ID" --start 501 --end 750 --workers 10
```

---

## 🔧 사전 준비 (처음 사용시)

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
- opencv-python (외곽선 보정)
- google-api-python-client (구글 API)
- google-auth-httplib2
- google-auth-oauthlib
- **google-cloud-storage (GCS)** 🆕

### 3. Google Cloud Console 설정

#### A. 프로젝트 및 API 설정

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 (또는 기존 프로젝트 선택)
3. **Google Sheets API** 활성화
4. **Google Cloud Storage API** 활성화 🆕
5. OAuth 2.0 인증 정보 생성
6. `credentials.json` 파일 다운로드 및 프로젝트 루트에 저장

#### B. GCS 버킷 생성 및 설정

1. **버킷 생성**:
   - [Cloud Storage](https://console.cloud.google.com/storage) 이동
   - "버킷 만들기" 클릭
   - 버킷 이름: `imgdiff-results` (또는 원하는 이름)
   - 위치: `asia-northeast3` (서울) 권장
   - 스토리지 클래스: Standard
   - 액세스 제어: Uniform (권장)
   - "만들기" 클릭

2. **버킷 공개 설정** (이미지가 시트에 표시되려면 필수):
   - 생성한 버킷 선택
   - "권한" 탭 이동
   - "주 구성원 추가" 클릭
   - 새 주 구성원: `allUsers`
   - 역할: `Storage 객체 뷰어` (Storage Object Viewer)
   - "저장" 클릭

3. **사용자 권한 추가**:
   - "권한" 탭에서 "주 구성원 추가" 클릭
   - 새 주 구성원: `YOUR_EMAIL@gmail.com` (본인 이메일)
   - 역할: `Storage 관리자` (Storage Admin)
   - "저장" 클릭

4. **결제 계정 활성화**:
   - GCS 사용을 위해 결제 계정이 활성화되어야 합니다
   - [결제](https://console.cloud.google.com/billing) 페이지에서 설정
   - 무료 티어: 월 5GB 저장소, 1GB 네트워크 송신 무료

#### C. OAuth 2.0 인증 범위 설정

`credentials.json` 생성 시 다음 범위가 포함되어야 합니다:

- `https://www.googleapis.com/auth/spreadsheets`
- `https://www.googleapis.com/auth/devstorage.full_control` 🆕

### 4. 구글 시트 준비

구글 시트는 다음과 같은 구조여야 합니다:

| A      | B              | C              | D          | E           | F          | G          | H             |
| ------ | -------------- | -------------- | ---------- | ----------- | ---------- | ---------- | ------------- |
| 행번호 | 이미지1 URL    | 이미지2 URL    | (자동생성) | (자동생성)  | (자동생성) | (자동생성) | (자동생성)    |
| 1      | 헤더           | 헤더           | 차이 강조  | 나란히 비교 | 판정       | 차이율 (%) | 변경 픽셀 (%) |
| 2      |                |                |            |             |            |            |               |
| 3      | =IMAGE("url1") | =IMAGE("url2") |            |             |            |            |               |

### 5. 초기 인증

첫 실행 시 OAuth 인증이 필요합니다:

```bash
source venv/bin/activate
python upload_to_gcs.py "YOUR_SHEET_ID" --start 3 --end 3
```

- 브라우저가 자동으로 열림
- Google 계정으로 로그인
- 권한 허용 클릭
- `token_gcs.pickle` 파일이 자동 생성됨 (이후 재인증 불필요)

---

## 📊 결과 확인

### 생성되는 파일

각 행마다 `googlesheet_url_results/row_N/` 폴더에:

- **`diff_highlight.png`**: 차이점이 빨간색으로 강조된 이미지 (외곽선 보정 적용)
- **`side_by_side.png`**: 4개 패널로 나란히 비교 (오른쪽 패널에 외곽선 보정 적용)
  - 패널 1: 이미지 1
  - 패널 2: 이미지 2
  - 패널 3: 픽셀 차이
  - 패널 4: 변경 영역 강조 (외곽선 보정 적용)
- **`stats.json`**: 통계 정보

### GCS 버킷 구조

```
imgdiff-results/
├── imgdiff/
│   ├── row3_diff.png
│   ├── row3_comparison.png
│   ├── row4_diff.png
│   ├── row4_comparison.png
│   └── ...
```

### 결과 열 설명

구글 시트에 업데이트되는 정보:

| 열  | 내용               | 설명                                                            |
| --- | ------------------ | --------------------------------------------------------------- |
| D   | 차이 강조 이미지   | 차이가 있는 부분을 빨간색으로 강조 (외곽선 보정 적용)           |
| E   | 나란히 비교 이미지 | 두 이미지를 나란히 배치                                         |
| F   | 판정               | ✅ 거의 동일 (< 1%)<br>⚠️ 약간 차이 (1~5%)<br>❌ 큰 차이 (> 5%) |
| G   | 차이율 (%)         | 전체 픽셀 대비 차이 정도 (0~100%)                               |
| H   | 변경 픽셀 (%)      | 변경된 픽셀의 비율 (0~100%)                                     |

---

## ❗ 문제 해결

### 1. GCS 버킷을 찾을 수 없음 (404 오류)

```
Error: The specified bucket does not exist
```

**해결 방법**:
- 버킷이 생성되었는지 확인: https://console.cloud.google.com/storage
- 결제 계정이 활성화되었는지 확인
- 버킷 이름이 올바른지 확인

### 2. 권한 부족 (403 오류)

```
Error: does not have storage.objects.create access
```

**해결 방법**:
- 버킷 권한 탭에서 본인 이메일에 "Storage 관리자" 역할 추가
- OAuth 토큰 재생성: `rm token_gcs.pickle` 후 재실행

### 3. Cloud Storage API가 비활성화됨

```
Error: Cloud Storage API has not been used in project
```

**해결 방법**:
- [API 라이브러리](https://console.cloud.google.com/apis/library)에서 "Cloud Storage API" 검색 후 활성화

### 4. 이미지가 시트에 표시되지 않음

**해결 방법**:
- 버킷이 공개로 설정되었는지 확인 (allUsers에게 Storage Object Viewer 권한)
- 이미지 URL이 `https://storage.googleapis.com/...` 형식인지 확인
- 브라우저에서 이미지 URL 직접 접속 테스트

### 5. OpenCV 설치 오류

```bash
# OpenCV 재설치
source venv/bin/activate
pip install --upgrade opencv-python
```

### 6. 외곽선 보정이 너무 약하거나 강한 경우

```bash
# 보정이 약하다면 (빨간색이 여전히 많음)
--threshold 50 --morphology-kernel-size 6

# 보정이 강하다면 (변경사항을 놓침)
--threshold 30 --morphology-kernel-size 3
```

### 7. 프로젝트 ID를 찾을 수 없음

**해결 방법**:
- `credentials.json` 파일에 `project_id`가 포함되어 있는지 확인
- 없다면 실행 시 프로젝트 ID를 수동으로 입력하라는 프롬프트가 표시됨
- [Cloud Console](https://console.cloud.google.com/)에서 프로젝트 ID 확인 가능

---

## 💰 비용 안내

### Google Cloud Storage 요금

**무료 티어** (항상 무료):
- 저장소: 월 5GB
- 네트워크 송신: 월 1GB (북미)
- 클래스 A 작업: 월 5,000회
- 클래스 B 작업: 월 50,000회

**일반적인 사용량 예시**:
- 1000개 이미지 (각 500KB): 약 500MB 저장소
- 월 조회수 10,000회: 무료 범위 내
- **예상 비용**: 무료 또는 월 $0.01 미만

**비용 절감 팁**:
- 오래된 결과는 정기적으로 삭제
- 이미지 압축 품질 조정
- 필요 없는 버전은 수명 주기 정책으로 자동 삭제

### Google Drive vs GCS 비용 비교

| 항목     | Google Drive       | Google Cloud Storage  |
| -------- | ------------------ | --------------------- |
| 저장소   | 15GB 무료          | 5GB 무료 (항상)       |
| 초과 시  | $1.99/월 (100GB)   | $0.02/GB/월           |
| 속도     | 느림               | 빠름                  |
| API 제한 | 엄격               | 관대                  |
| 권장용도 | 개인 파일          | 대용량 데이터, 웹호스팅 |

---

## 🎯 빠른 시작 체크리스트

- [ ] Python 3.7 이상 설치
- [ ] 가상환경 생성 및 활성화
- [ ] `pip install -r requirements.txt` 실행 (google-cloud-storage 포함)
- [ ] Google Cloud Console에서 프로젝트 생성
- [ ] Google Sheets API 활성화
- [ ] **Google Cloud Storage API 활성화** 🆕
- [ ] **결제 계정 활성화** 🆕
- [ ] OAuth 2.0 인증 정보 생성
- [ ] `credentials.json` 파일 저장
- [ ] **GCS 버킷 생성 (예: imgdiff-results)** 🆕
- [ ] **버킷을 공개로 설정 (allUsers → Storage Object Viewer)** 🆕
- [ ] **본인 계정에 Storage 관리자 권한 추가** 🆕
- [ ] 구글 시트에 B, C 열에 이미지 URL 준비 (3행부터)
- [ ] 외곽선 보정 파라미터 결정 (이미지 유형별 권장 설정 참고)
- [ ] `imgdiff_googlesheet_url.py` 실행 (외곽선 보정 적용)
- [ ] `upload_to_gcs.py` 실행 (초기 인증 진행)
- [ ] 구글 시트에서 결과 확인
- [ ] GCS 버킷에서 이미지 확인

---

## 🔬 성능 비교

### 1000개 행 처리 시간 비교

| 방식                      | 시간     | 병렬 워커 | 비고                     |
| ------------------------- | -------- | --------- | ------------------------ |
| Google Drive (순차)       | ~45분    | 1         | 기존 방식                |
| Google Drive (병렬 5개)   | ~30분    | 5         | 개선 버전                |
| **GCS (병렬 10개)**       | ~12분    | 10        | **권장 (4배 빠름)** ✅   |
| GCS (병렬 20개)           | ~8분     | 20        | 네트워크 환경에 따라 다름 |

---

## 📞 도움말

문제가 계속되면 다음을 확인하세요:

1. Python 버전: `python --version` (3.7 이상 필요)
2. 가상환경 활성화 확인: `which python`
3. OpenCV 설치 확인: `pip show opencv-python`
4. GCS 라이브러리 확인: `pip show google-cloud-storage`
5. GCS 버킷 존재 확인: https://console.cloud.google.com/storage
6. 버킷 권한 확인: 공개 설정 및 본인 Storage 관리자 권한
7. Cloud Storage API 활성화 확인: https://console.cloud.google.com/apis/library

---

**작성일**: 2025-11-19
**버전**: 3.0 (GCS 업로드 버전)
**변경사항**:

- Google Drive → Google Cloud Storage 변경
- 병렬 업로드 최적화 (10개 워커 기본)
- 약 4-5배 빠른 처리 속도
- GCS 버킷 설정 및 권한 관리 추가
- 비용 안내 및 성능 비교 추가

---

## 요청시 처리할 기본 값

- threshold: 40
- morphology_kernel_size: 4
- blur_kernel_size: 0
- bucket: imgdiff-results
- workers: 10
