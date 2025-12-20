#!/bin/bash
# manga-ocr セットアップスクリプト

set -e  # エラー時に終了

echo "=== manga-ocr セットアップスクリプト ==="
echo ""

# 1. comic-text-detectorのセットアップ（git submodule）
echo "1. comic-text-detector のセットアップ..."
if [ ! -d "vendor/comic-text-detector" ]; then
    echo "  git submodule を初期化しています..."
    git submodule update --init --recursive
    if [ -d "vendor/comic-text-detector" ]; then
        echo "  ✓ comic-text-detector のセットアップが完了しました"
    else
        echo "  ✗ comic-text-detector のセットアップに失敗しました"
        echo "  手動で以下を実行してください:"
        echo "    git submodule add https://github.com/dmMaze/comic-text-detector.git vendor/comic-text-detector"
        exit 1
    fi
else
    echo "  ✓ comic-text-detector は既にセットアップされています"
fi
echo ""

# 2. モデルファイルのダウンロード
echo "2. モデルファイルのダウンロード..."
MODEL_DIR="vendor/comic-text-detector/data"
MODEL_FILE="$MODEL_DIR/comictextdetector.pt"
MODEL_URL="https://github.com/zyddnys/manga-image-translator/releases/download/beta-0.3/comictextdetector.pt"

if [ -f "$MODEL_FILE" ]; then
    file_size=$(ls -lh "$MODEL_FILE" | awk '{print $5}')
    echo "  ✓ モデルファイルは既に存在します（サイズ: $file_size）"
    echo "  スキップします"
else
    echo "  モデルファイルをダウンロードしています（約76MB）..."
    mkdir -p "$MODEL_DIR"
    
    if command -v curl &> /dev/null; then
        curl -L -o "$MODEL_FILE" "$MODEL_URL"
    elif command -v wget &> /dev/null; then
        wget -O "$MODEL_FILE" "$MODEL_URL"
    else
        echo "  ✗ curl または wget が見つかりません"
        echo "  手動でモデルファイルをダウンロードしてください:"
        echo "    $MODEL_URL"
        exit 1
    fi
    
    if [ -f "$MODEL_FILE" ]; then
        file_size=$(ls -lh "$MODEL_FILE" | awk '{print $5}')
        echo "  ✓ モデルファイルのダウンロードが完了しました（サイズ: $file_size）"
    else
        echo "  ✗ モデルファイルのダウンロードに失敗しました"
        echo "  手動でダウンロードしてください:"
        echo "    $MODEL_URL"
        exit 1
    fi
fi
echo ""

# 3. 仮想環境の作成（オプション）
echo "3. 仮想環境のセットアップ（オプション）..."
if [ ! -d "venv" ]; then
    read -p "  仮想環境を作成しますか？ (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "  仮想環境を作成しています..."
        python3 -m venv venv
        echo "  ✓ 仮想環境が作成されました"
        echo "  有効化するには以下を実行してください:"
        echo "    source venv/bin/activate"
    else
        echo "  仮想環境の作成をスキップしました"
    fi
else
    echo "  ✓ 仮想環境は既に存在します"
fi
echo ""

# 4. 依存関係のインストール
echo "4. 依存関係のインストール..."
if [ -d "venv" ]; then
    echo "  仮想環境を使用してインストールします..."
    source venv/bin/activate
    pip install -r requirements.txt
    pip install -e .
else
    echo "  システムのPythonを使用してインストールします..."
    pip install -r requirements.txt
    pip install -e .
fi
echo "  ✓ 依存関係のインストールが完了しました"
echo ""

echo "=== セットアップ完了 ==="
echo ""
echo "使用方法:"
echo "  manga-ocr <zipファイル>"
echo ""
echo "例:"
echo "  manga-ocr comic.zip"
echo ""

