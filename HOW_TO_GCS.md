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

| 항목           | Google Drive  | Google Cloud Storage |
| -------------- | ------------- | -------------------- |
| 업로드 속도    | 느림 (순차적) | 빠름 (병렬)          |
| 1000개 행 처리 | ~30-40분      | ~10-15분             |
| 병렬 워커 수   | 5개 (기본)    | 10개 (기본)          |
| API 제한       | 엄격함        | 관대함               |
| 권한 설정      | 파일마다 설정 | 버킷 단위 설정       |
| 속도 개선      | -             | 약 4-5배 빠름        |

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

## ⚠️ 헤더 행 관리 및 주의사항 (2025-11-20 추가)

### 헤더 행의 중요성

**Google Sheets에서 헤더가 누락되는 문제 원인: `upload_to_gcs.py`의 조건부 헤더 추가**

`upload_to_gcs.py`는 헤더(D2:H2 행)를 다음과 같은 조건에서만 자동으로 추가합니다:

- `--start 3` 옵션이 사용된 경우에만 헤더 행 추가
- 다른 start 값(예: 10, 50 등)으로 실행하면 헤더가 누락됨

### 헤더 행 구성

```
A     B              C              D          E           F          G          H
─────────────────────────────────────────────────────────────────────────────────────
행번호 이미지1 URL    이미지2 URL    (자동생성) (자동생성)  (자동생성) (자동생성) (자동생성)
1      제목           제목           차이 강조  나란히 비교 판정       차이율(%) 변경픽셀(%)
2      헤더           헤더           헤더       헤더        헤더       헤더       헤더
3      =IMAGE(...)    =IMAGE(...)    (이미지)   (이미지)    판정값     수치       수치
```

### 헤더가 누락되지 않게 하는 방법

#### 방법 1: `--start 3`으로 항상 시작 (권장)

헤더 행을 자동으로 추가하려면 항상 `--start 3`으로 실행해야 합니다:

```bash
# ✅ 올바른 방법 (헤더 자동 추가)
python upload_to_gcs.py "SHEET_ID" \
  --start 3 --end 134 \
  --workers 10 \
  --bucket imgdiff-results

# ❌ 헤더가 추가되지 않음
python upload_to_gcs.py "SHEET_ID" \
  --start 10 --end 134 \  # ← start가 3이 아님
  --workers 10 \
  --bucket imgdiff-results
```

#### 방법 2: 수동으로 헤더 추가

만약 다른 행 번호로 시작해야 한다면, 수동으로 헤더를 먼저 추가하세요:

```bash
# 1단계: Google Sheets에서 D2:H2 행에 수동으로 헤더 입력
#        D2: "차이 강조"
#        E2: "나란히 비교"
#        F2: "판정"
#        G2: "차이율 (%)"
#        H2: "변경 픽셀 (%)"

# 2단계: 원하는 행 범위로 업로드 실행
python upload_to_gcs.py "SHEET_ID" \
  --start 10 --end 134 \
  --workers 10 \
  --bucket imgdiff-results
```

#### 방법 3: 분할 처리 (권장)

여러 배치로 나누어 처리할 경우, 첫 번째 배치는 `--start 3`으로 실행:

```bash
# 배치 1: 3~100행 (헤더 자동 추가)
python upload_to_gcs.py "SHEET_ID" \
  --start 3 --end 100 \
  --workers 10 \
  --bucket imgdiff-results

# 배치 2: 101~200행 (헤더는 이미 있으므로 start를 3이 아닌 다른 값으로도 가능)
# 단, 안전하려면 이 경우에도 수동으로 헤더가 있는지 확인 권장
python upload_to_gcs.py "SHEET_ID" \
  --start 101 --end 200 \
  --workers 10 \
  --bucket imgdiff-results
```

### 헤더 행 누락 확인 및 복구

#### 헤더 누락 확인

Google Sheets에서 다음을 확인하세요:

```
D2 셀 내용 확인
- ✅ "차이 강조" → 헤더가 정상
- ❌ 비어있음 또는 다른 값 → 헤더 누락
```

#### 헤더 누락 시 복구 방법

1. **Google Sheets에서 직접 추가**:

   - D2 셀 클릭
   - 다음 내용 입력:
     ```
     D2: 차이 강조
     E2: 나란히 비교
     F2: 판정
     G2: 차이율 (%)
     H2: 변경 픽셀 (%)
     ```

