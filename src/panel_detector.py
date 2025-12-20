"""コマ検出モジュール: テキスト領域の位置関係からコマを推定・グループ化"""

from typing import List, NamedTuple, Tuple
import logging

from .detector import TextRegion, sort_by_reading_order

logger = logging.getLogger(__name__)


class Panel(NamedTuple):
    """コマ（パネル）情報"""
    bbox: Tuple[int, int, int, int]  # コマの境界 (x1, y1, x2, y2)
    text_regions: List[TextRegion]   # コマ内のテキスト領域
    reading_order: int              # コマの読み順（0始まり）


def detect_panels(regions: List[TextRegion]) -> List[Panel]:
    """
    テキスト領域の位置関係からコマを推定・グループ化
    
    アルゴリズム:
    1. テキスト領域間の距離を計算
    2. 近接する領域を同じコマとしてグループ化
    3. コマの境界を領域の外接矩形で推定
    4. コマの読み順を決定
    
    Args:
        regions: テキスト領域のリスト
    
    Returns:
        読み順でソートされたコマのリスト
    """
    if not regions:
        return []
    
    if len(regions) == 1:
        # 領域が1つだけの場合は、その領域を1つのコマとして扱う
        region = regions[0]
        x1, y1, x2, y2 = region.bbox
        return [
            Panel(
                bbox=(x1, y1, x2, y2),
                text_regions=[region],
                reading_order=0
            )
        ]
    
    # 各領域の中心座標とサイズを計算
    region_data = []
    for region in regions:
        x1, y1, x2, y2 = region.bbox
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        width = x2 - x1
        height = y2 - y1
        region_data.append((region, center_x, center_y, width, height))
    
    # 平均的な領域サイズを計算（閾値計算用）
    avg_width = sum(w for _, _, _, w, _ in region_data) / len(region_data)
    avg_height = sum(h for _, _, _, _, h in region_data) / len(region_data)
    
    # 画像サイズを推定（領域の最大座標から）
    max_x = max(x2 for r in regions for x1, y1, x2, y2 in [r.bbox])
    max_y = max(y2 for r in regions for x1, y1, x2, y2 in [r.bbox])
    image_width = max_x
    image_height = max_y
    
    # コマ内のテキスト領域をグループ化するための閾値
    # 非常に近接している領域のみを同じコマとして扱う
    # コマ内のテキスト領域は通常、領域サイズの2倍以内に収まる
    # ただし、画像サイズに対して適切な比率を保つ
    panel_threshold_x = max(avg_width * 2.0, min(image_width * 0.08, 150))
    panel_threshold_y = max(avg_height * 2.0, min(image_height * 0.08, 150))
    
    logger.debug(f"Panel detection thresholds: x={panel_threshold_x:.1f}, y={panel_threshold_y:.1f} (avg_size={avg_width:.1f}x{avg_height:.1f}, image={image_width}x{image_height})")
    
    # コマごとにグループ化
    panels: List[List[TextRegion]] = []
    used = set()
    
    for region, cx, cy, w, h in region_data:
        if id(region) in used:
            continue
        
        # 同じコマ（非常に近接する領域）を探す
        panel_regions = [region]
        used.add(id(region))
        
        for other_region, other_cx, other_cy, other_w, other_h in region_data:
            if id(other_region) in used:
                continue
            
            # 領域間の距離を計算
            distance_x = abs(cx - other_cx)
            distance_y = abs(cy - other_cy)
            
            # 両方向で非常に近接している場合のみ同じコマとして扱う
            # これにより、コマを過剰にグループ化することを防ぐ
            if distance_x <= panel_threshold_x and distance_y <= panel_threshold_y:
                panel_regions.append(other_region)
                used.add(id(other_region))
        
        panels.append(panel_regions)
    
    # 各コマの境界を計算（外接矩形）
    panel_objects: List[Panel] = []
    for panel_regions in panels:
        if not panel_regions:
            continue
        
        # コマ内のテキスト領域を読み順でソート
        sorted_regions = sort_by_reading_order(panel_regions)
        
        # コマの境界を計算（すべての領域の外接矩形）
        min_x = min(x1 for r in panel_regions for x1, y1, x2, y2 in [r.bbox])
        min_y = min(y1 for r in panel_regions for x1, y1, x2, y2 in [r.bbox])
        max_x = max(x2 for r in panel_regions for x1, y1, x2, y2 in [r.bbox])
        max_y = max(y2 for r in panel_regions for x1, y1, x2, y2 in [r.bbox])
        
        panel_objects.append(
            Panel(
                bbox=(min_x, min_y, max_x, max_y),
                text_regions=sorted_regions,
                reading_order=0  # 後でソート
            )
        )
    
    # コマが1つしかない場合は、フォールバック（現在の実装と同じ動作）
    if len(panel_objects) <= 1:
        logger.debug("コマが1つしか検出されなかったため、全領域を1つのコマとして扱います")
        # すべての領域を1つのコマとして扱う
        sorted_all_regions = sort_by_reading_order(regions)
        min_x = min(x1 for r in regions for x1, y1, x2, y2 in [r.bbox])
        min_y = min(y1 for r in regions for x1, y1, x2, y2 in [r.bbox])
        max_x = max(x2 for r in regions for x1, y1, x2, y2 in [r.bbox])
        max_y = max(y2 for r in regions for x1, y1, x2, y2 in [r.bbox])
        return [
            Panel(
                bbox=(min_x, min_y, max_x, max_y),
                text_regions=sorted_all_regions,
                reading_order=0
            )
        ]
    
    # コマの読み順を決定（既存のsort_by_reading_orderアルゴリズムを活用）
    # コマの右上座標（右端x、上端y）を使用してソート
    panel_top_right = []
    for panel in panel_objects:
        x1, y1, x2, y2 = panel.bbox
        right_x = x2  # 右端x座標
        top_y = y1    # 上端y座標（右上のy座標）
        panel_top_right.append((panel, right_x, top_y))
    
    # 段組みを考慮したソート（既存のアルゴリズムと同様）
    # 画像の高さを取得（右上のy座標を使用）
    max_panel_y = max(ty for _, _, ty in panel_top_right)
    min_panel_y = min(ty for _, _, ty in panel_top_right)
    image_height = max_panel_y - min_panel_y
    
    # 段の閾値: 平均的なコマの高さの60%以内を同じ段とみなす
    avg_panel_height = sum((y2 - y1) for p in panel_objects for x1, y1, x2, y2 in [p.bbox]) / len(panel_objects)
    row_threshold = max(20, min(avg_panel_height * 0.6, image_height * 0.08))
    
    # 段（行）ごとにグループ化
    rows: List[List[Panel]] = []
    used_panels = set()
    
    # 右上のy座標（上端）でソート
    for panel, rx, ty in sorted(panel_top_right, key=lambda x: x[2]):  # 上端y座標でソート
        if id(panel) in used_panels:
            continue
        
        # 同じ段（右上のy座標が近い）のコマを探す
        row = [panel]
        used_panels.add(id(panel))
        
        for other_panel, other_rx, other_ty in panel_top_right:
            if id(other_panel) in used_panels:
                continue
            
            # 右上のy座標（上端）の差が閾値以内なら同じ段
            if abs(ty - other_ty) <= row_threshold:
                row.append(other_panel)
                used_panels.add(id(other_panel))
        
        # デバッグログ: ソート前の順序
        if len(row) > 1:
            logger.debug(f"段内コマ（ソート前）: {len(row)}個")
            for i, p in enumerate(row):
                x1, y1, x2, y2 = p.bbox
                logger.debug(f"  コマ[{i}]: 右上=({x2},{y1}), 右端={x2}, 上端={y1}")
        
        # 段内で右から左にソート（右上のx座標=右端の降順、同じ場合は右上のy座標=上端の昇順）
        row.sort(key=lambda p: (-p.bbox[2], p.bbox[1]))  # 右端x座標の降順、同じ場合は上端y座標の昇順
        
        # デバッグログ: ソート後の順序
        if len(row) > 1:
            logger.debug(f"段内コマ（ソート後）: {len(row)}個")
            for i, p in enumerate(row):
                x1, y1, x2, y2 = p.bbox
                logger.debug(f"  コマ[{i}]: 右上=({x2},{y1}), 右端={x2}, 上端={y1}")
        
        rows.append(row)
    
    # 段を上から下にソート（各段の最小y座標=右上のy座標でソート）
    rows.sort(key=lambda row: min(p.bbox[1] for p in row))  # 上端y座標（右上のy座標）でソート
    
    # デバッグログ: 最終的な読み順
    logger.debug(f"コマの読み順（最終）: {len(rows)}段、合計{sum(len(row) for row in rows)}コマ")
    for row_idx, row in enumerate(rows):
        logger.debug(f"  段[{row_idx}]: {len(row)}コマ")
        for panel_idx, panel in enumerate(row):
            x1, y1, x2, y2 = panel.bbox
            logger.debug(f"    コマ[{panel_idx}]: 右上=({x2},{y1}), 右端={x2}, 上端={y1}")
    
    # フラット化して読み順を設定
    result = []
    reading_order = 0
    for row in rows:
        for panel in row:
            result.append(
                Panel(
                    bbox=panel.bbox,
                    text_regions=panel.text_regions,
                    reading_order=reading_order
                )
            )
            reading_order += 1
    
    return result

