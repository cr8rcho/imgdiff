#!/usr/bin/env python3
"""
imgdiff 사용 예제
"""

from imgdiff import ImageComparator

def example_basic():
    """기본 사용 예제"""
    print("=" * 60)
    print("기본 사용 예제")
    print("=" * 60)

    # 두 이미지 비교
    comparator = ImageComparator('image1.png', 'image2.png')

    # 이미지 로드
    comparator.load_images()

    # 통계 정보 확인
    stats = comparator.get_statistics()

    print(f"전체 픽셀 수: {stats['total_pixels']:,}")
    print(f"변경된 픽셀: {stats['changed_pixels']:,} ({stats['changed_percentage']:.2f}%)")
    print(f"차이율: {stats['diff_percentage']:.2f}%")

    # 차이 이미지 저장
    diff_img = comparator.create_diff_image('highlight')
    diff_img.save('difference_highlight.png')
    print("\n차이 이미지가 'difference_highlight.png'에 저장되었습니다.")


def example_advanced():
    """고급 사용 예제"""
    print("\n" + "=" * 60)
    print("고급 사용 예제")
    print("=" * 60)

    comparator = ImageComparator('image1.png', 'image2.png')

    # 다양한 시각화 모드
    modes = ['difference', 'highlight', 'heatmap']

    for mode in modes:
        diff_img = comparator.create_diff_image(mode)
        filename = f'diff_{mode}.png'
        diff_img.save(filename)
        print(f"{mode} 모드 이미지 저장: {filename}")

    # 변경된 영역 찾기
    regions = comparator.find_changed_regions(threshold=20, min_area=100)

    print(f"\n발견된 변경 영역: {len(regions)}개")
    for i, region in enumerate(regions[:5], 1):  # 최대 5개만 표시
        print(f"  영역 {i}: 위치({region['x']}, {region['y']}), "
              f"크기({region['width']}x{region['height']})")


def example_full_report():
    """전체 리포트 생성 예제"""
    print("\n" + "=" * 60)
    print("전체 리포트 생성 예제")
    print("=" * 60)

    comparator = ImageComparator('image1.png', 'image2.png')

    # 종합 리포트 생성 (comparison_results 디렉토리에 저장)
    stats, regions = comparator.save_comparison_report('my_comparison')

    # 나란히 비교 이미지 생성
    comparator.create_side_by_side_comparison('comparison_view.png')


if __name__ == '__main__':
    print("이미지 차이 비교 도구 예제\n")
    print("주의: 이 예제를 실행하려면 'image1.png'와 'image2.png' 파일이 필요합니다.\n")

    try:
        # 기본 예제 실행
        example_basic()

        # 고급 예제 실행
        example_advanced()

        # 전체 리포트 예제
        example_full_report()

        print("\n✅ 모든 예제가 성공적으로 실행되었습니다!")

    except FileNotFoundError:
        print("\n⚠️  'image1.png'와 'image2.png' 파일을 먼저 준비해주세요.")
        print("테스트용 이미지를 생성하려면 create_test_images.py를 실행하세요.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")