2. **Google Apps Script 사용**:
   - Google Sheets에서 확장프로그램 → Apps Script 열기
   - 다음 코드 실행:
     ```javascript
     function addHeaders() {
       var sheet = SpreadsheetApp.getActiveSheet();
       var headerRow = sheet.getRange("D2:H2");
       headerRow.setValues([
         ["차이 강조", "나란히 비교", "판정", "차이율 (%)", "변경 픽셀 (%)"],
       ]);
     }
     addHeaders();
     ```

### 업로드 전 체크리스트

- [ ] **D2:H2 헤더가 존재하는가?**

  - 없다면 `--start 3`으로 실행하거나 수동으로 추가

- [ ] **데이터가 3행부터 시작하는가?**

  - 헤더(2행), 데이터(3행부터)의 순서 확인

- [ ] **데이터 손실 우려가 없는가?**

  - 업로드 범위가 기존 데이터와 겹치지 않는지 확인

- [ ] **--start 값이 올바른가?**
  - `--start 3`으로 실행하거나 헤더 존재 확인

### 헤더 자동 추가 로직 상세

`upload_to_gcs.py`의 현재 헤더 추가 로직:

```python
# 헤더 추가 (D2:H2) - --start 3일 때만 실행됨
if start_row == 3:
    header_body = {
        'values': [['차이 강조', '나란히 비교', '판정', '차이율 (%)', '변경 픽셀 (%)']]
    }
    self.sheet_service.spreadsheets().values().update(
        spreadsheetId=self.spreadsheet_id,
        range='D2:H2',
        valueInputOption='USER_ENTERED',
        body=header_body
    ).execute()
    print("✅ 헤더 추가 완료")
```

**즉**: `--start 3`일 때만 자동으로 D2:H2에 헤더를 추가합니다.

---

## 🔗 파일명 매핑 및 주의사항 (2025-11-20 추가)

### 파일명 일관성의 중요성

**이미지가 Google Sheets에 표시되지 않는 가장 흔한 원인: 파일명 불일치**

로컬에서 생성되는 파일명과 GCS에 업로드되는 파일명이 정확히 일치해야만 IMAGE 함수가 올바르게 작동합니다. 파일명 실수가 있으면 GCS URL은 유효하지만 이미지가 로드되지 않는 현상이 발생합니다.

### 파일명 생성 규칙

#### 1. 로컬에서 생성되는 파일명

각 행(row)마다 `googlesheet_url_results/row_{ROW_NUM}/` 폴더에 다음 파일들이 생성됩니다:

```
googlesheet_url_results/
├── row_3/
│   ├── diff_highlight.png          ← 차이 강조 이미지 (정확한 이름)
│   ├── side_by_side.png            ← 나란히 비교 이미지 (정확한 이름)
│   └── stats.json                  ← 통계 정보
├── row_4/
│   ├── diff_highlight.png
│   ├── side_by_side.png
│   └── stats.json
└── ...
```

**⚠️ 중요**: 파일명은 항상 **정확히** `diff_highlight.png`와 `side_by_side.png`입니다.

#### 2. GCS에 업로드될 때의 파일명

`upload_to_gcs.py` 스크립트가 파일을 업로드할 때, 로컬 파일명 앞에 행 번호를 붙여서 업로드됩니다:

```
gs://imgdiff-results/imgdiff/
├── row3_diff_highlight.png         ← row_3/ 폴더의 diff_highlight.png가 업로드됨
├── row3_side_by_side.png           ← row_3/ 폴더의 side_by_side.png가 업로드됨
├── row3_stats.json
├── row4_diff_highlight.png
├── row4_side_by_side.png
├── row4_stats.json
└── ...
```

**⚠️ 주의**:

- GCS 경로의 파일명에는 **row 앞에 숫자만** 붙습니다 (예: `row3_`, `row4_`)
- 로컬 파일명 자체는 변경되지 않습니다

### 파일명 매핑 표

