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

    # --- パネルの読み順を決定する新しいロジック ---
    from functools import cmp_to_key

    def _compare_panels(p1_data, p2_data):
        """2つのパネルの読み順を比較する関数"""
        p1_bbox = p1_data['panel'].bbox
        p2_bbox = p2_data['panel'].bbox

        x1_1, y1_1, x2_1, y2_1 = p1_bbox
        x1_2, y1_2, x2_2, y2_2 = p2_bbox

        h1 = y2_1 - y1_1
        h2 = y2_2 - y1_2

        # y方向の重なりの長さを計算
        y_overlap = max(0, min(y2_1, y2_2) - max(y1_1, y1_2))

        # 重なりがそれぞれの高さの小さい方の20%以上あれば、同じ段とみなす
        # この閾値は経験的なもので、調整の余地あり
        is_same_row = y_overlap > (min(h1, h2) * 0.2) if min(h1, h2) > 0 else False

        if is_same_row:
            # 同じ段なら、x中心で比較（右が先）
            cx1 = p1_data['cx']
            cx2 = p2_data['cx']
            if cx1 > cx2:
                return -1  # p1が先
            else:
                return 1   # p2が先
        else:
            # 別の段なら、y中心で比較（上が先）
            cy1 = p1_data['cy']
            cy2 = p2_data['cy']
            if cy1 < cy2:
                return -1  # p1が先
            else:
                return 1   # p2が先
        return 0

    # パネルの中心座標データを準備
    panel_data = []
    for p in panel_objects:
        x1, y1, x2, y2 = p.bbox
        panel_data.append({'panel': p, 'cx': (x1 + x2) / 2, 'cy': (y1 + y2) / 2})

    # カスタム比較関数でソート
    sorted_panel_data = sorted(panel_data, key=cmp_to_key(_compare_panels))

    # フラット化して最終的な読み順を設定
    result: List[Panel] = []
    reading_order = 0
    for p_data in sorted_panel_data:
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

