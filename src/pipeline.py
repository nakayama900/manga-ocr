"""パイプライン統合: 検出→OCRの連携"""

import time
from pathlib import Path
from typing import List, NamedTuple
import logging

from PIL import Image

from .detector import detect_text_regions, TextRegion
from .ocr import recognize_text_regions, OCRResult
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
        try:
            regions = detect_text_regions(
                image,
                model_path=detector_model_path,
                device=device
            )
            logger.debug(f"Detected {len(regions)} text regions in {filename}")
        except Exception as e:
            if skip_errors:
                logger.warning(f"Text detection failed for {filename}: {e}")
                regions = []
            else:
                raise ImageProcessingError(f"Text detection failed for {filename}: {e}")
        
        # OCRを実行
        ocr_results: List[OCRResult] = []
        if regions:
            try:
                ocr_results = recognize_text_regions(regions, device=device)
                logger.debug(f"OCR completed for {len(ocr_results)} regions in {filename}")
            except Exception as e:
                if skip_errors:
                    logger.warning(f"OCR failed for {filename}: {e}")
                    # 空の結果を追加
                    ocr_results = [
                        OCRResult(text="", confidence=0.0, region=region)
                        for region in regions
                    ]
                else:
                    raise ImageProcessingError(f"OCR failed for {filename}: {e}")
        
        processing_time = time.time() - start_time
        
        return PageResult(
            filename=filename,
            page_number=page_number,
            regions=regions,
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