| 로컬 위치                          | 로컬 파일명          | GCS 경로                        | GCS 파일명                  |
| ---------------------------------- | -------------------- | ------------------------------- | --------------------------- |
| `googlesheet_url_results/row_3/`   | `diff_highlight.png` | `gs://imgdiff-results/imgdiff/` | `row3_diff_highlight.png`   |
| `googlesheet_url_results/row_3/`   | `side_by_side.png`   | `gs://imgdiff-results/imgdiff/` | `row3_side_by_side.png`     |
| `googlesheet_url_results/row_3/`   | `stats.json`         | `gs://imgdiff-results/imgdiff/` | `row3_stats.json`           |
| `googlesheet_url_results/row_130/` | `diff_highlight.png` | `gs://imgdiff-results/imgdiff/` | `row130_diff_highlight.png` |
| `googlesheet_url_results/row_130/` | `side_by_side.png`   | `gs://imgdiff-results/imgdiff/` | `row130_side_by_side.png`   |

### IMAGE 함수 구성

Google Sheets에서 IMAGE 함수를 사용할 때는 **GCS의 최종 파일명**을 사용해야 합니다:

```javascript
// 차이 강조 이미지 (D열)
=IMAGE("https://storage.googleapis.com/imgdiff-results/imgdiff/row3_diff_highlight.png")

// 나란히 비교 이미지 (E열)
=IMAGE("https://storage.googleapis.com/imgdiff-results/imgdiff/row3_side_by_side.png")
```

#### 올바른 IMAGE 함수 패턴

```javascript
=IMAGE("https://storage.googleapis.com/{BUCKET_NAME}/imgdiff/row{ROW_NUM}_{FILENAME}")
```

예시:

- 버킷명: `imgdiff-results`
- 행번호: `3`, `4`, `130` 등
- 파일명: `diff_highlight.png`, `side_by_side.png`

```javascript
// ✅ 올바른 예
=IMAGE("https://storage.googleapis.com/imgdiff-results/imgdiff/row3_diff_highlight.png")
=IMAGE("https://storage.googleapis.com/imgdiff-results/imgdiff/row130_side_by_side.png")

// ❌ 잘못된 예 (파일명 불일치)
=IMAGE("https://storage.googleapis.com/imgdiff-results/imgdiff/row3_diff.png")       // ← 틀림
=IMAGE("https://storage.googleapis.com/imgdiff-results/imgdiff/row3_comparison.png")  // ← 틀림
```

### 파일명 불일치 체크리스트

이 문제를 예방하기 위해 실행 전/후 다음을 확인하세요:

#### 실행 전

- [ ] 로컬 파일이 정확히 `diff_highlight.png`, `side_by_side.png`로 생성되는지 코드 확인
- [ ] `upload_to_gcs.py`에서 파일을 업로드할 때 행 번호를 올바르게 붙이는지 확인

  ```python
  # 올바른 패턴
  dest_name = f'imgdiff/row{row_num}_{file_path.name}'  # ✅

  # 잘못된 패턴
  dest_name = f'imgdiff/{file_path.name}'  # ❌ 행번호 누락
  ```

#### 실행 후

- [ ] 로컬 `googlesheet_url_results/row_N/` 폴더에서 파일명이 올바른지 확인

  ```bash
  ls googlesheet_url_results/row_3/
  # diff_highlight.png  side_by_side.png  stats.json  (이렇게 나와야 함)
  ```

- [ ] GCS 버킷에 업로드된 파일명 확인

  ```bash
  gsutil ls gs://imgdiff-results/imgdiff/ | head -20
  # gs://imgdiff-results/imgdiff/row3_diff_highlight.png
  # gs://imgdiff-results/imgdiff/row3_side_by_side.png
  # (row 뒤에 숫자 바로 붙음)
  ```

- [ ] Google Sheets에서 IMAGE 함수가 GCS 파일명과 정확히 일치하는지 확인

  - D3 셀 수식: `=IMAGE("https://storage.googleapis.com/imgdiff-results/imgdiff/row3_diff_highlight.png")`
  - E3 셀 수식: `=IMAGE("https://storage.googleapis.com/imgdiff-results/imgdiff/row3_side_by_side.png")`

- [ ] 이미지가 올바르게 표시되는지 확인
  - GCS URL을 브라우저에서 직접 방문하면 이미지가 로드되어야 함
  - Google Sheets에서도 이미지가 표시되어야 함

### 파일명 불일치 문제 해결

