#!/usr/bin/env python3
"""セットアップヘルパースクリプト

このスクリプトは setup.sh の機能を Python で実装したものです。
以下の処理を行います:
1. comic-text-detector のサブモジュール初期化
2. モデルファイルのダウンロード
"""

import os
import sys
import subprocess
from pathlib import Path
import urllib.request
import shutil


def setup_submodule() -> bool:
    """
    comic-text-detector のサブモジュールをセットアップ
    
    Returns:
        成功した場合 True、失敗した場合 False
    """
    print("1. comic-text-detector のセットアップ...")
    
    vendor_dir = Path("vendor/comic-text-detector")
    
    if vendor_dir.exists() and (vendor_dir / ".git").exists():
        print("  ✓ comic-text-detector は既にセットアップされています")
        return True
    
    print("  git submodule を初期化しています...")
    try:
        subprocess.run(
            ["git", "submodule", "update", "--init", "--recursive"],
            check=True,
            capture_output=True,
            text=True
        )
        
        if vendor_dir.exists():
            print("  ✓ comic-text-detector のセットアップが完了しました")
            return True
        else:
            print("  ✗ comic-text-detector のセットアップに失敗しました", file=sys.stderr)
            print("  手動で以下を実行してください:", file=sys.stderr)
            print("    git submodule add https://github.com/dmMaze/comic-text-detector.git vendor/comic-text-detector", file=sys.stderr)
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"  ✗ git submodule の初期化に失敗: {e}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("  ✗ git コマンドが見つかりません", file=sys.stderr)
        return False


def download_model() -> bool:
    """
    モデルファイルをダウンロード
    
    Returns:
        成功した場合 True、失敗した場合 False
    """
    print("\n2. モデルファイルのダウンロード...")
    
    model_dir = Path("vendor/comic-text-detector/data")
    model_file = model_dir / "comictextdetector.pt"
    model_url = "https://github.com/zyddnys/manga-image-translator/releases/download/beta-0.3/comictextdetector.pt"
    
    if model_file.exists():
        file_size = model_file.stat().st_size / (1024 * 1024)  # MB
        print(f"  ✓ モデルファイルは既に存在します（サイズ: {file_size:.1f}MB）")
        print("  スキップします")
        return True
    
    print("  モデルファイルをダウンロードしています（約76MB）...")
    model_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # urllib を使用してダウンロード
        with urllib.request.urlopen(model_url) as response:
            with open(model_file, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        
        if model_file.exists():
            file_size = model_file.stat().st_size / (1024 * 1024)  # MB
            print(f"  ✓ モデルファイルのダウンロードが完了しました（サイズ: {file_size:.1f}MB）")
            return True
        else:
            print("  ✗ モデルファイルのダウンロードに失敗しました", file=sys.stderr)
            print(f"  手動でダウンロードしてください: {model_url}", file=sys.stderr)
            return False
            
    except Exception as e:
        print(f"  ✗ モデルファイルのダウンロードに失敗: {e}", file=sys.stderr)
        print(f"  手動でダウンロードしてください: {model_url}", file=sys.stderr)
        return False


def main() -> int:
    """
    メイン関数
    
    Returns:
        終了コード（0: 成功、1: エラー）
    """
    print("=== manga-ocr セットアップスクリプト ===\n")
    
    # カレントディレクトリをプロジェクトルートに変更
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    os.chdir(project_root)
    
    success = True
    
    # サブモジュールのセットアップ
    if not setup_submodule():
        success = False
    
    # モデルファイルのダウンロード
    if not download_model():
        success = False
    
    print("\n=== セットアップ完了 ===\n")
    
    if success:
        print("使用方法:")
        print("  manga-ocr <zipファイル>")
        print("\n例:")
        print("  manga-ocr comic.zip")
        return 0
    else:
        print("⚠️  一部のセットアップに失敗しました")
        print("上記のエラーメッセージを確認してください")
        return 1


if __name__ == "__main__":
    sys.exit(main())
