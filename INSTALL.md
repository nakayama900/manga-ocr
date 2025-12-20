# インストールガイド

## 基本的な依存ライブラリ

```bash
pip install -r requirements.txt
```

## comic-text-detector のインストール

`comic-text-detector` は既に `vendor/comic-text-detector` ディレクトリにクローンされています。

### モデルのダウンロード

`comic-text-detector` を使用するには、事前にトレーニングされたモデルファイルが必要です。

1. 以下のリンクからモデルファイルをダウンロードしてください：
   - [manga-image-translator リリースページ](https://github.com/zyddnys/manga-image-translator/releases/tag/beta-0.2.1)
   - [Google Drive](https://drive.google.com/drive/folders/1cTsXP5NYTCjhPVxwScdhxqJleHuIOyXG?usp=sharing)

2. ダウンロードしたモデルファイル（`comictextdetector.pt` または `comictextdetector.pt.onnx`）を以下のいずれかの場所に配置してください：
   - `vendor/comic-text-detector/data/comictextdetector.pt`
   - `vendor/comic-text-detector/data/comictextdetector.pt.onnx`

3. または、`--model-path` オプション（将来実装予定）でモデルファイルのパスを指定できます。

### 注意事項

- モデルファイルが配置されていない場合、テキスト検出機能は使用できません（フォールバックとして画像全体を1つの領域として扱います）
- モデルファイルは約100MB以上のサイズがあります

## 動作確認

インストールが完了したら、以下のコマンドで動作確認できます：

```bash
python3 -m src.cli --help
```

