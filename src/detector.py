"""テキスト検出モジュール: comic-text-detector のラッパー"""

import sys
from pathlib import Path
from typing import List, NamedTuple, Tuple, Optional
import logging

# comic-text-detector のパスを追加
COMIC_DETECTOR_PATH = Path(__file__).parent.parent / "vendor" / "comic-text-detector"
if COMIC_DETECTOR_PATH.exists():
    sys.path.insert(0, str(COMIC_DETECTOR_PATH))

try:
    from inference import TextDetector
    from utils.textmask import REFINEMASK_INPAINT
    import cv2
    import numpy as np
    HAS_COMIC_DETECTOR = True
except ImportError as e:
    HAS_COMIC_DETECTOR = False
    TextDetector = None
    REFINEMASK_INPAINT = None
    cv2 = None
    np = None

from PIL import Image

from .exceptions import ImageProcessingError

logger = logging.getLogger(__name__)

# グローバルなTextDetectorインスタンスのキャッシュ
_detector_cache: dict[str, TextDetector] = {}

# 警告ログの重複を防ぐためのフラグ
_comic_detector_warning_logged = False
_model_file_warning_logged = False
_model_file_warning_logged = False


class TextRegion(NamedTuple):
    """テキスト領域情報"""
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    image: Image.Image  # クロップされた画像
    reading_order: int  # 読み順（0始まり）


def detect_text_regions(
    image: Image.Image,
    model_path: Optional[str] = None,
    device: str = "auto"
) -> List[TextRegion]:
    """
    画像からテキスト領域を検出
    
    Args:
        image: PIL Imageオブジェクト
        model_path: comic-text-detector のモデルファイルパス
                    Noneの場合はデフォルトパスを試行
        device: 使用デバイス ("auto" | "mps" | "cpu" | "cuda")
    
    Returns:
        読み順でソートされたテキスト領域のリスト
    
    Raises:
        ImageProcessingError: 画像処理エラー
    """
    if not HAS_COMIC_DETECTOR:
        # comic-text-detectorが利用できない場合は、テキスト検出をスキップ
        global _comic_detector_warning_logged
        if not _comic_detector_warning_logged:
            logger.warning(
                "comic-text-detector が利用できません。"
                "テキスト検出をスキップします。"
                "テキスト検出の精度を上げるには、README.mdの手順に従って comic-text-detector をセットアップしてください。"
            )
            _comic_detector_warning_logged = True
        # 空のリストを返す（テキスト検出なし）
        return []
    
    try:
        # デバイスの決定
        if device == "auto":
            if hasattr(cv2, "cuda") and cv2.cuda.getCudaEnabledDeviceCount() > 0:
                device_str = "cuda"
            else:
                device_str = "cpu"
        elif device == "mps":
            # MPSはcomic-text-detectorでは直接サポートされていないため、CPUにフォールバック
            # 注意: これは正常な動作です。comic-text-detectorはPyTorchのMPSを直接使用できません
            # テキスト検出はCPUで実行されますが、OCR処理（manga-ocr）はMPSを使用します
            if not hasattr(sort_by_reading_order, '_mps_warning_logged'):
                logger.info(
                    "comic-text-detectorはMPSを直接サポートしていないため、"
                    "テキスト検出はCPUで実行されます。"
                    "OCR処理（manga-ocr）はMPSを使用します。"
                )
                sort_by_reading_order._mps_warning_logged = True
            device_str = "cpu"
        else:
            device_str = device
        
        # モデルパスの決定
        if model_path is None:
            # デフォルトのモデルパスを試行
            default_paths = [
                COMIC_DETECTOR_PATH / "data" / "comictextdetector.pt",
                COMIC_DETECTOR_PATH / "data" / "comictextdetector.pt.onnx",
                Path("vendor/comic-text-detector/data/comictextdetector.pt"),
                Path("vendor/comic-text-detector/data/comictextdetector.pt.onnx"),
            ]
            model_path = None
            for path in default_paths:
                if path.exists():
                    model_path = str(path)
                    break
            
            if model_path is None:
                global _model_file_warning_logged
                if not _model_file_warning_logged:
                    logger.warning(
                        "comic-text-detector のモデルファイルが見つかりません。"
                        "モデルファイルをダウンロードして配置してください。"
                        "詳細は README.md を参照してください。"
                        "テキスト検出をスキップします。"
                    )
                    _model_file_warning_logged = True
                # モデルファイルがない場合は、テキスト検出をスキップ
                return []
        
        # PIL Image を OpenCV 形式に変換
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # TextDetector の初期化（初回のみ、キャッシュを使用）
        cache_key = f"{model_path}:{device_str}"
        if cache_key not in _detector_cache:
            if logger.isEnabledFor(logging.INFO):
                logger.info(f"TextDetector を初期化中: {model_path} (device: {device_str})")
            _detector_cache[cache_key] = TextDetector(
                model_path=model_path,
                input_size=1024,
                device=device_str,
                act='leaky'
            )
        
        detector = _detector_cache[cache_key]
        
        # テキスト検出を実行
        mask, mask_refined, blk_list = detector(img_cv, refine_mode=REFINEMASK_INPAINT, keep_undetected_mask=False)
        
        # TextBlock から TextRegion に変換
        regions: List[TextRegion] = []
        for blk in blk_list:
            x1, y1, x2, y2 = blk.xyxy
            # バウンディングボックスが有効か確認
            if x2 > x1 and y2 > y1:
                # 領域をクロップ（後でcrop_text_regionsで処理）
                regions.append(
                    TextRegion(
                        bbox=(int(x1), int(y1), int(x2), int(y2)),
                        image=None,  # 後でクロップ
                        reading_order=0  # 後でソート
                    )
                )
        
        if not regions:
            # テキスト領域が検出されなかった場合は、空のリストを返す
            # ログは出力しない（大量の画像を処理する場合、ログが多すぎる）
            return []
        
        # 読み順でソート
        regions = sort_by_reading_order(regions)
        
        # 領域をクロップ
        regions = crop_text_regions(image, regions)
        
        return regions
        
    except Exception as e:
        logger.error(f"テキスト領域の検出に失敗しました: {e}", exc_info=True)
        raise ImageProcessingError(f"テキスト領域の検出に失敗しました: {e}")


