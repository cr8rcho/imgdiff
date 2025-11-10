#!/usr/bin/env python3
"""
CSV 파일 기반 이미지 비교 도구
CSV 파일에 있는 이미지 경로를 읽어 자동으로 비교합니다.
"""

import csv
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import argparse
import json
from datetime import datetime
from imgdiff import ImageComparator


class CSVImageComparator:
    """CSV 파일에서 이미지 경로를 읽어 비교하는 클래스"""

    def __init__(self, csv_path: str, output_dir: str = "csv_comparison_results"):
        """
        초기화

        Args:
            csv_path: CSV 파일 경로
            output_dir: 결과를 저장할 디렉토리
        """
        self.csv_path = csv_path
        self.output_dir = output_dir
        self.results = []

    def read_csv(self) -> List[Dict[str, str]]:
        """
        CSV 파일을 읽어 이미지 경로 쌍을 반환합니다.

        Returns:
            이미지 경로 쌍의 리스트
        """
        image_pairs = []

        with open(self.csv_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)

            # 헤더가 있다면 스킵
            headers = next(reader, None)

            for row_num, row in enumerate(reader, start=2):  # 헤더 다음부터 시작
                if len(row) >= 2:
                    # 첫 번째와 두 번째 컬럼을 이미지 경로로 사용
                    image1_path = row[0].strip()
                    image2_path = row[1].strip()

                    # 추가 정보가 있다면 포함
                    metadata = {
                        'row_number': row_num,
                        'image1': image1_path,
                        'image2': image2_path,
                        'name': row[2].strip() if len(row) > 2 else f"Row_{row_num}",
                        'description': row[3].strip() if len(row) > 3 else ""
                    }

                    image_pairs.append(metadata)
                else:
                    print(f"⚠️  Row {row_num}: 불완전한 데이터 (컬럼 수 부족)")

        return image_pairs

    def compare_images_batch(self, image_pairs: List[Dict[str, str]]) -> List[Dict]:
        """
        여러 이미지 쌍을 배치로 비교합니다.

        Args:
            image_pairs: 이미지 경로 쌍의 리스트

        Returns:
            비교 결과 리스트
        """
        results = []
        total = len(image_pairs)

        for idx, pair in enumerate(image_pairs, 1):
            print(f"\n[{idx}/{total}] 비교 중: {pair['name']}")
            print(f"  이미지 1: {pair['image1']}")
            print(f"  이미지 2: {pair['image2']}")

            result = {
                'row_number': pair['row_number'],
                'name': pair['name'],
                'description': pair['description'],
                'image1': pair['image1'],
                'image2': pair['image2'],
                'status': 'pending'
            }

            try:
                # 이미지 파일 존재 확인
                if not os.path.exists(pair['image1']):
                    raise FileNotFoundError(f"이미지 1을 찾을 수 없음: {pair['image1']}")
                if not os.path.exists(pair['image2']):
                    raise FileNotFoundError(f"이미지 2를 찾을 수 없음: {pair['image2']}")

                # 이미지 비교
                comparator = ImageComparator(pair['image1'], pair['image2'])
                stats = comparator.get_statistics()

                # 결과 저장
                result.update({
                    'status': 'success',
                    'diff_percentage': stats['diff_percentage'],
                    'changed_pixels': stats['changed_pixels'],
                    'changed_percentage': stats['changed_percentage'],
                    'mean_diff_r': stats['mean_diff']['r'],
                    'mean_diff_g': stats['mean_diff']['g'],
                    'mean_diff_b': stats['mean_diff']['b'],
                    'image_size': comparator.img1.size
                })

                # 개별 결과 디렉토리 생성
                row_output_dir = os.path.join(self.output_dir, f"row_{pair['row_number']}_{pair['name'].replace(' ', '_')}")
                os.makedirs(row_output_dir, exist_ok=True)

                # 차이 이미지 저장
                diff_img = comparator.create_diff_image('highlight')
                diff_img.save(os.path.join(row_output_dir, 'diff_highlight.png'))

                # 간단한 텍스트 리포트 저장
                with open(os.path.join(row_output_dir, 'report.txt'), 'w', encoding='utf-8') as f:
                    f.write(f"비교 리포트\n")
                    f.write(f"="*50 + "\n")
                    f.write(f"이름: {pair['name']}\n")
                    f.write(f"설명: {pair['description']}\n")
                    f.write(f"이미지 1: {pair['image1']}\n")
                    f.write(f"이미지 2: {pair['image2']}\n")
                    f.write(f"차이율: {stats['diff_percentage']:.2f}%\n")
                    f.write(f"변경된 픽셀: {stats['changed_percentage']:.2f}%\n")

                print(f"  ✅ 성공: 차이율 {stats['diff_percentage']:.2f}%")

            except Exception as e:
                result.update({
                    'status': 'error',
                    'error_message': str(e)
                })
                print(f"  ❌ 오류: {e}")

            results.append(result)

        self.results = results
        return results

    def generate_summary_report(self):
        """종합 리포트를 생성합니다."""
        if not self.results:
            print("⚠️  비교 결과가 없습니다.")
            return

        # HTML 리포트 생성
        html_report = self._generate_html_report()
        html_path = os.path.join(self.output_dir, 'summary_report.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_report)

        # JSON 리포트 생성 (numpy 타입을 Python 타입으로 변환)
        json_path = os.path.join(self.output_dir, 'results.json')

        # numpy 타입을 Python 타입으로 변환
        def convert_numpy_types(obj):
            import numpy as np
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            else:
                return obj

        json_results = convert_numpy_types(self.results)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, ensure_ascii=False, indent=2)

        # CSV 리포트 생성
        csv_path = os.path.join(self.output_dir, 'results.csv')
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['row_number', 'name', 'description', 'image1', 'image2',
                         'status', 'diff_percentage', 'changed_percentage', 'error_message']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in self.results:
                writer.writerow({
                    'row_number': result.get('row_number'),
                    'name': result.get('name'),
                    'description': result.get('description'),
                    'image1': result.get('image1'),
                    'image2': result.get('image2'),
                    'status': result.get('status'),
                    'diff_percentage': result.get('diff_percentage', ''),
                    'changed_percentage': result.get('changed_percentage', ''),
                    'error_message': result.get('error_message', '')
                })

        # 콘솔 요약 출력
        print("\n" + "="*60)
        print("비교 완료 요약")
        print("="*60)

        success_count = sum(1 for r in self.results if r['status'] == 'success')
        error_count = sum(1 for r in self.results if r['status'] == 'error')

        print(f"전체: {len(self.results)}개")
        print(f"성공: {success_count}개")
        print(f"실패: {error_count}개")

        if success_count > 0:
            avg_diff = sum(r['diff_percentage'] for r in self.results if r['status'] == 'success') / success_count
            print(f"평균 차이율: {avg_diff:.2f}%")

        print(f"\n📁 결과 저장 위치: {self.output_dir}")
        print(f"  - HTML 리포트: summary_report.html")
        print(f"  - JSON 데이터: results.json")
        print(f"  - CSV 결과: results.csv")

    def _generate_html_report(self) -> str:
        """HTML 형식의 리포트를 생성합니다."""
        html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>이미지 비교 결과 리포트</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }
        .summary {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .summary-stats {
            display: flex;
            gap: 20px;
            margin-top: 10px;
        }
        .stat-box {
            flex: 1;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 8px;
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        th {
            background: #4CAF50;
            color: white;
            padding: 12px;
            text-align: left;
        }
        td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }
        tr:hover {
            background: #f5f5f5;
        }
        .status-success {
            color: green;
            font-weight: bold;
        }
        .status-error {
            color: red;
            font-weight: bold;
        }
        .diff-low {
            background: #c8e6c9;
        }
        .diff-medium {
            background: #fff9c4;
        }
        .diff-high {
            background: #ffccbc;
        }
        .timestamp {
            color: #666;
            font-size: 0.9em;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <h1>🖼️ 이미지 비교 결과 리포트</h1>

    <div class="summary">
        <h2>요약</h2>
        <div class="summary-stats">
            <div class="stat-box">
                <div class="stat-number">""" + str(len(self.results)) + """</div>
                <div>전체 비교</div>
            </div>
            <div class="stat-box" style="background: linear-gradient(135deg, #56ab2f 0%, #a8e063 100%);">
                <div class="stat-number">""" + str(sum(1 for r in self.results if r['status'] == 'success')) + """</div>
                <div>성공</div>
            </div>
            <div class="stat-box" style="background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);">
                <div class="stat-number">""" + str(sum(1 for r in self.results if r['status'] == 'error')) + """</div>
                <div>실패</div>
            </div>
        </div>
    </div>

    <h2>상세 결과</h2>
    <table>
        <thead>
            <tr>
                <th>Row</th>
                <th>이름</th>
                <th>설명</th>
                <th>상태</th>
                <th>차이율</th>
                <th>변경 픽셀</th>
                <th>결과 폴더</th>
            </tr>
        </thead>
        <tbody>
"""

        for result in self.results:
            status_class = 'status-success' if result['status'] == 'success' else 'status-error'

            if result['status'] == 'success':
                diff = result['diff_percentage']
                if diff < 5:
                    diff_class = 'diff-low'
                elif diff < 20:
                    diff_class = 'diff-medium'
                else:
                    diff_class = 'diff-high'
            else:
                diff_class = ''

            diff_percent = result.get('diff_percentage', 'N/A')
            changed_percent = result.get('changed_percentage', 'N/A')

            diff_str = f"{diff_percent:.2f}" if isinstance(diff_percent, (int, float)) else diff_percent
            changed_str = f"{changed_percent:.2f}" if isinstance(changed_percent, (int, float)) else changed_percent

            html += f"""
            <tr class="{diff_class}">
                <td>{result['row_number']}</td>
                <td>{result['name']}</td>
                <td>{result.get('description', '')}</td>
                <td class="{status_class}">{result['status'].upper()}</td>
                <td>{diff_str}%</td>
                <td>{changed_str}%</td>
                <td>row_{result['row_number']}_{result['name'].replace(' ', '_')}/</td>
            </tr>
"""

        html += f"""
        </tbody>
    </table>

    <div class="timestamp">
        생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</body>
</html>
"""
        return html


def main():
    parser = argparse.ArgumentParser(description='CSV 파일 기반 이미지 배치 비교')
    parser.add_argument('csv_file', help='이미지 경로가 포함된 CSV 파일')
    parser.add_argument('--output-dir', default='csv_comparison_results',
                       help='결과 저장 디렉토리 (기본값: csv_comparison_results)')

    args = parser.parse_args()

    # CSV 파일 존재 확인
    if not os.path.exists(args.csv_file):
        print(f"❌ CSV 파일을 찾을 수 없습니다: {args.csv_file}")
        return 1

    # 출력 디렉토리 생성
    os.makedirs(args.output_dir, exist_ok=True)

    # CSV 비교 실행
    comparator = CSVImageComparator(args.csv_file, args.output_dir)

    print(f"📂 CSV 파일 읽는 중: {args.csv_file}")
    image_pairs = comparator.read_csv()

    if not image_pairs:
        print("⚠️  처리할 이미지 쌍이 없습니다.")
        return 1

    print(f"✅ {len(image_pairs)}개의 이미지 쌍을 발견했습니다.")

    # 배치 비교 실행
    comparator.compare_images_batch(image_pairs)

    # 종합 리포트 생성
    comparator.generate_summary_report()

    return 0


if __name__ == '__main__':
    exit(main())