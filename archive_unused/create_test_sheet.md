# 테스트용 구글 시트 만들기

## 1. 새 구글 시트 생성
1. [구글 시트](https://sheets.google.com) 접속
2. "빈 스프레드시트" 클릭

## 2. 테스트 데이터 입력
B3, C3부터 다음과 같이 입력:

| | A | B | C | D | E |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | image1.png | image2.png | | |
| 4 | | v1_001.png | v2_001.png | | |
| 5 | | small_image.png | large_image.png | | |

## 3. 시트 ID 복사
URL에서 ID 부분 복사:
```
https://docs.google.com/spreadsheets/d/{이_부분이_ID}/edit
```

## 4. 실행
```bash
./test_googlesheet.sh
# 또는
python imgdiff_googlesheet.py YOUR_SHEET_ID --update-sheet
```

## 주의사항
- 이미지 파일 경로는 현재 디렉토리 기준
- 또는 절대 경로 사용 (/Users/...)