def sort_by_reading_order(regions: List[TextRegion]) -> List[TextRegion]:
    """
    テキスト領域を漫画の読み順でソート
    
    漫画の一般的な読み順:
    - 右上から左下へ
    - 段組みを考慮（上段→下段、各段内で右→左）
    
    アルゴリズム:
    1. 領域をy座標でグループ化（閾値内のy座標差を同じ段とみなす）
    2. 各段内でx座標でソート（右から左、つまり-x座標でソート）
    3. 段をy座標でソート（上から下）
    
    Args:
        regions: テキスト領域のリスト
    
    Returns:
        ソートされたテキスト領域のリスト
    """
    if not regions:
        return []
    
    if len(regions) == 1:
        return [
            TextRegion(
                bbox=regions[0].bbox,
                image=regions[0].image,
                reading_order=0
            )
        ]
    
    # 各領域の右上座標（右端x、上端y）と高さを計算
    region_data = []
    for region in regions:
        x1, y1, x2, y2 = region.bbox
        right_x = x2  # 右端x座標
        top_y = y1    # 上端y座標（右上のy座標）
        height = y2 - y1
        region_data.append((region, right_x, top_y, height))
    
    # 画像の高さを取得（段の閾値計算用、右上のy座標を使用）
    max_y = max(ty for _, _, ty, _ in region_data)
    min_y = min(ty for _, _, ty, _ in region_data)
    image_height = max_y - min_y
    
    # 平均的な領域の高さを計算
    avg_height = sum(h for _, _, _, h in region_data) / len(region_data) if region_data else 50
    
    # 段の閾値: 平均的な領域の高さの60%以内を同じ段とみなす
    # 最小値として15ピクセル、最大値として画像高さの8%を保証
    row_threshold = max(15, min(avg_height * 0.6, image_height * 0.08))
    
    # 段（行）ごとにグループ化
    rows: List[List[Tuple[TextRegion, float, float]]] = []
    used = set()
    
    # 右上のy座標（上端）でソートして、上から順に処理
    for region, rx, ty, _ in sorted(region_data, key=lambda x: x[2]):  # 上端y座標でソート
        if id(region) in used:
            continue
        
        # 同じ段（右上のy座標が近い）の領域を探す
        row = [(region, rx, ty)]
        used.add(id(region))
        
        for other_region, other_rx, other_ty, _ in region_data:
            if id(other_region) in used:
                continue
            
            # 右上のy座標（上端）の差が閾値以内なら同じ段
            if abs(ty - other_ty) <= row_threshold:
                row.append((other_region, other_rx, other_ty))
                used.add(id(other_region))
        
        # 段内でソート: まず右端x座標（右から左）、同じなら上端y座標（上から下）
        # これにより、右上が最優先になる
        # 中心座標ではなく、右上座標（右端x、上端y）で評価
        row.sort(key=lambda x: (-x[0].bbox[2], x[0].bbox[1]))  # 右端x座標の降順、次に上端y座標の昇順
        rows.append(row)
    
    # 段を上から下にソート（各段の最小y座標=右上のy座標でソート）
    # 最小y座標（上端）を使うことで、段の上端で比較できる
    rows.sort(key=lambda row: min(ty for _, _, ty in row))
    
    # フラット化して読み順を設定
    result = []
    reading_order = 0
    for row in rows:
        for region, _, _ in row:
            result.append(
                TextRegion(
                    bbox=region.bbox,
                    image=region.image,
                    reading_order=reading_order
                )
            )
            reading_order += 1
    
    return result


def crop_text_regions(image: Image.Image, regions: List[TextRegion]) -> List[TextRegion]:
    """
    テキスト領域を画像からクロップ
    
    Args:
        image: 元の画像
        regions: テキスト領域のリスト（bbox情報のみ）
    
    Returns:
        クロップされた画像を含むテキスト領域のリスト
    """
    cropped_regions: List[TextRegion] = []
    
    for region in regions:
        x1, y1, x2, y2 = region.bbox
        
        # バウンディングボックスが画像範囲内か確認
        width, height = image.size
        x1 = max(0, min(x1, width))
        y1 = max(0, min(y1, height))
        x2 = max(0, min(x2, width))
        y2 = max(0, min(y2, height))
        
        if x2 <= x1 or y2 <= y1:
            logger.warning(f"無効なバウンディングボックスをスキップ: {region.bbox}")
            continue
        
        # 領域をクロップ
        try:
            cropped_image = image.crop((x1, y1, x2, y2))
            cropped_regions.append(
                TextRegion(
                    bbox=(x1, y1, x2, y2),
                    image=cropped_image,
                    reading_order=region.reading_order
                )
            )
        except Exception as e:
            logger.warning(f"領域のクロップに失敗: {region.bbox}, エラー: {e}")
            continue
    
    return cropped_regions

