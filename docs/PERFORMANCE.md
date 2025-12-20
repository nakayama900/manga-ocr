# パフォーマンスとデバイス使用について

## デバイス使用の概要

このツールは2つの主要な処理を行います：

1. **テキスト検出** (`comic-text-detector`)
2. **OCR処理** (`manga-ocr`)

それぞれが異なるデバイスを使用する可能性があります。使用されるデバイスは、お使いの環境（OS、GPU）によって自動的に選択されます。

## 対応デバイス

### Apple Silicon Mac (M1/M2/M3/M4)
- **OCR処理**: MPS（Metal Performance Shaders）を使用
- **テキスト検出**: CPUを使用（MPS非対応のため）

### Windows / Linux (NVIDIA GPU搭載)
- **OCR処理**: CUDAを使用（利用可能な場合）、またはCPU
- **テキスト検出**: CUDAを使用（利用可能な場合）、またはCPU

### Intel Mac / CPUのみの環境
- **OCR処理**: CPUを使用
- **テキスト検出**: CPUを使用

## GPUアクセラレーション技術

### MPS（Metal Performance Shaders）

**MPS（Metal Performance Shaders）** は、Appleが開発したGPUアクセラレーション技術です。Apple Silicon（M1、M2、M3、M4など）を搭載したMacで、機械学習や画像処理を高速化するために使用されます。

### CUDA

**CUDA** は、NVIDIAが開発したGPUアクセラレーション技術です。NVIDIA GPUを搭載したWindows/Linuxマシンで、機械学習や画像処理を高速化するために使用されます。

### なぜ速いのか？

1. **並列処理**: GPUは数千個の小さなコアを持ち、同時に多くの計算を実行できます
2. **専用ハードウェア**: 画像処理や行列計算に最適化された回路を持っています
3. **メモリ帯域**: CPUよりも高速なメモリアクセスが可能です

## デバイス使用の詳細

### テキスト検出（comic-text-detector）

**使用デバイス**: CPU（またはCUDA、利用可能な場合）

**理由**:
- `comic-text-detector` はPyTorchのMPS（Metal Performance Shaders）を直接サポートしていません
- このライブラリは主にCUDA（NVIDIA GPU）またはCPUでの実行を想定しています
- Apple SiliconのMPSは、PyTorch 1.12以降でサポートされていますが、`comic-text-detector`の実装ではMPSが明示的にサポートされていません

**影響**:
- テキスト検出処理はCPUで実行されます
- 処理速度はCPUの性能に依存します
- 通常、テキスト検出は比較的高速に完了します

### OCR処理（manga-ocr）

**使用デバイス**: 環境に応じて自動選択
- **Apple Silicon Mac**: MPS（自動検出）
- **Windows/Linux (NVIDIA GPU)**: CUDA（自動検出）
- **その他**: CPU

**理由**:
- `manga-ocr` はPyTorchベースで、利用可能なGPUを自動的に検出して使用します
- GPUが利用可能な場合、CPUよりも高速に推論が可能です

**影響**:
- GPUが利用可能な場合、OCR処理は高速に実行されます
- 大量のテキスト領域がある場合でも、GPUにより高速に処理できます

## パフォーマンス

### 処理時間の目安

一般的な処理時間の目安（218ページの例）:
- テキスト検出: 各画像数秒（CPU）
- OCR処理: 各領域0.5-2秒（MPS）

### パフォーマンス比較

| デバイス | OCR処理速度（1領域あたり） | 対応環境 |
|---------|------------------------|---------|
| CPU | 2-5秒 | すべての環境 |
| MPS | 0.5-2秒 | Apple Silicon Mac |
| CUDA | 0.5-2秒 | Windows/Linux (NVIDIA GPU) |

**GPU使用時は約2-4倍高速**になります！

## 確認方法

デバイス使用状況を確認するには：

```bash
python3 -m src.cli comic.zip --verbose
```

出力例（Apple Silicon Mac）：
```
使用デバイス: mps
comic-text-detectorはMPSを直接サポートしていないため、テキスト検出はCPUで実行されます。
OCR処理（manga-ocr）はMPSを使用します。
2025-12-20 12:30:23.957 | INFO | manga_ocr.ocr:__init__:25 - Using MPS
```

出力例（Windows/Linux with NVIDIA GPU）：
```
使用デバイス: cuda
OCR処理（manga-ocr）はCUDAを使用します。
```

「Using MPS」または「Using CUDA」と表示されていれば、GPUが使用されています。

## よくある質問

### Q: GPUは自動的に使用される？

A: はい。利用可能なGPU（MPS/CUDA）は自動的に検出され、使用されます。GPUが利用できない場合はCPUで実行されます。

### Q: MPSはすべてのMacで使える？

A: いいえ。Apple Silicon（M1/M2/M3/M4）を搭載したMacでのみ使用できます。Intel Macでは使用できません。

### Q: CUDAはどの環境で使える？

A: NVIDIA GPUを搭載したWindows/Linuxマシンで使用できます。CUDAドライバーとPyTorchのCUDA対応版が必要です。

### Q: GPUを使わないとどうなる？

A: CPUで処理されます。速度は遅くなりますが、結果は同じです。

### Q: 強制的にCPUを使いたい場合は？

A: `--device cpu` オプションを使用してください：
```bash
python3 -m src.cli comic.zip --device cpu
```

### Q: なぜテキスト検出だけCPUなのか？

A: `comic-text-detector`ライブラリがMPSを直接サポートしていないためです。これはライブラリの制限であり、ツール側で変更することはできません。

### Q: 処理速度に影響はあるか？

A: テキスト検出は比較的軽量な処理のため、CPUでも十分な速度で実行できます。OCR処理はMPSを使用するため、全体的なパフォーマンスは良好です。

### Q: CUDAは使用できるか？

A: NVIDIA GPUが利用可能な場合、`comic-text-detector`は自動的にCUDAを使用します。ただし、Apple Silicon MacではCUDAは利用できません。

## 参考リンク

より詳しい技術情報が必要な場合は、以下のドキュメントを参照してください：
- [PyTorch MPS ドキュメント](https://pytorch.org/docs/stable/notes/mps.html)
- [Apple Metal ドキュメント](https://developer.apple.com/metal/)
