"""出力生成モジュール: JSON形式とテキスト形式の出力"""

import json
from pathlib import Path
from typing import List
import logging

from .pipeline import PageResult

logger = logging.getLogger(__name__)


def generate_json_output(results: List[PageResult], output_path: Path) -> None:
    """
    JSON形式の出力ファイルを生成
    
    Args:
        results: ページごとのOCR結果
        output_path: 出力ファイルパス
    """
    output_data = []
    
    for result in results:
        # テキスト領域の詳細情報を構築
        text_regions = []
        texts = []
        
        # region_id（reading_order）でソートして、コマの読み順を保証
        sorted_ocr_results = sorted(result.ocr_results, key=lambda r: r.region.reading_order if r.region else 0)
        
        for ocr_result in sorted_ocr_results:
            if ocr_result.region is not None:
                x1, y1, x2, y2 = ocr_result.region.bbox
                text_regions.append({
                    "region_id": ocr_result.region.reading_order,
                    "bbox": [x1, y1, x2, y2],
                    "text": ocr_result.text,
                    "confidence": ocr_result.confidence
                })
            
            if ocr_result.text:
                texts.append(ocr_result.text)
        
        page_data = {
            "filename": result.filename,
            "page_number": result.page_number,
            "text_regions": text_regions,
            "texts": texts,
            "processing_time": round(result.processing_time, 2)
        }
        
        output_data.append(page_data)
    
    # JSONファイルに書き込み
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"JSON output saved to: {output_path}")


def generate_text_output(results: List[PageResult], output_path: Path) -> None:
    """
    テキスト形式の出力ファイルを生成
    
    Args:
        results: ページごとのOCR結果
        output_path: 出力ファイルパス
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in results:
            # ページヘッダー
            f.write(f"[{result.filename}]\n")
            
            # テキストを出力（読み順でソート済み）
            # region_id（reading_order）でソートして、コマの読み順を保証
            sorted_ocr_results = sorted(result.ocr_results, key=lambda r: r.region.reading_order if r.region else 0)
            for ocr_result in sorted_ocr_results:
                if ocr_result.text:
                    f.write(f"{ocr_result.text}\n")
            
            # ページ区切り（空行）
            f.write("\n")
    
    logger.info(f"Text output saved to: {output_path}")


def generate_outputs(
    results: List[PageResult],
    output_dir: Path,
    zip_filename: str,
    output_format: str = "both"
) -> List[Path]:
    """
    指定された形式で出力ファイルを生成
    
    Args:
        results: ページごとのOCR結果
        output_dir: 出力ディレクトリ
        zip_filename: Zipファイル名（拡張子なし）
        output_format: 出力形式 ("json" | "txt" | "both")
    
    Returns:
        生成された出力ファイルのパスのリスト
    """
    output_files: List[Path] = []
    
    if output_format in ("json", "both"):
        json_path = output_dir / f"{zip_filename}_output.json"
        generate_json_output(results, json_path)
        output_files.append(json_path)
    
    if output_format in ("txt", "both"):
        txt_path = output_dir / f"{zip_filename}_output.txt"
        generate_text_output(results, txt_path)
        output_files.append(txt_path)
    
    return output_files

