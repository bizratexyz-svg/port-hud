# port-hud

[English](README.md) | **日本語**

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

ローカルでリッスンしている TCP ポートを確認・終了するための、軽量・外部依存ゼロの CLI ＆ サイバーパンク風フローティング HUD ツールです。

## 主な機能

- **CLI テーブルモード**: `lsof` を使ってリッスン中の TCP ポート（`Port`、`PID`、`Process`、`Address`）を一覧表示します。
- **インタラクティブ Kill**: 指定したポートにバインドされているプロセスをすばやく終了できます（`--kill <port>`）。
- **サイバーパンク・フローティング HUD**: ネオンシアン／ピンク配色のフレームレス・半透明・最前面表示 `tkinter` オーバーレイ（`--overlay`）。クリックで終了するボタン、ドラッグ移動、3 秒ごとの自動更新に対応しています。

## インストール

```bash
uv tool install .
```

または `uv` で直接実行できます:

```bash
uv run port-hud
```

## 使い方

```bash
# リッスン中の TCP ポートをテーブル表示
port-hud

# ポート 3000 のプロセスを対話的に終了
port-hud --kill 3000

# 確認なしで強制終了
port-hud --kill 3000 --force -y

# サイバーパンク・フローティング HUD を起動
port-hud --overlay
```

## 出力例

```text
$ port-hud
PORT  PID    PROCESS   ADDRESS
----  -----  --------  ---------
3000  12345  node      127.0.0.1
5432  4321   postgres  *
8000  9999   python3   [::1]
```

## 動作要件

- Python >= 3.11
- `lsof`（macOS および多くの Linux ディストリビューションにプリインストール済み）
- `tkinter`（`--overlay` モード使用時）

## ライセンス

MIT
