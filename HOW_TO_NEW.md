# 이미지 비교 도구 사용 가이드 (외곽선 보정 기능 추가)

구글 시트의 이미지 URL을 자동으로 비교하고 결과를 시트에 업데이트하는 도구입니다.

**🆕 새로운 기능: 외곽선 보정**

- 미세한 색상 차이(안티앨리어싱 등)를 무시하고 중요한 변화만 강조
- 형태학적 연산을 통한 노이즈 제거
- 이미지 유형에 따른 최적화된 설정 제공

---

## ⚡ 빠른 시작 (외곽선 보정 적용)

하나의 시트를 처리하려면 다음 2개 명령어만 실행하면 됩니다:

```bash
# 1. 이미지 비교 수행 (외곽선 보정 적용)
source venv/bin/activate
python imgdiff_googlesheet_url.py "YOUR_SHEET_ID" \
  --threshold 30 \
  --morphology-kernel-size 3

# 2. 결과를 구글 드라이브에 업로드하고 시트 업데이트
python upload_to_drive.py "YOUR_SHEET_ID" --start 3 --end 658
```

**예시:**

```bash
# 시트 ID: 1GjpcVKjSaY7O_ouCuORuTaE7cdzyYmUQYYtGFRDBs-U
source venv/bin/activate

# 텍스트/문서 이미지 비교 (권장 설정)
python imgdiff_googlesheet_url.py "1GjpcVKjSaY7O_ouCuORuTaE7cdzyYmUQYYtGFRDBs-U" \
  --threshold 30 \
  --morphology-kernel-size 3

python upload_to_drive.py "1GjpcVKjSaY7O_ouCuORuTaE7cdzyYmUQYYtGFRDBs-U" --start 3 --end 658
```

---

## 🆕 외곽선 보정 기능 상세 설명

### 새로운 파라미터

#### 1. `--threshold` (차이 감지 임계값)

- **기본값**: 30
- **범위**: 0-255
- **효과**: 이 값보다 작은 픽셀 차이는 무시됨
- **높을수록**: 민감도 낮음 (미세한 차이 무시)
- **낮을수록**: 민감도 높음 (작은 차이도 감지)

```bash
# 엄격한 비교 (작은 차이도 감지)
--threshold 15

# 보통 (기본값, 권장)
--threshold 30

# 관대한 비교 (큰 차이만 감지)
--threshold 50
```

#### 2. `--morphology-kernel-size` (형태학적 연산 커널 크기)

- **기본값**: 3
- **범위**: 0 (비활성화), 3, 5, 7, 9...
- **효과**: 미세한 외곽선 노이즈를 제거하고 주요 변경 영역만 강조
- **동작 방식**: Opening 연산 (Erosion → Dilation)을 통해 작은 노이즈 제거

```bash
# 비활성화 (노이즈 제거 안함)
--morphology-kernel-size 0

# 약간의 노이즈 제거 (기본값)
--morphology-kernel-size 3

# 강한 노이즈 제거 (사진/일러스트용)
--morphology-kernel-size 5
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
  --threshold 30 \
  --morphology-kernel-size 3 \
  --blur-kernel-size 0
```

- **이유**: 텍스트 외곽선의 안티앨리어싱 차이를 무시하면서 내용 변경 감지

### 사진/일러스트

```bash
python imgdiff_googlesheet_url.py "SHEET_ID" \
  --threshold 40 \
  --morphology-kernel-size 5 \
  --blur-kernel-size 0
```

- **이유**: JPEG 압축 노이즈와 미세한 색상 차이를 무시하면서 실질적인 변경만 감지

### UI/웹사이트 스크린샷

```bash
python imgdiff_googlesheet_url.py "SHEET_ID" \
  --threshold 30 \
  --morphology-kernel-size 3 \
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

## 🔄 전체 워크플로우 (외곽선 보정 적용)

```bash
# 1. 가상환경 활성화
source venv/bin/activate

# 2. 이미지 비교 (외곽선 보정 적용)
python imgdiff_googlesheet_url.py "YOUR_SHEET_ID" \
  --range "B3:C10" \
  --threshold 30 \
  --morphology-kernel-size 3

# 3. 결과를 구글 드라이브에 업로드하고 시트 업데이트
python upload_to_drive.py "YOUR_SHEET_ID" --start 3 --end 10

# 4. 구글 시트에서 결과 확인
# https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
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

  🆕 외곽선 보정 옵션:
  --threshold INT             차이 감지 임계값 (기본값: 30, 높을수록 민감도 낮음)
  --morphology-kernel-size INT 형태학적 연산 커널 크기 (기본값: 3, 0이면 비활성화)
  --blur-kernel-size INT      가우시안 블러 커널 크기 (기본값: 0, 0이면 비활성화)
```

### `upload_to_drive.py`

```bash
python upload_to_drive.py [SHEET_ID] [옵션]

필수 인자:
  SHEET_ID                    구글 시트 ID

선택 옵션:
  --start START               시작 행 (기본값: 3)
  --end END                   종료 행 (기본값: 7)
```

---

## 💡 사용 팁

### 1. 최적의 설정 찾기

먼저 몇 개 행으로 테스트해보세요:

```bash
# 3-10행만 테스트
python imgdiff_googlesheet_url.py "SHEET_ID" --range "B3:C10" \
  --threshold 30 --morphology-kernel-size 3