만약 이미지가 Google Sheets에 표시되지 않는다면:

#### 1단계: GCS URL 직접 확인

```bash
# 브라우저나 curl로 URL 접근 테스트
curl -I "https://storage.googleapis.com/imgdiff-results/imgdiff/row3_diff_highlight.png"

# 200 OK 응답이 나오면 파일은 존재
# 404 오류가 나오면 파일명이 정확하지 않음
```

#### 2단계: GCS의 실제 파일명 확인

```bash
# 활성화된 가상환경에서
gsutil ls -r gs://imgdiff-results/imgdiff/ | grep row3

# 출력 예:
# gs://imgdiff-results/imgdiff/row3_diff_highlight.png
# gs://imgdiff-results/imgdiff/row3_side_by_side.png
```

#### 3단계: Google Sheets 수식 확인

- 각 셀의 수식을 수정 모드에서 확인
- GCS 경로가 실제 파일명과 정확히 일치하는지 비교
- 특히 로우 번호(3, 4, 130 등)가 올바른지 확인

#### 4단계: 파일 재업로드

```bash
# 만약 파일명이 잘못되었다면 다시 업로드
source venv/bin/activate
python upload_to_gcs.py "SHEET_ID" \
  --start 3 --end 10 \
  --workers 5 \
  --bucket imgdiff-results
```

### 완벽한 파일명 매핑 예시

**시나리오**: 행 3, 130, 150을 처리하는 경우

```
로컬 생성:
  googlesheet_url_results/row_3/diff_highlight.png
  googlesheet_url_results/row_3/side_by_side.png
  googlesheet_url_results/row_130/diff_highlight.png
  googlesheet_url_results/row_130/side_by_side.png
  googlesheet_url_results/row_150/diff_highlight.png
  googlesheet_url_results/row_150/side_by_side.png

GCS 업로드됨:
  gs://imgdiff-results/imgdiff/row3_diff_highlight.png
  gs://imgdiff-results/imgdiff/row3_side_by_side.png
  gs://imgdiff-results/imgdiff/row130_diff_highlight.png
  gs://imgdiff-results/imgdiff/row130_side_by_side.png
  gs://imgdiff-results/imgdiff/row150_diff_highlight.png
  gs://imgdiff-results/imgdiff/row150_side_by_side.png

Google Sheets 수식:
  D3:  =IMAGE("https://storage.googleapis.com/imgdiff-results/imgdiff/row3_diff_highlight.png")
  E3:  =IMAGE("https://storage.googleapis.com/imgdiff-results/imgdiff/row3_side_by_side.png")
  D130: =IMAGE("https://storage.googleapis.com/imgdiff-results/imgdiff/row130_diff_highlight.png")
  E130: =IMAGE("https://storage.googleapis.com/imgdiff-results/imgdiff/row130_side_by_side.png")
  D150: =IMAGE("https://storage.googleapis.com/imgdiff-results/imgdiff/row150_diff_highlight.png")
  E150: =IMAGE("https://storage.googleapis.com/imgdiff-results/imgdiff/row150_side_by_side.png")
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
| 1      | 제목           | 제목           | 차이 강조  | 나란히 비교 | 판정       | 차이율 (%) | 변경 픽셀 (%) |
| 2      | 헤더           | 헤더           | 헤더       | 헤더        | 헤더       | 헤더       | 헤더          |
| 3      | =IMAGE("url1") | =IMAGE("url2") |            |             |            |            |               |

**중요**:

- **D2~H2는 헤더 행입니다** - 업로드 시 이 영역을 건너뜁니다
- 데이터는 **3행부터 시작**합니다
- A열은 행 번호, B~C열은 이미지 URL 필수

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

| 열  | 행    | 내용               | 설명                                                          |
| --- | ----- | ------------------ | ------------------------------------------------------------- |
| D   | 2행   | 헤더: 차이 강조    | (헤더, 보호됨)                                                |
| D   | 3~N행 | 차이 강조 이미지   | 차이가 있는 부분을 빨간색으로 강조 (외곽선 보정 적용)         |
| E   | 2행   | 헤더: 나란히 비교  | (헤더, 보호됨)                                                |
| E   | 3~N행 | 나란히 비교 이미지 | 두 이미지를 나란히 배치 (4개 패널 비교)                       |
| F   | 2행   | 헤더: 판정         | (헤더, 보호됨)                                                |
| F   | 3~N행 | 판정               | ✅ 거의 동일 / ⚠️ 약간 다름/ ❌ 상당히 다름 (stats.json 기반) |
| G   | 2행   | 헤더: 차이율(%)    | (헤더, 보호됨)                                                |
| G   | 3~N행 | 차이율 (%)         | 전체 픽셀 대비 차이 정도 (original 기준, 0~100%)              |
| H   | 2행   | 헤더: 변경픽셀(%)  | (헤더, 보호됨)                                                |
| H   | 3~N행 | 변경 픽셀 (%)      | 변경된 픽셀의 비율 (original 기준, 0~100%)                    |

**주의사항**:

- **D2~H2 헤더 행은 업로드 시 자동으로 건너뜁니다**
- 데이터는 항상 3행부터 시작하여 업데이트됩니다
- 헤더 행이 덮어쓰기되지 않도록 보호됩니다

---

## ⚠️ 주요 이슈 및 해결 방법 (2025-11-19 업데이트)

### 알려진 이슈

#### 1. Processed Statistics가 0으로 표시되는 현상

**문제**:

- 구글 시트의 G열(차이율), H열(변경 픽셀 %)이 0으로 표시됨
- 실제로는 이미지에 명확한 차이가 있음

**원인**:

- 기본 설정 (`--threshold 40 --morphology-kernel-size 4`)의 형태학적 연산이 너무 공격적
- `stats.json`의 `processed` 통계에서 약 43% 행(132개 중 57개)이 diff_percentage = 0.0으로 계산됨
- 반면 `original` 통계는 항상 실제 값을 보유

**해결 방법**:

```python
# ❌ 기존 방식 (processed 사용)
original = stats['original']
processed = stats['processed']
# → G열에 processed['diff_percentage'] 사용 시 많은 행이 0 표시

