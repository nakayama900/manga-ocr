# System Design

## 技術スタック

### Core Stack
- **Language**: Python 3.10+
- **Hardware Acceleration**: PyTorch with MPS (Metal Performance Shaders)
- **CLI Framework**: `click` または標準ライブラリ `argparse`

### 主要依存ライブラリ
- **OCR Engine**: `manga-ocr`
- **Text Detection**: `comic-text-detector`
- **Image Processing**: `Pillow` (PIL)
- **Archive Processing**: `zipfile` (標準ライブラリ)
- **File Sorting**: `natsort`
- **Deep Learning Framework**: `torch`, `torchvision`

### 推奨追加ライブラリ
- **Logging**: `loguru` または標準 `logging`
- **Progress Bar**: `tqdm`（処理進捗表示）
- **Configuration**: `pydantic`（設定検証、オプション）

## アーキテクチャ概要

```
┌─────────────────────────────────────────┐
│         CLI Entry Point                 │
│    (main.py / __main__.py)              │
│  - コマンドライン引数解析                │
│  - デバイス検出（MPS優先）               │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      Zip Processor                      │
│  - Zipファイルの展開                     │
│  - 画像ファイルのフィルタリング          │
│  - 自然順ソート（natsort）               │
│  - 一時ディレクトリ管理                  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      Image Processing Pipeline          │
│  ┌──────────────────────────────┐      │
│  │  Text Detector                │      │
│  │  (comic-text-detector)        │      │
│  │  - テキスト領域検出            │      │
│  │  - 読み順ソート                │      │
│  │  - 領域のクロップ              │      │
│  └──────────────┬───────────────┘      │
│                 │                       │
│                 ▼                       │
│  ┌──────────────────────────────┐      │
│  │  OCR Engine                  │      │
│  │  (manga-ocr)                 │      │
│  │  - テキスト認識               │      │
│  │  - MPSデバイス使用            │      │
│  └──────────────┬───────────────┘      │
└─────────────────┼──────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      Output Generator                   │
│  - JSON形式生成                          │
│  - テキスト形式生成                      │
│  - 出力先ディレクトリ指定                │
└─────────────────────────────────────────┘
```

## プロジェクト構造

```
manga-ocr/
├── src/
│   ├── __init__.py
│   ├── cli.py              # CLI entry point (argparse/click)
│   ├── processor.py        # Zip processing & orchestration
│   ├── detector.py         # Text detection wrapper
│   ├── ocr.py              # OCR wrapper
│   ├── output.py           # Output generation (JSON/TXT)
│   └── utils.py            # Utilities (device detection, etc.)
├── tests/
│   ├── __init__.py
│   ├── test_processor.py
│   ├── test_detector.py
│   ├── test_ocr.py
│   └── test_output.py
├── docs/                   # SDD documents
│   ├── 00_CONTEXT/
│   ├── 10_SPEC/
│   └── 20_PLAN/
├── requirements.txt
├── setup.py / pyproject.toml
├── README.md
└── .cursorrules
```

## デバイス管理戦略

1. **デバイス検出**: `torch.backends.mps.is_available()` でMPS利用可能性を確認
2. **優先順位**: MPS > CPU（MPSが利用可能な場合は必ず使用）
3. **フォールバック**: MPSが利用不可の場合、CPUで処理を継続

## エラーハンドリング戦略

- **破損画像**: 個別の画像処理エラーはログに記録し、処理を継続
- **Zip展開エラー**: 致命的エラーとして処理を中断
- **モデル読み込みエラー**: 致命的エラーとして処理を中断
- **出力ファイル書き込みエラー**: 致命的エラーとして処理を中断

## パフォーマンス考慮事項

- **バッチ処理**: 可能であれば複数画像をバッチで処理（モデル依存）
- **メモリ管理**: 大きなZipファイルでもメモリ効率的に処理
- **進捗表示**: `tqdm`を使用して処理進捗を可視化
- **一時ファイル**: 処理完了後は必ずクリーンアップ