```

결과를 확인하고 다음과 같이 조정:

- **빨간색이 너무 많다면**: threshold를 높이거나 morphology-kernel-size를 증가
- **변경사항을 놓친다면**: threshold를 낮추거나 morphology-kernel-size를 감소

### 2. 비교: 보정 전 vs 후

```bash
# 보정 없이 (기존 방식)
python imgdiff_googlesheet_url.py "SHEET_ID" --range "B3:C5" \
  --threshold 20 --morphology-kernel-size 0 \
  --output-dir "results_old"

# 보정 적용 (새 방식)
python imgdiff_googlesheet_url.py "SHEET_ID" --range "B3:C5" \
  --threshold 30 --morphology-kernel-size 3 \
  --output-dir "results_new"
```

### 3. 배치 처리 설정

큰 시트를 처리할 때 권장:

```bash
# 텍스트/문서가 주를 이루는 경우
python imgdiff_googlesheet_url.py "SHEET_ID" \
  --threshold 30 \
  --morphology-kernel-size 3
```

---

## 🔬 외곽선 보정 원리

### 문제점

기존 방식은 픽셀 단위로 절대 차이를 계산하므로:

- 안티앨리어싱으로 인한 1-2픽셀 차이를 모두 빨간색으로 표시
- JPEG 압축 아티팩트가 차이로 감지됨
- 텍스트 외곽선의 미세한 렌더링 차이가 과도하게 강조됨

### 해결책

1. **Threshold 조절**: 미세한 차이 무시
2. **Morphological Opening**: 작은 노이즈 제거
   - Erosion: 미세한 외곽선 제거
   - Dilation: 주요 영역 복원
3. **Gaussian Blur (선택)**: 외곽선 부드럽게 처리

### 효과

- ✅ 안티앨리어싱 차이 무시
- ✅ JPEG 압축 노이즈 제거
- ✅ 의미 있는 변경만 강조
- ✅ 더 깔끔한 비교 결과

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
- **opencv-python (외곽선 보정)** 🆕
- google-api-python-client (구글 API)
- google-auth-httplib2
- google-auth-oauthlib

### 3. Google Cloud Console 설정

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성
3. Google Sheets API 및 Google Drive API 활성화
4. OAuth 2.0 인증 정보 생성 및 `credentials.json` 저장

### 4. 구글 시트 준비

구글 시트는 다음과 같은 구조여야 합니다:

| A      | B              | C              | D          | E           | F          | G          | H             |
| ------ | -------------- | -------------- | ---------- | ----------- | ---------- | ---------- | ------------- |
| 행번호 | 이미지1 URL    | 이미지2 URL    | (자동생성) | (자동생성)  | (자동생성) | (자동생성) | (자동생성)    |
| 1      | 헤더           | 헤더           | 차이 강조  | 나란히 비교 | 판정       | 차이율 (%) | 변경 픽셀 (%) |
| 2      |                |                |            |             |            |            |               |
| 3      | =IMAGE("url1") | =IMAGE("url2") |            |             |            |            |               |

---

## ❗ 문제 해결

### 1. OpenCV 설치 오류

```bash
# OpenCV 재설치
source venv/bin/activate
pip install --upgrade opencv-python
```

### 2. 외곽선 보정이 너무 약하거나 강한 경우

```bash
# 보정이 약하다면 (빨간색이 여전히 많음)
--threshold 40 --morphology-kernel-size 5

# 보정이 강하다면 (변경사항을 놓침)
--threshold 20 --morphology-kernel-size 1
```

### 3. 메모리 부족 (대용량 이미지)

```bash
# 이미지가 너무 큰 경우 리사이즈 권장
# 코드에서 자동으로 리사이즈하지만, 원본 URL이 너무 큰 경우 문제 발생 가능
```

---

## 📞 도움말

문제가 계속되면 다음을 확인하세요:

1. Python 버전: `python --version` (3.7 이상 필요)
2. 가상환경 활성화 확인: `which python`
3. OpenCV 설치 확인: `pip show opencv-python`
4. 패키지 설치 확인: `pip list | grep opencv`

---

## 🎯 빠른 시작 체크리스트

- [ ] Python 3.7 이상 설치
- [ ] 가상환경 생성 및 활성화
- [ ] `pip install -r requirements.txt` 실행 (opencv-python 포함)
- [ ] Google Cloud Console에서 프로젝트 생성
- [ ] Google Sheets API 활성화
- [ ] Google Drive API 활성화
- [ ] OAuth 2.0 인증 정보 생성
- [ ] `credentials.json` 파일 저장
- [ ] 구글 시트에 B, C 열에 이미지 URL 준비 (3행부터)
- [ ] 🆕 외곽선 보정 파라미터 결정 (이미지 유형별 권장 설정 참고)
- [ ] `imgdiff_googlesheet_url.py` 실행 (외곽선 보정 적용)
- [ ] `upload_to_drive.py` 실행
- [ ] 구글 시트에서 결과 확인

---

**작성일**: 2025-11-12
**버전**: 2.0 (외곽선 보정 기능 추가)
**변경사항**:

- 외곽선 보정 기능 추가 (threshold, morphology, blur)
- 이미지 유형별 권장 설정 추가
- OpenCV 의존성 추가

---

요청시 처리할 기본 값

- threshold: 40
- morphology_kernel_size: 4
- blur_kernel_size: 0