# ✅ 올바른 방식 (original 사용)
original = stats['original']
# → G열에 original['diff_percentage'] 사용
# → H열에 original['changed_percentage'] 사용
```

**stats.json 구조 이해**:

```json
{
  "original": {
    "diff_percentage": 0.5, // 실제 픽셀 차이율 (필터링 없음)
    "changed_pixels": 3000, // 변경된 픽셀 개수
    "changed_percentage": 0.2, // 변경된 픽셀 비율
    "mean_diff": { "r": 1.2, "g": 1.1, "b": 1.0 }, // 평균 차이
    "max_diff": { "r": 100, "g": 95, "b": 98 } // 최대 차이
  },
  "processed": {
    "diff_percentage": 0.0, // 필터링 후 차이율 (형태학 연산 적용)
    "changed_percentage": 0.0, // 필터링 후 변경 픽셀 비율
    "processing_applied": {
      "threshold": 40,
      "morphology_kernel": 4,
      "blur_kernel": 0
    }
  }
}
```

**어느 것을 사용할지 판단 기준**:

- **Display/Report용**: `original` 사용 (실제 데이터를 사용자에게 보여줌)
- **Visual diff용**: `processed` 사용 (diff_highlight.png에 반영됨)

#### 2. 판정(Judgment) 열이 모두 같은 값으로 표시

**문제**:

- F열(판정)이 모든 행에서 "✅ 거의 동일"로 고정됨
- 실제로는 다양한 수준의 차이가 있음

**원인**:

- 판정 값이 stats.json의 실제 데이터를 기반으로 하지 않고 하드코딩됨
- 각 행의 이미지 비교 결과와 무관하게 동일 값 적용

**해결 방법**:
동적 판정 로직을 적용하여 각 행의 통계를 기반으로 판정 생성:

```python
def get_judgment(original_stats):
    """
    stats.json의 original 통계를 기반으로 판정 생성
    """
    diff_percentage = original_stats['diff_percentage']
    mean_diff_r = original_stats['mean_diff']['r']
    mean_diff_g = original_stats['mean_diff']['g']
    mean_diff_b = original_stats['mean_diff']['b']
    max_diff_r = original_stats['max_diff']['r']
    max_diff_g = original_stats['max_diff']['g']
    max_diff_b = original_stats['max_diff']['b']

    mean_diff = (mean_diff_r + mean_diff_g + mean_diff_b) / 3
    max_diff = max(max_diff_r, max_diff_g, max_diff_b)

    # Tier 1: 거의 동일
    if diff_percentage < 0.5 and mean_diff < 2:
        return "✅ 거의 동일"
    elif diff_percentage < 1.5 and mean_diff < 5:
        return "✅ 거의 동일"

    # Tier 3: 상당히 다름 (max_diff 기준)
    elif max_diff > 200:
        return "❌ 상당히 다름"

    # Tier 2: 약간 다름 (기본값)
    else:
        return "⚠️ 약간 다름"
