#!/usr/bin/env python3
"""
이미지 차이 비교 도구
두 이미지 간의 차이를 분석하고 시각화합니다.
"""

from PIL import Image, ImageDraw, ImageFont
import numpy as np
import argparse
import os
from typing import Tuple, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import cv2


class ImageComparator:
    def __init__(self, image1_path: str, image2_path: str):
        """
        이미지 비교 클래스 초기화

        Args:
            image1_path: 첫 번째 이미지 경로
            image2_path: 두 번째 이미지 경로
        """
        self.image1_path = image1_path
        self.image2_path = image2_path
        self.img1 = None
        self.img2 = None
        self.diff_array = None

    def load_images(self) -> Tuple[Image.Image, Image.Image]:
        """이미지를 로드하고 크기를 맞춥니다."""
        try:
            self.img1 = Image.open(self.image1_path).convert('RGB')
            self.img2 = Image.open(self.image2_path).convert('RGB')
        except FileNotFoundError as e:
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {e}")
        except Exception as e:
            raise Exception(f"이미지 로드 중 오류 발생: {e}")

        # 크기가 다르면 리사이즈
        if self.img1.size != self.img2.size:
            print(f"⚠️  이미지 크기 차이 감지: {self.img1.size} vs {self.img2.size}")
            print(f"   두 번째 이미지를 첫 번째 이미지 크기로 리사이즈합니다.")
            self.img2 = self.img2.resize(self.img1.size, Image.Resampling.LANCZOS)

        return self.img1, self.img2

    def calculate_difference(self) -> np.ndarray:
        """픽셀 단위로 차이를 계산합니다."""
        if self.img1 is None or self.img2 is None:
            self.load_images()

        # numpy 배열로 변환
        arr1 = np.array(self.img1)
        arr2 = np.array(self.img2)

        # 픽셀 단위 차이 계산
        self.diff_array = np.abs(arr1.astype(np.int16) - arr2.astype(np.int16))

        return self.diff_array

    def get_statistics(self, threshold: int = 10) -> dict:
        """
        차이에 대한 통계를 계산합니다.

        Args:
            threshold: 변경된 픽셀로 간주할 차이 임계값 (기본값: 10)
        """
        if self.diff_array is None:
            self.calculate_difference()

        # RGB 채널별 차이
        r_diff = self.diff_array[:, :, 0]
        g_diff = self.diff_array[:, :, 1]
        b_diff = self.diff_array[:, :, 2]

        # 전체 차이율 계산
        total_pixels = self.diff_array.shape[0] * self.diff_array.shape[1]
        max_possible_diff = total_pixels * 255 * 3  # RGB 3채널
        actual_diff = np.sum(self.diff_array)
        diff_percentage = (actual_diff / max_possible_diff) * 100

        # 변경된 픽셀 수 (임계값 기준)
        diff_mask = np.any(self.diff_array > threshold, axis=2)
        changed_pixels = np.sum(diff_mask)
        changed_percentage = (changed_pixels / total_pixels) * 100

        stats = {
            'total_pixels': total_pixels,
            'diff_percentage': diff_percentage,
            'changed_pixels': changed_pixels,
            'changed_percentage': changed_percentage,
            'mean_diff': {
                'r': np.mean(r_diff),
                'g': np.mean(g_diff),
                'b': np.mean(b_diff)
            },
            'max_diff': {
                'r': np.max(r_diff),
                'g': np.max(g_diff),
                'b': np.max(b_diff)
            }
        }

        return stats

    def get_processed_statistics(self, threshold: int = 20,
                                 morphology_kernel_size: int = 0,
                                 blur_kernel_size: int = 0) -> dict:
        """
        OpenCV 처리 후 마스크 기반 통계를 계산합니다.
        create_diff_image의 'highlight' 모드와 동일한 처리를 적용합니다.

        Args:
            threshold: 차이 임계값 (기본값: 20)
            morphology_kernel_size: 형태학적 연산 커널 크기 (0이면 비활성화)
            blur_kernel_size: Gaussian blur 커널 크기 (0이면 비활성화)

        Returns:
            처리된 마스크 기반 통계 정보
        """
        if self.diff_array is None:
            self.calculate_difference()

        total_pixels = self.diff_array.shape[0] * self.diff_array.shape[1]

        # 원본 마스크 생성 (create_diff_image의 'highlight' 모드와 동일)
        diff_mask = np.any(self.diff_array > threshold, axis=2).astype(np.uint8)

        # 형태학적 연산 적용
        if morphology_kernel_size > 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                               (morphology_kernel_size, morphology_kernel_size))
            diff_mask = cv2.morphologyEx(diff_mask, cv2.MORPH_OPEN, kernel)

        # Gaussian blur 적용
        if blur_kernel_size > 0:
            if blur_kernel_size % 2 == 0:
                blur_kernel_size += 1
            diff_mask_float = diff_mask.astype(np.float32)
            diff_mask_blurred = cv2.GaussianBlur(diff_mask_float, (blur_kernel_size, blur_kernel_size), 0)
            diff_mask = (diff_mask_blurred > 0.5).astype(np.uint8)

        # 처리된 마스크에서 통계 계산
        changed_pixels = np.sum(diff_mask)
        changed_percentage = (changed_pixels / total_pixels) * 100

        # 처리된 영역의 실제 차이 계산
        diff_mask_bool = diff_mask.astype(bool)
        if changed_pixels > 0:
            # 변경된 영역의 실제 픽셀 차이 합계
            actual_diff_in_region = np.sum(self.diff_array[diff_mask_bool])
        else:
            actual_diff_in_region = 0

        max_possible_diff = total_pixels * 255 * 3  # RGB 3채널
        diff_percentage = (actual_diff_in_region / max_possible_diff) * 100 if max_possible_diff > 0 else 0

        return {
            'total_pixels': int(total_pixels),
            'changed_pixels': int(changed_pixels),
            'changed_percentage': float(changed_percentage),
            'diff_percentage': float(diff_percentage),
            'processing_applied': {
                'threshold': threshold,
                'morphology_kernel': morphology_kernel_size,
                'blur_kernel': blur_kernel_size
            }
        }

    def create_diff_image(self, mode: str = 'difference', threshold: int = 20,
                          morphology_kernel_size: int = 0, blur_kernel_size: int = 0) -> Image.Image:
        """
        차이를 시각화한 이미지를 생성합니다.

        Args:
            mode: 시각화 모드 ('difference', 'highlight', 'heatmap')
            threshold: 차이 임계값 (기본값: 20)
            morphology_kernel_size: 형태학적 연산 커널 크기 (0이면 비활성화, 기본값: 0)
            blur_kernel_size: Gaussian blur 커널 크기 (0이면 비활성화, 기본값: 0)
        """
        if self.diff_array is None:
            self.calculate_difference()

        if mode == 'difference':
            # 차이를 그대로 표시
            diff_img = Image.fromarray(self.diff_array.astype('uint8'))

        elif mode == 'highlight':
            # 차이가 있는 부분을 빨간색으로 강조
            diff_mask = np.any(self.diff_array > threshold, axis=2).astype(np.uint8)

            # 형태학적 연산 적용 (노이즈 제거)
            if morphology_kernel_size > 0:
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                                   (morphology_kernel_size, morphology_kernel_size))
                # Opening: erosion → dilation (작은 노이즈 제거)
                diff_mask = cv2.morphologyEx(diff_mask, cv2.MORPH_OPEN, kernel)

            # Gaussian blur 적용 (외곽선 부드럽게)
            if blur_kernel_size > 0:
                # blur_kernel_size는 홀수여야 함
                if blur_kernel_size % 2 == 0:
                    blur_kernel_size += 1
                diff_mask_float = diff_mask.astype(np.float32)
                diff_mask_blurred = cv2.GaussianBlur(diff_mask_float, (blur_kernel_size, blur_kernel_size), 0)
                # threshold 다시 적용
                diff_mask = (diff_mask_blurred > 0.5).astype(np.uint8)

            # Boolean mask로 변환
            diff_mask_bool = diff_mask.astype(bool)

            # 원본 이미지를 회색조로 변환
            base_img = self.img1.convert('L').convert('RGB')
            base_array = np.array(base_img)

            # 차이가 있는 부분을 빨간색으로 표시
            highlight_array = base_array.copy()
            highlight_array[diff_mask_bool] = [255, 0, 0]

            diff_img = Image.fromarray(highlight_array.astype('uint8'))

        elif mode == 'heatmap':
            # 차이 강도를 히트맵으로 표시
            diff_intensity = np.mean(self.diff_array, axis=2)

            # 정규화 (0-255)
            normalized = (diff_intensity / diff_intensity.max() * 255 if diff_intensity.max() > 0
                         else diff_intensity)

            # 히트맵 색상 적용 (파란색 -> 빨간색)
            heatmap = np.zeros((normalized.shape[0], normalized.shape[1], 3), dtype=np.uint8)
            heatmap[:, :, 0] = normalized  # Red channel
            heatmap[:, :, 2] = 255 - normalized  # Blue channel

            diff_img = Image.fromarray(heatmap)

        else:
            raise ValueError(f"지원하지 않는 모드: {mode}")

        return diff_img

    def find_changed_regions(self, threshold: int = 20, min_area: int = 100,
                            morphology_kernel_size: int = 0) -> list:
        """
        변경된 영역을 찾아 바운딩 박스로 반환합니다.

        Args:
            threshold: 차이 임계값
            min_area: 최소 영역 크기
            morphology_kernel_size: 형태학적 연산 커널 크기 (0이면 비활성화)
        """
        if self.diff_array is None:
            self.calculate_difference()

        # 차이가 임계값 이상인 픽셀 마스크
        diff_mask = np.any(self.diff_array > threshold, axis=2).astype(np.uint8)

        # 형태학적 연산 적용 (노이즈 제거)
        if morphology_kernel_size > 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                               (morphology_kernel_size, morphology_kernel_size))
            # Opening: erosion → dilation (작은 노이즈 제거)
            diff_mask = cv2.morphologyEx(diff_mask, cv2.MORPH_OPEN, kernel)

        # 연결된 컴포넌트 찾기 (간단한 구현)
        from scipy import ndimage
        labeled_array, num_features = ndimage.label(diff_mask)

        regions = []
        for i in range(1, num_features + 1):
            component = (labeled_array == i)
            if np.sum(component) >= min_area:
                rows, cols = np.where(component)
                regions.append({
                    'x': int(np.min(cols)),
                    'y': int(np.min(rows)),
                    'width': int(np.max(cols) - np.min(cols) + 1),
                    'height': int(np.max(rows) - np.min(rows) + 1),
                    'area': int(np.sum(component))
                })

        return regions

    def save_comparison_report(self, output_dir: str = 'comparison_results'):
        """종합 비교 리포트를 저장합니다."""
        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)

        # 통계 정보 가져오기
        stats = self.get_statistics()

        # 차이 이미지들 생성 및 저장
        diff_img = self.create_diff_image('difference')
        diff_img.save(os.path.join(output_dir, 'difference.png'))

        highlight_img = self.create_diff_image('highlight')
        highlight_img.save(os.path.join(output_dir, 'highlight.png'))

        heatmap_img = self.create_diff_image('heatmap')
        heatmap_img.save(os.path.join(output_dir, 'heatmap.png'))

        # 변경된 영역 찾기
        regions = self.find_changed_regions()

        # 변경 영역 표시 이미지 생성
        region_img = self.img1.copy()
        draw = ImageDraw.Draw(region_img)
        for region in regions:
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            draw.rectangle([x, y, x+w, y+h], outline='red', width=2)
        region_img.save(os.path.join(output_dir, 'regions.png'))

        # 텍스트 리포트 생성
        report = f"""이미지 비교 리포트
=====================================
원본 이미지 1: {self.image1_path}
원본 이미지 2: {self.image2_path}
이미지 크기: {self.img1.size}

통계 정보
-------------------------------------
전체 픽셀 수: {stats['total_pixels']:,}
변경된 픽셀 수: {stats['changed_pixels']:,} ({stats['changed_percentage']:.2f}%)
전체 차이율: {stats['diff_percentage']:.2f}%

채널별 평균 차이
-------------------------------------
Red:   {stats['mean_diff']['r']:.2f}
Green: {stats['mean_diff']['g']:.2f}
Blue:  {stats['mean_diff']['b']:.2f}

채널별 최대 차이
-------------------------------------
Red:   {stats['max_diff']['r']}
Green: {stats['max_diff']['g']}
Blue:  {stats['max_diff']['b']}

변경된 영역
-------------------------------------
발견된 영역 수: {len(regions)}
"""

        for i, region in enumerate(regions, 1):
            report += f"\n영역 {i}:"
            report += f"\n  위치: ({region['x']}, {region['y']})"
            report += f"\n  크기: {region['width']} x {region['height']}"
            report += f"\n  면적: {region['area']} pixels"

        # 리포트 저장
        with open(os.path.join(output_dir, 'report.txt'), 'w', encoding='utf-8') as f:
            f.write(report)

        print(report)
        print(f"\n✅ 비교 결과가 '{output_dir}' 디렉토리에 저장되었습니다.")

        return stats, regions

    def create_side_by_side_comparison(self, output_path: str = 'side_by_side.png',
                                       threshold: int = 20, morphology_kernel_size: int = 0,
                                       blur_kernel_size: int = 0):
        """
        원본 이미지들과 차이를 나란히 표시합니다.

        Args:
            output_path: 저장할 파일 경로
            threshold: 차이 임계값
            morphology_kernel_size: 형태학적 연산 커널 크기
            blur_kernel_size: 가우시안 블러 커널 크기
        """
        if self.diff_array is None:
            self.calculate_difference()

        fig, axes = plt.subplots(1, 4, figsize=(20, 5))

        # 원본 이미지 1
        axes[0].imshow(self.img1)
        axes[0].set_title('이미지 1')
        axes[0].axis('off')

        # 원본 이미지 2
        axes[1].imshow(self.img2)
        axes[1].set_title('이미지 2')
        axes[1].axis('off')

        # 차이 이미지
        diff_img = self.create_diff_image('difference')
        axes[2].imshow(diff_img)
        axes[2].set_title('픽셀 차이')
        axes[2].axis('off')

        # 하이라이트 이미지 (새로운 파라미터 적용)
        highlight_img = self.create_diff_image(
            'highlight',
            threshold=threshold,
            morphology_kernel_size=morphology_kernel_size,
            blur_kernel_size=blur_kernel_size
        )
        axes[3].imshow(highlight_img)
        axes[3].set_title('변경 영역 강조')
        axes[3].axis('off')

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"✅ 비교 이미지가 '{output_path}'에 저장되었습니다.")


