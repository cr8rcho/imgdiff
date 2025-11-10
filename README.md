# 이미지 비교 도구 (Image Diff)

두 이미지 간의 차이를 분석하고 시각화하는 Python 도구입니다.

## 주요 기능

- **픽셀 단위 비교**: 두 이미지의 각 픽셀을 비교하여 차이를 계산
- **다양한 시각화 모드**:
  - `difference`: 픽셀 차이를 그대로 표시
  - `highlight`: 차이가 있는 영역을 빨간색으로 강조
  - `heatmap`: 차이 강도를 히트맵으로 표시
- **통계 정보 제공**: 차이율, 변경된 픽셀 수, 채널별 차이 등
- **변경 영역 탐지**: 차이가 있는 영역을 자동으로 찾아 바운딩 박스로 표시
- **크기 자동 조정**: 크기가 다른 이미지 자동 리사이즈
- **종합 리포트 생성**: 텍스트 리포트와 여러 시각화 이미지 생성

## 설치 방법

```bash
# 가상 환경 생성 (권장)
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate  # Windows

# 필요한 패키지 설치
pip install -r requirements.txt
```

## 사용 방법

### 기본 사용법

```bash
# 전체 리포트 모드 (기본값)
python imgdiff.py image1.png image2.png

# 빠른 비교 모드
python imgdiff.py image1.png image2.png --mode quick

# 출력 디렉토리 지정
python imgdiff.py image1.png image2.png --output-dir my_results
```

### Python 코드에서 사용

```python
from imgdiff import ImageComparator

# 이미지 비교 객체 생성
comparator = ImageComparator('image1.png', 'image2.png')

# 통계 정보 가져오기
stats = comparator.get_statistics()
print(f"차이율: {stats['diff_percentage']:.2f}%")

# 차이 이미지 생성
diff_img = comparator.create_diff_image('highlight')
diff_img.save('my_diff.png')

# 종합 리포트 생성
comparator.save_comparison_report('my_results')
```

## 테스트 이미지 생성

테스트용 이미지를 생성하려면:

```bash
python create_test_images.py
```

생성되는 이미지:
- `image1.png`, `image2.png`: 여러 차이가 있는 테스트 이미지
- `identical1.png`, `identical2.png`: 동일한 이미지
- `small_image.png`, `large_image.png`: 크기가 다른 이미지

## 출력 파일 설명

전체 리포트 모드에서 생성되는 파일들:

- `report.txt`: 텍스트 형식의 상세 리포트
- `difference.png`: 픽셀 차이를 그대로 표시
- `highlight.png`: 변경된 영역을 빨간색으로 강조
- `heatmap.png`: 차이 강도를 히트맵으로 시각화
- `regions.png`: 변경된 영역에 바운딩 박스 표시
- `side_by_side.png`: 원본 이미지들과 차이를 나란히 표시

## 예제

### 예제 1: 빠른 차이 확인

```python
from imgdiff import ImageComparator

comparator = ImageComparator('before.png', 'after.png')
stats = comparator.get_statistics()

if stats['diff_percentage'] > 10:
    print("이미지에 큰 차이가 있습니다!")
else:
    print("이미지가 거의 동일합니다.")
```

### 예제 2: 변경된 영역 찾기

```python
from imgdiff import ImageComparator

comparator = ImageComparator('original.png', 'modified.png')
regions = comparator.find_changed_regions(threshold=20, min_area=100)

for i, region in enumerate(regions, 1):
    print(f"영역 {i}: {region['width']}x{region['height']} at ({region['x']}, {region['y']})")
```

## 필요 패키지

- `Pillow`: 이미지 처리
- `numpy`: 수치 연산
- `matplotlib`: 시각화
- `scipy`: 이미지 분석

## CSV/구글 시트 연동

대량의 이미지를 자동으로 비교하는 기능이 추가되었습니다.

### CSV 파일 배치 처리

```bash
# CSV 파일로 여러 이미지 한번에 비교
python imgdiff_csv.py sample_images.csv

# 결과: HTML 리포트, CSV, JSON 파일 생성
```

### 구글 시트 연동 (B3:C부터 시작)

```bash
# 구글 시트에서 B3:C 범위 데이터 읽어오기
python imgdiff_googlesheet.py YOUR_SPREADSHEET_ID

# 결과를 구글 시트 D3부터 자동 업데이트
python imgdiff_googlesheet.py YOUR_SPREADSHEET_ID --update-sheet

# 커스텀 범위 지정
python imgdiff_googlesheet.py YOUR_SPREADSHEET_ID --range "E5:F" --result-column G --result-row 5
```

자세한 사용법은 [GOOGLE_SHEET_GUIDE.md](GOOGLE_SHEET_GUIDE.md) 참조

## 라이선스

MIT