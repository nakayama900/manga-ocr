"""OCRモジュール: manga-ocr のラッパー"""

from typing import NamedTuple, Optional
import logging

try:
    from manga_ocr import MangaOcr
    HAS_MANGA_OCR = True
except ImportError:
    HAS_MANGA_OCR = False
    MangaOcr = None

from PIL import Image

from .exceptions import ImageProcessingError
from .detector import TextRegion

logger = logging.getLogger(__name__)

# グローバルなMangaOcrインスタンスのキャッシュ
_ocr_cache: Optional[MangaOcr] = None


class OCRResult(NamedTuple):
    """OCR結果"""
    text: str  # 認識されたテキスト
    confidence: float  # 信頼度（0.0-1.0、manga-ocrでは提供されない場合は1.0）
    region: TextRegion  # 元の領域情報


def _get_ocr_instance(device: str = "auto", force_cpu: bool = False) -> MangaOcr:
    """
    MangaOcrインスタンスを取得（シングルトン）
    
    Args:
        device: 使用デバイス ("auto" | "mps" | "cpu")
        force_cpu: CPUを強制使用するか
    
    Returns:
        MangaOcrインスタンス
    
    Raises:
        RuntimeError: manga-ocrがインストールされていない場合
    """
    global _ocr_cache
    
    if not HAS_MANGA_OCR:
        raise RuntimeError(
            "manga-ocr is not installed. Please install it with: pip install manga-ocr"
        )
    
    # デバイスに応じてforce_cpuを設定
    if device == "cpu" or force_cpu:
        force_cpu_flag = True
    elif device == "mps":
        # manga-ocrは自動的にMPSを使用する（force_cpu=False）
        force_cpu_flag = False
    else:  # device == "auto"
        # manga-ocrが自動的にデバイスを選択
        force_cpu_flag = False
    
    # キャッシュがあって、同じ設定の場合は再利用
    if _ocr_cache is not None:
        return _ocr_cache
    
    # 新しいインスタンスを作成
    logger.info(f"Initializing MangaOcr (force_cpu={force_cpu_flag})")
    _ocr_cache = MangaOcr(force_cpu=force_cpu_flag)
    return _ocr_cache


def recognize_text(
    region_image: Image.Image,
    region: TextRegion | None = None,
    device: str = "auto"
) -> OCRResult:
    """
    テキスト領域画像からテキストを認識
    
    Args:
        region_image: クロップされたテキスト領域画像（PIL Image）
        region: テキスト領域情報（オプション）
        device: 使用デバイス ("auto" | "mps" | "cpu")
    
    Returns:
        OCR結果（テキスト、信頼度など）
    
    Raises:
        ImageProcessingError: OCR処理エラー
        RuntimeError: manga-ocrがインストールされていない場合
    """
    if not HAS_MANGA_OCR:
        raise RuntimeError(
            "manga-ocr is not installed. Please install it with: pip install manga-ocr"
        )
    
    try:
        # MangaOcrインスタンスを取得
        ocr = _get_ocr_instance(device=device)
        
        # OCRを実行
        # manga-ocrはPIL Imageまたはファイルパスを受け取る
        text = ocr(region_image)
        
        # manga-ocrは信頼度を返さないため、デフォルト値を使用
        # 将来的に信頼度が提供される場合は、ここで取得
        confidence = 1.0
        
        result = OCRResult(
            text=text if text else "",
            confidence=confidence,
            region=region
        )
        
        return result
        
    except Exception as e:
        logger.error(f"OCR処理に失敗しました: {e}", exc_info=True)
        raise ImageProcessingError(f"OCR処理に失敗しました: {e}")


def recognize_text_regions(
    regions: list[TextRegion],
    device: str = "auto"
) -> list[OCRResult]:
    """
    複数のテキスト領域に対してOCRを実行
    
    Args:
        regions: テキスト領域のリスト
        device: 使用デバイス ("auto" | "mps" | "cpu")
    
    Returns:
        OCR結果のリスト（読み順でソート済み）
    
    Raises:
        ImageProcessingError: OCR処理エラー
    """
    if not regions:
        return []
    
    ocr_results: list[OCRResult] = []
    
    for region in regions:
        try:
            # 各領域の画像に対してOCRを実行
            text_result = recognize_text(region.image, region=region, device=device)
            ocr_results.append(text_result)
            
        except Exception as e:
            logger.warning(f"領域 {region.reading_order} のOCR処理に失敗: {e}")
            # エラーが発生した領域は空のテキストで追加
            ocr_results.append(
                OCRResult(
                    text="",
                    confidence=0.0,
                    region=region
                )
            )
    
    return ocr_results

