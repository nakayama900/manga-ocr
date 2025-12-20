"""CLIエントリーポイント"""

import argparse
import sys
from pathlib import Path

from . import __version__
from .exceptions import MangaOCRError, ZipExtractionError, NoImagesFoundError
from .utils import get_device, get_output_path
from .processor import process_zip
from .pipeline import process_images
from .output import generate_outputs
from pathlib import Path
from tqdm import tqdm


def parse_args() -> argparse.Namespace:
    """
    コマンドライン引数を解析
    
    Returns:
        解析された引数
    """
    parser = argparse.ArgumentParser(
        description="Zipファイルで圧縮された漫画画像を一括でOCR処理するCLIツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s comic.zip
  %(prog)s comic.zip --output-format json
  %(prog)s comic.zip -o ./results --verbose
  %(prog)s comic.zip --device mps
        """.strip()
    )
    
    # 必須引数
    parser.add_argument(
        "zip_file",
        type=str,
        help="処理対象のZipファイルのパス"
    )
    
    # 出力関連オプション
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default=None,
        help="出力ディレクトリを指定（デフォルト: Zipファイルと同じディレクトリ）"
    )
    
    parser.add_argument(
        "--output-format", "-f",
        type=str,
        choices=["json", "txt", "both"],
        default="both",
        help="出力形式を指定（デフォルト: both）"
    )
    
    # 処理設定
    parser.add_argument(
        "--device",
        type=str,
        choices=["auto", "mps", "cpu"],
        default="auto",
        help="使用デバイスを指定（デフォルト: auto）"
    )
    
    parser.add_argument(
        "--temp-dir",
        type=str,
        default=None,
        help="一時ディレクトリを指定（デフォルト: システムの一時ディレクトリ）"
    )
    
    # 動作制御
    parser.add_argument(
        "--skip-errors",
        action="store_true",
        default=True,
        help="エラーが発生した画像をスキップして処理を継続（デフォルト: 有効）"
    )
    
    parser.add_argument(
        "--no-skip-errors",
        action="store_false",
        dest="skip_errors",
        help="エラー時に処理を中断"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="詳細ログを出力"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        default=False,
        help="エラー以外のログを抑制"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    """
    引数の妥当性を検証
    
    Args:
        args: 解析された引数
    
    Raises:
        SystemExit: 引数が無効な場合
    """
    zip_path = Path(args.zip_file)
    
    if not zip_path.exists():
        print(f"エラー: Zipファイルが見つかりません: {args.zip_file}", file=sys.stderr)
        sys.exit(1)
    
    if not zip_path.is_file():
        print(f"エラー: 指定されたパスはファイルではありません: {args.zip_file}", file=sys.stderr)
        sys.exit(1)
    
    if zip_path.suffix.lower() != ".zip":
        print(f"警告: ファイル拡張子が .zip ではありません: {args.zip_file}", file=sys.stderr)


def main() -> int:
    """
    CLIメイン関数
    
    Returns:
        終了コード（0: 成功、1: エラー）
    """
    try:
        args = parse_args()
        validate_args(args)
        
        # デバイス検出
        try:
            device = get_device(args.device)
            if args.verbose:
                print(f"使用デバイス: {device}")
        except RuntimeError as e:
            print(f"エラー: {e}", file=sys.stderr)
            return 1
        
        # Zipファイルの処理
        try:
            if args.verbose:
                print(f"Zipファイルを展開中: {args.zip_file}")
            
            # 一時ディレクトリを保持しながら処理
            from .processor import extract_zip
            
            with extract_zip(args.zip_file, args.temp_dir) as extracted_dir:
                from .processor import get_image_files
                
                image_files = get_image_files(extracted_dir)
                
                if not args.quiet:
                    print(f"画像ファイルを {len(image_files)} 個見つけました")
                
                if args.verbose:
                    print("見つかった画像ファイル:")
                    for img in image_files[:10]:  # 最初の10個のみ表示
                        print(f"  [{img.index}] {img.filename}")
                    if len(image_files) > 10:
                        print(f"  ... 他 {len(image_files) - 10} 個")
                
                # OCR処理を実行
                if not args.quiet:
                    print(f"\n処理を開始します（デバイス: {device}）...")
                
                # 進捗バーを表示
                if not args.quiet:
                    image_files_iter = tqdm(image_files, desc="処理中", unit="画像")
                else:
                    image_files_iter = image_files
                
                # パイプライン処理（一時ディレクトリが有効な間）
                results = process_images(
                    image_files,
                    device=device,
                    skip_errors=args.skip_errors,
                    detector_model_path=None  # デフォルトパスを使用
                )
                
                if not args.quiet:
                    print(f"\n処理完了: {len(results)} ページを処理しました")
                
                # 出力ファイルの生成
                zip_path = Path(args.zip_file)
                zip_stem = zip_path.stem
                
                output_dir = Path(args.output_dir) if args.output_dir else zip_path.parent
                output_dir.mkdir(parents=True, exist_ok=True)
                
                output_files = generate_outputs(
                    results,
                    output_dir,
                    zip_stem,
                    args.output_format
                )
                
                if not args.quiet:
                    print("\n出力ファイル:")
                    for output_file in output_files:
                        print(f"  - {output_file}")
                
                if args.verbose:
                    total_time = sum(r.processing_time for r in results)
                    print(f"\n総処理時間: {total_time:.2f}秒")
                    print(f"平均処理時間: {total_time/len(results):.2f}秒/ページ")
            
            return 0
            
        except ZipExtractionError as e:
            print(f"エラー: {e}", file=sys.stderr)
            return 1
        except NoImagesFoundError as e:
            print(f"エラー: {e}", file=sys.stderr)
            return 1
        
    except KeyboardInterrupt:
        print("\n処理が中断されました", file=sys.stderr)
        return 130
    except MangaOCRError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"予期しないエラー: {e}", file=sys.stderr)
        if args.verbose if 'args' in locals() else False:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