```

**판정 기준**:

| 판정           | 조건                                                         |
| -------------- | ------------------------------------------------------------ |
| ✅ 거의 동일   | diff < 0.5% (mean_diff < 2) 또는 diff < 1.5% (mean_diff < 5) |
| ⚠️ 약간 다름   | 나머지 (기본값, max_diff ≤ 200)                              |
| ❌ 상당히 다름 | max_diff > 200 (주요 색상 변화)                              |

**구글 시트 업데이트 방법**:

```python
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import json
from pathlib import Path

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
spreadsheet_id = 'YOUR_SHEET_ID'
sheet_name = '시트명'

# 인증
creds = None
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

service = build('sheets', 'v4', credentials=creds)

# 판정 값 수집
updates = []
all_rows = [3, 4, 5, ...]  # 처리한 행 번호들

for row_num in all_rows:
    stats_file = Path(f'googlesheet_url_results/row_{row_num}/stats.json')
    with open(stats_file) as f:
        stats = json.load(f)

    original = stats['original']
    judgment = get_judgment(original)

    updates.append({
        'range': f"'{sheet_name}'!F{row_num}",
        'values': [[judgment]]
    })

# 배치 업데이트 (100개씩)
for i in range(0, len(updates), 100):
    batch = updates[i:i+100]
    data = [{'range': u['range'], 'values': u['values']} for u in batch]
    body = {'data': data, 'valueInputOption': 'RAW'}
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()
```

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

| 항목     | Google Drive     | Google Cloud Storage    |
| -------- | ---------------- | ----------------------- |
| 저장소   | 15GB 무료        | 5GB 무료 (항상)         |
| 초과 시  | $1.99/월 (100GB) | $0.02/GB/월             |
| 속도     | 느림             | 빠름                    |
| API 제한 | 엄격             | 관대                    |
| 권장용도 | 개인 파일        | 대용량 데이터, 웹호스팅 |

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

| 방식                    | 시간  | 병렬 워커 | 비고                      |
| ----------------------- | ----- | --------- | ------------------------- |
| Google Drive (순차)     | ~45분 | 1         | 기존 방식                 |
| Google Drive (병렬 5개) | ~30분 | 5         | 개선 버전                 |
| **GCS (병렬 10개)**     | ~12분 | 10        | **권장 (4배 빠름)** ✅    |
| GCS (병렬 20개)         | ~8분  | 20        | 네트워크 환경에 따라 다름 |

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

---

## 📌 Best Practices & 권장사항

### 1. Stats 데이터 사용 가이드

**원본 vs 처리된 통계 선택**:

- **Google Sheets에 표시할 수 있는 값 (차이율, 변경픽셀 등)**:

  - ✅ `stats['original']` 사용 (사용자에게 보여줄 실제 수치)
  - ❌ `stats['processed']` 사용하면 안 됨 (형태학 연산으로 인한 필터링)

- **Visual Diff 이미지 (diff_highlight.png) 생성에 사용**:
  - ✅ `stats['processed']` 데이터 기반 (노이즈 제거됨)
  - 결과적으로 diff_highlight.png에는 중요한 변화만 강조됨

```python
# 예시: 올바른 사용법
stats = json.load(open('googlesheet_url_results/row_3/stats.json'))

# 시트에 표시할 값
sheet_diff_percentage = stats['original']['diff_percentage']  # ✅ 실제 값
sheet_changed_percentage = stats['original']['changed_percentage']  # ✅ 실제 값

