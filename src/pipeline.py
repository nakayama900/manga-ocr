"""パイプライン統合: 検出→OCRの連携"""

import time
from pathlib import Path
from typing import List, NamedTuple
import logging

from PIL import Image

from .detector import detect_text_regions, TextRegion
from .panel_detector import detect_panels, Panel
from .ocr import recognize_text, OCRResult
from .exceptions import ImageProcessingError
from .processor import ImageFile

logger = logging.getLogger(__name__)


class PageResult(NamedTuple):
    """ページ単位のOCR結果"""
    filename: str
    page_number: int
    regions: List[TextRegion]
    ocr_results: List[OCRResult]
    processing_time: float


def process_image(
    image_path: Path,
    page_number: int,
    device: str = "auto",
    skip_errors: bool = True,
    detector_model_path: str | None = None
) -> PageResult:
    """
    1つの画像を処理（検出→OCR）
    
    Args:
        image_path: 画像ファイルのパス
        page_number: ページ番号
        device: 使用デバイス ("auto" | "mps" | "cpu")
        skip_errors: エラー時にスキップするか
        detector_model_path: comic-text-detectorのモデルパス
    
    Returns:
        ページ単位のOCR結果
    
    Raises:
        ImageProcessingError: 画像処理エラー（skip_errors=Falseの場合）
    """
    start_time = time.time()
    filename = image_path.name
    
    try:
        # 画像を読み込み
        image = Image.open(image_path)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        logger.debug(f"Processing image: {filename}")
        
        # テキスト領域を検出
        regions = detect_text_regions(
            image,
            model_path=detector_model_path,
            device=device
        )
        logger.debug(f"Detected {len(regions)} text regions in {filename}")
        
        # コマを検出・グループ化
        panels: List[Panel] = []
        if regions:
            try:
                panels = detect_panels(regions)
                logger.debug(f"Detected {len(panels)} panels in {filename}")
            except Exception as e:
                if skip_errors:
                    logger.warning(f"Panel detection failed for {filename}: {e}, falling back to region-based sort.")
                    panels = [] # パネル検出失敗として扱う
                else:
                    raise ImageProcessingError(f"Panel detection failed for {filename}: {e}")

        # パネル検出が有効だったかを評価する
        use_panels = True
        if not panels:
            use_panels = False
        # パネルが1つにしかグループ化されなかった場合、DBSCANが機能しなかった可能性が高い
        elif len(panels) == 1:
            logger.debug("Panel detection resulted in a single panel, falling back to region-based sort.")
            use_panels = False
        # パネルが細分化されすぎている（領域の8割以上が個別のパネルになった）場合
        elif len(panels) > len(regions) * 0.8 and len(regions) > 2:
            logger.debug(f"Too many panels ({len(panels)}) for {len(regions)} regions, falling back to region-based sort.")
            use_panels = False

        # OCR処理
        ocr_results: List[OCRResult] = []
        final_regions: List[TextRegion] = []
        
        if use_panels:
            # --- パネル検出成功時の処理 ---
            logger.debug("Using panel-based reading order.")
            for panel in panels:
                for region_idx, region in enumerate(panel.text_regions):
                    try:
                        # コマの読み順を基準に、コマ内のテキスト領域の読み順を再設定
                        adjusted_reading_order = panel.reading_order * 1000 + region_idx
                        updated_region = TextRegion(
                            bbox=region.bbox, image=region.image, reading_order=adjusted_reading_order
                        )
                        ocr_result = recognize_text(updated_region.image, region=updated_region, device=device)
                        ocr_results.append(ocr_result)
                        final_regions.append(updated_region)
                    except Exception as e:
                        if skip_errors:
                            logger.warning(f"OCR failed for region in panel {panel.reading_order}: {e}")
                            adjusted_reading_order = panel.reading_order * 1000 + region_idx
                            error_region = TextRegion(bbox=region.bbox, image=region.image, reading_order=adjusted_reading_order)
                            ocr_results.append(OCRResult(text="", confidence=0.0, region=error_region))
                            final_regions.append(error_region)
                        else:
                            raise ImageProcessingError(f"OCR failed for region in panel {panel.reading_order}: {e}")
        else:
            # --- パネル検出失敗時のフォールバック処理 ---
            logger.debug("Using simple region-based reading order (fallback).")
            # detect_text_regions が返したソート順をそのまま使う
            for region in regions:
                 try:
                    ocr_result = recognize_text(region.image, region=region, device=device)
                    ocr_results.append(ocr_result)
                    final_regions.append(region)
                 except Exception as e:
                    if skip_errors:
                        logger.warning(f"OCR failed for region {region.reading_order}: {e}")
                        ocr_results.append(OCRResult(text="", confidence=0.0, region=region))
                        final_regions.append(region)
                    else:
                        raise ImageProcessingError(f"OCR failed for region {region.reading_order}: {e}")

        processing_time = time.time() - start_time
        
        return PageResult(
            filename=filename,
            page_number=page_number,
            regions=final_regions,
            ocr_results=ocr_results,
            processing_time=processing_time
        )
        
    except Exception as e:
        if skip_errors:
            logger.error(f"Failed to process {filename}: {e}", exc_info=True)
            # エラー時は空の結果を返す
            return PageResult(
                filename=filename,
                page_number=page_number,
                regions=[],
                ocr_results=[],
                processing_time=time.time() - start_time
            )
        else:
            raise


def process_images(
    image_files: List[ImageFile],
    device: str = "auto",
    skip_errors: bool = True,
    detector_model_path: str | None = None
) -> List[PageResult]:
    """
    複数の画像を処理（検出→OCR）
    
    Args:
        image_files: 画像ファイルのリスト
        device: 使用デバイス ("auto" | "mps" | "cpu")
        skip_errors: エラー時にスキップするか
        detector_model_path: comic-text-detectorのモデルパス
    
    Returns:
        ページ単位のOCR結果のリスト
    """
    results: List[PageResult] = []
    
    for image_file in image_files:
        try:
            result = process_image(
                image_file.path,
                image_file.index,
                device=device,
                skip_errors=skip_errors,
                detector_model_path=detector_model_path
            )
            results.append(result)
        except Exception as e:
            if skip_errors:
                logger.error(f"Failed to process {image_file.filename}: {e}", exc_info=True)
                # エラー時は空の結果を追加
                results.append(
                    PageResult(
                        filename=image_file.filename,
                        page_number=image_file.index,
                        regions=[],
                        ocr_results=[],
                        processing_time=0.0
                    )
                )
            else:
                raise
    
    return results