def main():
    parser = argparse.ArgumentParser(description='두 이미지의 차이를 비교합니다.')
    parser.add_argument('image1', help='첫 번째 이미지 경로')
    parser.add_argument('image2', help='두 번째 이미지 경로')
    parser.add_argument('--output-dir', default='comparison_results',
                       help='결과를 저장할 디렉토리 (기본값: comparison_results)')
    parser.add_argument('--mode', choices=['quick', 'full'], default='full',
                       help='비교 모드 (quick: 빠른 비교, full: 전체 리포트)')

    args = parser.parse_args()

    try:
        # 이미지 비교 객체 생성
        comparator = ImageComparator(args.image1, args.image2)

        if args.mode == 'quick':
            # 빠른 비교 모드
            comparator.load_images()
            stats = comparator.get_statistics()

            print(f"\n📊 빠른 비교 결과")
            print(f"{'='*50}")
            print(f"차이율: {stats['diff_percentage']:.2f}%")
            print(f"변경된 픽셀: {stats['changed_percentage']:.2f}%")

            # 차이 이미지만 저장
            diff_img = comparator.create_diff_image('highlight')
            diff_img.save('quick_diff.png')
            print(f"\n✅ 차이 이미지가 'quick_diff.png'에 저장되었습니다.")

        else:
            # 전체 리포트 모드
            print(f"\n🔍 이미지 비교 시작...")
            print(f"{'='*50}")

            # 종합 리포트 생성
            stats, regions = comparator.save_comparison_report(args.output_dir)

            # 나란히 비교 이미지 생성
            side_by_side_path = os.path.join(args.output_dir, 'side_by_side.png')
            comparator.create_side_by_side_comparison(side_by_side_path)

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())