# Judgment 생성용
judgment = get_judgment(stats['original'])  # ✅ original 기반
```

### 2. 형태학적 연산(Morphology) 파라미터 최적화

**현재 기본값 (threshold=40, morphology-kernel-size=4)의 특성**:

- 텍스트/문서 비교에 최적화
- 안티앨리어싱으로 인한 미세한 차이 무시
- 약 43% 행에서 processed diff_percentage = 0.0 (정상)

**조정이 필요한 경우**:

| 상황                          | 권장 설정                              |
| ----------------------------- | -------------------------------------- |
| 변경사항이 모두 포착되어야 함 | threshold=20, morphology-kernel-size=2 |
| 미세한 차이는 무시해도 됨     | threshold=50, morphology-kernel-size=6 |
| 사진/컬러 이미지              | threshold=50, morphology-kernel-size=4 |
| 엄격한 픽셀 비교              | threshold=15, morphology-kernel-size=0 |

### 3. 대량 시트 업데이트 패턴

Google Sheets API 배치 업데이트 시 주의사항:

```python
# ✅ 올바른 패턴: 100개씩 배치 처리 (헤더 행 2행 건너뛰기)
updates = [...]  # 모든 업데이트 항목 수집

for i in range(0, len(updates), 100):
    batch = updates[i:i+100]
    data = [{'range': u['range'], 'values': u['values']} for u in batch]
    body = {'data': data, 'valueInputOption': 'RAW'}  # RAW 사용
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()
```

**주의점**:

- `valueInputOption='RAW'`: 수식이 아닌 일반 값으로 입력
- **D2~H2 헤더 행은 자동으로 건너뜁니다** (업데이트 시 보호)
- 데이터는 항상 3행부터 시작하여 업데이트
- 100개 배치: API 제한 회피
- 한 번에 수백 개 행 업데이트 가능

**헤더 행 보호 구현**:

```python
# 잘못된 예: 헤더를 덮어쓰는 경우
for row_num in range(2, 1002):  # ❌ 2행부터 시작 (헤더 덮어씀)
    updates.append({
        'range': f"'{sheet_name}'!F{row_num}",
        'values': [[judgment]]
    })

# 올바른 예: 헤더를 건너뛰는 경우
for row_num in range(3, 1002):  # ✅ 3행부터 시작 (헤더 보호)
    updates.append({
        'range': f"'{sheet_name}'!F{row_num}",
        'values': [[judgment]]
    })
```

### 4. Stats.json 파일 검증

각 실행 후 샘플 stats.json 확인:

```bash
# 첫 번째 행의 통계 확인
cat googlesheet_url_results/row_3/stats.json | python -m json.tool

# original과 processed 비교
python3 << 'EOF'
import json

with open('googlesheet_url_results/row_3/stats.json') as f:
    stats = json.load(f)

print(f"Original diff: {stats['original']['diff_percentage']:.2f}%")
print(f"Processed diff: {stats['processed']['diff_percentage']:.2f}%")
print(f"차이: {abs(stats['original']['diff_percentage'] - stats['processed']['diff_percentage']):.2f}%")
EOF
```

---

## 📊 숫자 정밀도 및 소숫점 포맷

### 현재 동작 방식

Google Sheets에 업로드되는 **차이율(diff_percentage)** 과 **변경된 픽셀 비율(changed_percentage)** 은 다음과 같이 처리됩니다:

#### 1. **코드 동작 (upload_to_gcs.py)**

```python
# 라인 175-176: 통계 값 추출 (포맷 없음, 모든 소수점 유지)
diff_pct = stats.get('diff_percentage', 0)
changed_pct = stats.get('changed_percentage', 0)

# 라인 199-200: Google Sheets에 전송 (전체 소수점 그대로)
row_data = [
    ...
    diff_pct,                     # G열: 차이율 (%) - 모든 소수점 노출
    changed_pct,                  # H열: 변경된 픽셀 비율 (%) - 모든 소수점 노출
]

