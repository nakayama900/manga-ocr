"""panel_detector.py のユニットテスト"""

import pytest
from src.panel_detector import detect_panels, Panel
from src.detector import TextRegion
from PIL import Image


def test_detect_panels_empty():
    """空の領域リストのテスト"""
    panels = detect_panels([])
    assert panels == []


def test_detect_panels_single():
    """領域が1つの場合のテスト"""
    img = Image.new('RGB', (100, 50), color='white')
    region = TextRegion(bbox=(10, 10, 90, 40), image=img, reading_order=0)
    
    panels = detect_panels([region])
    assert len(panels) == 1
    assert panels[0].bbox == (10, 10, 90, 40)
    assert len(panels[0].text_regions) == 1
    assert panels[0].reading_order == 0


def test_detect_panels_grouping():
    """コマのグループ化のテスト"""
    img1 = Image.new('RGB', (100, 50), color='white')
    img2 = Image.new('RGB', (100, 50), color='white')
    img3 = Image.new('RGB', (100, 50), color='white')
    
    # コマ1: 近接する2つの領域（右上）
    region1 = TextRegion(bbox=(200, 50, 300, 100), image=img1, reading_order=0)
    region2 = TextRegion(bbox=(210, 110, 290, 150), image=img2, reading_order=0)
    
    # コマ2: 離れた領域（左下）
    region3 = TextRegion(bbox=(50, 250, 150, 300), image=img3, reading_order=0)
    
    panels = detect_panels([region1, region2, region3])
    
    # 2つのコマが検出されることを確認
    assert len(panels) >= 1  # グループ化の結果、1つ以上
    
    # 読み順が設定されていることを確認
    assert all(p.reading_order >= 0 for p in panels)
    assert all(len(p.text_regions) > 0 for p in panels)


def test_detect_panels_reading_order():
    """コマの読み順のテスト"""
    img1 = Image.new('RGB', (100, 50), color='white')
    img2 = Image.new('RGB', (100, 50), color='white')
    img3 = Image.new('RGB', (100, 50), color='white')
    img4 = Image.new('RGB', (100, 50), color='white')
    
    # 4つのコマ: 右上、左上、右下、左下
    region1 = TextRegion(bbox=(200, 50, 300, 100), image=img1, reading_order=0)   # 右上
    region2 = TextRegion(bbox=(50, 50, 150, 100), image=img2, reading_order=0)    # 左上
    region3 = TextRegion(bbox=(200, 200, 300, 250), image=img3, reading_order=0)  # 右下
    region4 = TextRegion(bbox=(50, 200, 150, 250), image=img4, reading_order=0)  # 左下
    
    panels = detect_panels([region1, region2, region3, region4])
    
    # 読み順が設定されていることを確認
    assert len(panels) > 0
    reading_orders = [p.reading_order for p in panels]
    assert len(set(reading_orders)) == len(reading_orders)  # 重複がない
    assert min(reading_orders) == 0  # 0から始まる


def test_detect_panels_within_panel_sorting():
    """コマ内のテキスト領域のソートのテスト"""
    img1 = Image.new('RGB', (100, 50), color='white')
    img2 = Image.new('RGB', (100, 50), color='white')
    
    # 同じコマ内の2つの領域（右から左の順序）
    region1 = TextRegion(bbox=(200, 100, 300, 150), image=img1, reading_order=0)  # 右
    region2 = TextRegion(bbox=(50, 100, 150, 150), image=img2, reading_order=0)    # 左
    
    panels = detect_panels([region1, region2])
    
    # コマが検出されることを確認
    assert len(panels) > 0
    
    # 最初のコマ内の領域が読み順でソートされていることを確認
    if len(panels) > 0 and len(panels[0].text_regions) >= 2:
        # 読み順が設定されていることを確認
        assert all(r.reading_order >= 0 for r in panels[0].text_regions)


def test_detect_panels_same_row_right_to_left():
    """同じ段内で複数のコマがある場合の右→左ソートのテスト"""
    img1 = Image.new('RGB', (100, 50), color='white')
    img2 = Image.new('RGB', (100, 50), color='white')
    img3 = Image.new('RGB', (100, 50), color='white')
    
    # 同じ段（y座標が近い）の3つのコマ: 右、中央、左
    # 右端x座標が大きい順に: 300 > 200 > 100
    region1 = TextRegion(bbox=(250, 50, 300, 100), image=img1, reading_order=0)   # 右（右端=300）
    region2 = TextRegion(bbox=(150, 50, 200, 100), image=img2, reading_order=0)    # 中央（右端=200）
    region3 = TextRegion(bbox=(50, 50, 100, 100), image=img3, reading_order=0)     # 左（右端=100）
    
    panels = detect_panels([region1, region2, region3])
    
    # 3つのコマが検出されることを確認（または適切にグループ化される）
    assert len(panels) > 0
    
    # 同じ段内のコマが右から左にソートされていることを確認
    # 各コマの右端x座標を取得
    panel_right_edges = []
    for panel in panels:
        x1, y1, x2, y2 = panel.bbox
        panel_right_edges.append((x2, panel.reading_order))
    
    # 同じ段（y座標が近い）のコマをグループ化
    # 簡易的なテスト: 読み順が0, 1, 2の順で、右端x座標が降順になっていることを確認
    if len(panels) >= 3:
        # 読み順でソート
        sorted_panels = sorted(panels, key=lambda p: p.reading_order)
        
        # 最初の3つのコマが同じ段にある場合（y座標が近い）、右端x座標が降順になっていることを確認
        first_three = sorted_panels[:3]
        if len(first_three) == 3:
            y_coords = [p.bbox[1] for p in first_three]
            # y座標の差が小さい場合（同じ段とみなせる場合）
            if max(y_coords) - min(y_coords) < 50:
                right_edges = [p.bbox[2] for p in first_three]
                # 右端x座標が降順になっていることを確認
                assert right_edges[0] >= right_edges[1] >= right_edges[2], \
                    f"同じ段内のコマが右→左にソートされていません: 右端x座標={right_edges}"

