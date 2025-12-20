"""detector.py のユニットテスト"""

import pytest
from PIL import Image
from src.detector import (
    detect_text_regions,
    sort_by_reading_order,
    crop_text_regions,
    TextRegion,
    HAS_COMIC_DETECTOR
)


def test_sort_by_reading_order():
    """読み順ソートのテスト（段組みを考慮）"""
    # テスト用の領域を作成（右上から左下へ）
    # 上段: 右(200,50) -> 左(50,50)
    # 下段: 右(200,200) -> 左(50,200)
    regions = [
        TextRegion(bbox=(50, 50, 150, 100), image=None, reading_order=0),   # 上段左
        TextRegion(bbox=(200, 200, 300, 250), image=None, reading_order=0),  # 下段右
        TextRegion(bbox=(200, 50, 300, 100), image=None, reading_order=0),  # 上段右
        TextRegion(bbox=(50, 200, 150, 250), image=None, reading_order=0),   # 下段左
    ]
    
    sorted_regions = sort_by_reading_order(regions)
    
    # 読み順が設定されていることを確認
    assert all(r.reading_order >= 0 for r in sorted_regions)
    assert len(sorted_regions) == len(regions)
    
    # 正しい読み順を確認
    # 期待される順序: 上段右(0) -> 上段左(1) -> 下段右(2) -> 下段左(3)
    assert sorted_regions[0].bbox[0] == 200  # 上段右
    assert sorted_regions[0].bbox[1] == 50
    assert sorted_regions[1].bbox[0] == 50   # 上段左
    assert sorted_regions[1].bbox[1] == 50
    assert sorted_regions[2].bbox[0] == 200  # 下段右
    assert sorted_regions[2].bbox[1] == 200
    assert sorted_regions[3].bbox[0] == 50   # 下段左
    assert sorted_regions[3].bbox[1] == 200


def test_crop_text_regions():
    """領域クロップのテスト"""
    img = Image.new('RGB', (300, 300), color='white')
    
    regions = [
        TextRegion(bbox=(50, 50, 150, 100), image=None, reading_order=0),
        TextRegion(bbox=(200, 200, 300, 250), image=None, reading_order=1),
    ]
    
    cropped = crop_text_regions(img, regions)
    assert len(cropped) == 2
    assert all(r.image is not None for r in cropped)
    assert all(r.image.size[0] > 0 and r.image.size[1] > 0 for r in cropped)


def test_detect_text_regions_fallback():
    """テキスト検出のフォールバックテスト"""
    img = Image.new('RGB', (100, 100), color='white')
    
    # comic-text-detectorが利用できない場合でも動作することを確認
    regions = detect_text_regions(img, device="cpu")
    assert len(regions) > 0
    assert regions[0].bbox == (0, 0, 100, 100)  # フォールバック時は画像全体