# 라인 202: 콘솔 출력만 2자리 포맷 (Google Sheets 업로드는 영향 없음)
print(f"  ✅ 업로드 완료 (차이율: {diff_pct:.2f}%)")
```

#### 2. **전체 소수점 노출**

- **imgdiff 도구**: stats.json의 원본 값을 그대로 전송 (모든 소수점 포함)
- **Google Sheets**: 수신한 전체 소수점을 모두 저장 및 표시
- **실제 값**: stats.json의 완전한 정밀도 유지 (예: 2.3022673801959486)
- **표시**: Google Sheets가 전체 소수점을 노출 (예: 2.3022673801959486)

#### 3. **예시**

| stats.json 값       | Google Sheets 저장/표시 | 설명               |
| ------------------- | ----------------------- | ------------------ |
| 2.3022673801959486  | 2.3022673801959486      | 모든 소수점 노출   |
| 0.07753619025735294 | 0.07753619025735294     | 완전한 정밀도 보존 |
| 1.28289794921875    | 1.28289794921875        | 추가 포맷 없음     |

### 권장사항

- **기본 정책**: 모든 소수점을 제한 없이 노출 (현재 상태)
- **데이터 정확성**: 완전한 소수점 값 유지로 정밀한 비교 가능
- **저장 형식**: stats.json의 완전한 값을 그대로 Google Sheets에 저장
- **표시**: Google Sheets가 전체 소수점을 모두 표시

---

**작성일**: 2025-11-20
**버전**: 3.4 (숫자 정밀도 및 소숫점 포맷 가이드 추가)
**변경사항**:

### 3.3 → 3.4 업데이트 (2025-11-20)

- 📊 **숫자 정밀도 및 소숫점 포맷** 섹션 추가
  - Google Sheets 업로드 시 전체 소수점 노출 정책 문서화
  - stats.json의 원본 값을 그대로 전송하는 방식 설명
  - 표시 포맷 조정이 필요한 경우의 대체 방법 제시
- ✅ **기본 정책**: 모든 소수점을 노출하여 완전한 정밀도 유지
- 📋 **포맷 조정**: Google Sheets 포맷 설정이나 수식으로 표시 방식만 변경 가능

### 3.2 → 3.3 업데이트 (2025-11-20)

- ⚠️ **헤더 행 관리 및 주의사항** 섹션 추가
  - `upload_to_gcs.py`의 조건부 헤더 추가 로직 상세 설명
  - 헤더 행이 누락되는 이유: `--start 3`일 때만 자동 추가
  - 3가지 헤더 추가 방법: `--start 3`로 실행, 수동 추가, 분할 처리
  - 헤더 누락 확인 및 복구 방법 (Google Sheets 직접 추가, Apps Script)
  - 업로드 전 체크리스트 (헤더 확인, 행 번호, --start 값)
  - 헤더 자동 추가 로직의 정확한 코드 설명
- ✅ **문제 예방**: 헤더가 누락되지 않도록 명확한 가이드 제공
- 📋 **복구 방법**: 헤더 누락 시 빠르게 복구할 수 있는 절차 제시

### 3.1 → 3.2 업데이트

- 🔗 **파일명 매핑 및 주의사항** 섹션 추가
  - 로컬 파일명과 GCS 경로의 정확한 매핑 관계 문서화
  - IMAGE 함수 구성 패턴 및 올바른 예제 제공
  - 파일명 불일치 체크리스트 (실행 전/후)
  - 파일명 불일치 문제 해결 절차 (4단계)
  - 완벽한 파일명 매핑 예시 추가
- ✅ **문제 예방**: 이미지가 Google Sheets에 표시되지 않는 이슈 해결
- 📋 **검증 가이드**: GCS URL 직접 확인 방법 제공

### 3.0 → 3.1 업데이트

- ⚠️ **주요 이슈**: Processed Statistics 0 값 문제 원인 분석 및 해결
- ✅ **판정 열 동적 생성**: Stats.json 기반 자동 판정 로직
- 📖 **Best Practices** 섹션 추가
- 📌 **Stats 데이터 사용 가이드** 추가

### 이전 변경사항 (3.0)

- Google Drive → Google Cloud Storage 변경
- 병렬 업로드 최적화 (10개 워커 기본)
- 약 4-5배 빠른 처리 속도
- GCS 버킷 설정 및 권한 관리 추가
- 비용 안내 및 성능 비교 추가

---

## 요청시 처리할 기본 값

- threshold: 35
- morphology_kernel_size: 2
- blur_kernel_size: 0
- bucket: imgdiff-results-2025
  - 버킷 안에 폴더는 HOW*TO_GCS.md 에서 처럼 imgdiff*{timestamp} 구성됨.
- workers: 10
