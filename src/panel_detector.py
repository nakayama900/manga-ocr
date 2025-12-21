"""コマ検出モジュール: テキスト領域の位置関係からコマを推定・グループ化"""

from typing import List, NamedTuple, Tuple
import logging
import numpy as np
from sklearn.cluster import DBSCAN

from .detector import TextRegion, sort_by_reading_order

logger = logging.getLogger(__name__)


class Panel(NamedTuple):
    """コマ（パネル）情報"""
    bbox: Tuple[int, int, int, int]  # コマの境界 (x1, y1, x2, y2)
    text_regions: List[TextRegion]   # コマ内のテキスト領域
    reading_order: int              # コマの読み順（0始まり）


def detect_panels(regions: List[TextRegion]) -> List[Panel]:
    """
    テキスト領域の位置関係からDBSCANを用いてコマを推定・グループ化
    
    アルゴリズム:
    1. テキスト領域の中心座標をDBSCANでクラスタリング。
    2. 同じクラスタに属する領域を同じコマとしてグループ化。
    3. 各コマの境界を計算し、コマ内のテキストをソート。
    4. コマ自体の読み順を決定。
    
    Args:
        regions: テキスト領域のリスト
    
    Returns:
        読み順でソートされたコマのリスト
    """
    if not regions:
        return []

    # 領域が少ない場合は、全体を1つのコマとして扱う
    if len(regions) <= 2:
        sorted_regions = sort_by_reading_order(regions)
        min_x = min(r.bbox[0] for r in regions)
        min_y = min(r.bbox[1] for r in regions)
        max_x = max(r.bbox[2] for r in regions)
        max_y = max(r.bbox[3] for r in regions)
        return [Panel(bbox=(min_x, min_y, max_x, max_y), text_regions=sorted_regions, reading_order=0)]

    # DBSCAN用のデータ準備 (x, yの中心座標)
    coordinates = np.array([( (r.bbox[0] + r.bbox[2]) / 2, (r.bbox[1] + r.bbox[3]) / 2 ) for r in regions])
    
    # DBSCANのパラメータ設定
    # eps: クラスタを形成するための最大距離。テキスト領域の平均的な高さの1.5倍を基準にする
    avg_height = sum(r.bbox[3] - r.bbox[1] for r in regions) / len(regions)
    eps = avg_height * 1.8  # 以前の閾値より寛容に設定
    min_samples = 1  # 1つの領域だけでもクラスタを形成可能にする

    # DBSCAN実行
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(coordinates)
    labels = db.labels_

    # ラベルごとに領域をグループ化
    panel_groups: dict[int, List[TextRegion]] = {}
    for i, label in enumerate(labels):
        if label not in panel_groups:
            panel_groups[label] = []
        panel_groups[label].append(regions[i])

    # 各グループをPanelオブジェクトに変換
    panel_objects: List[Panel] = []
    
    # ノイズ（ラベル-1）として扱われた領域を先に個別のパネルとして追加
    if -1 in panel_groups:
        for region in panel_groups[-1]:
             panel_objects.append(
                Panel(
                    bbox=region.bbox,
                    text_regions=[region],
                    reading_order=0 # 後でソート
                )
            )
        del panel_groups[-1]

    # クラスタリングされたパネルを追加
    for label, panel_regions in panel_groups.items():
        if not panel_regions:
            continue
        
        # コマ内のテキスト領域を読み順でソート
        sorted_regions_in_panel = sort_by_reading_order(panel_regions)
        
        # コマの境界を計算
        min_x = min(r.bbox[0] for r in panel_regions)
        min_y = min(r.bbox[1] for r in panel_regions)
        max_x = max(r.bbox[2] for r in panel_regions)
        max_y = max(r.bbox[3] for r in panel_regions)
        
        panel_objects.append(
            Panel(
                bbox=(min_x, min_y, max_x, max_y),
                text_regions=sorted_regions_in_panel,
                reading_order=0  # 後でソート
            )
        )

    # コマの読み順を決定 (sort_by_reading_orderと似たロジック)
    # コマの中心座標でソート
    panel_data = []
    for p in panel_objects:
        x1, y1, x2, y2 = p.bbox
        panel_data.append({'panel': p, 'cx': (x1 + x2) / 2, 'cy': (y1 + y2) / 2})

    # y中心でソート
    sorted_panels_by_y = sorted(panel_data, key=lambda p: p['cy'])

    # 段（行）にグループ化
    # 閾値は画像の高さの10%程度
    max_h = max(p['cy'] for p in sorted_panels_by_y)
    min_h = min(p['cy'] for p in sorted_panels_by_y)
    row_threshold = (max_h - min_h) * 0.15 if max_h > min_h else avg_height

    rows: List[List[dict]] = []
    if sorted_panels_by_y:
        current_row = [sorted_panels_by_y[0]]
        for p_data in sorted_panels_by_y[1:]:
            base_cy = current_row[0]['cy']
            if abs(p_data['cy'] - base_cy) <= row_threshold:
                current_row.append(p_data)
            else:
                rows.append(current_row)
                current_row = [p_data]
        rows.append(current_row)

    # フラット化して最終的な読み順を設定
    result: List[Panel] = []
    reading_order = 0
    for row in rows:
        # 段内でx中心の降順（右から左）でソート
        row.sort(key=lambda p: -p['cx'])
        for p_data in row:
            panel = p_data['panel']
            result.append(
                Panel(
                    bbox=panel.bbox,
                    text_regions=panel.text_regions,
                    reading_order=reading_order
                )
            )
            reading_order += 1
            
    return result

