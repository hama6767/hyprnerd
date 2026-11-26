# hyprnerd

[![CI](https://github.com/hama6767/hyprnerd/actions/workflows/ci.yml/badge.svg)](https://github.com/hama6767/hyprnerd/actions/workflows/ci.yml)

JaKooLit v2.3.17 の見た目を Hyprland 0.57.x の Lua 設定へ移植した dotfiles です（Ubuntu 24.04 / 26.04・Arch Linux x86_64 向け）。壁紙・テーマ・フォントを同梱し、外部ツールのバージョンとハッシュを `dependencies.lock.json` で固定しています。

> OS や Hyprland 本体のインストーラではありません。既存の **Hyprland 0.57.x** 環境に適用してください。

![Desktop preview](docs/preview.png)
![Desktop demo](docs/demo.gif)

## セットアップ

```bash
git clone [https://github.com/hama6767/hyprnerd.git](https://github.com/hama6767/hyprnerd.git) && cd hyprnerd
```

### 1. 基本ツール・日本語入力の導入（任意）

```bash
python3 bootstrap.py --check
python3 bootstrap.py --apply
python3 scripts/check-foundation.py
```

- **導入対象**: Neovim 0.12.6（LazyVim）, lazygit 0.66.3, LazyDon 0.1.4, Atuin 18.25.1, superfile (`spf`) 1.6.1, tree-sitter, ripgrep, fd, Fcitx5 + Mozc, 日本語フォント
- バイナリは `~/.local/opt/hyprnerd-tools/` に配置し、`~/.local/bin/` へリンクします（`EDITOR`/`VISUAL` は `nvim`、`spf` 終了時は移動先へ `cd`）。
- パッケージ導入に `sudo` を使用します（Arch は `pacman -Syu`）。不要な場合は `--skip-packages` を付けてください。
- その他のオプション: `--skip-plugins`（Neovim プラグイン取得を延期）、`--no-session`（Fcitx5 を自動起動しない）。
- 既存の設定・Atuin DB は `~/.local/state/hyprnerd/bootstrap-backups/<日時>/` に退避し、既存の LazyVim 独自設定や Atuin 履歴は維持します。反映にはシェル再起動か `source ~/.config/shell/hyprnerd-tools.sh` が必要です。

### 2. デスクトップ設定の適用

Hyprland セッション上から実行します（`sudo` 不要）。

```bash
# 任意: 公式 Kitty（x86_64） / Ubuntu 24.04 向け Qt5/Qt6 プラグインをユーザー領域へ導入
python3 scripts/install-kitty.py
python3 scripts/install-qt-plugins.py

# 汎用 PC（既存の入力・モニター設定を引き継ぐ）
python3 install.py --profile generic --check
python3 install.py --profile generic --apply

# 専用機（NVIDIA / ee,us / HDMI-A-1）※別 PC では使用しない
python3 install.py --profile ubuntu-desktop --check
python3 install.py --profile ubuntu-desktop --apply
```

- `--check` は差分表示のみ。`--apply` は `~/.local/state/kool-dotfiles/backups/<日時>/` へ退避後、構文検証して即時反映します。
- `generic` で既存設定の形式が合わない場合は、先に `home/.config/hypr/UserConfigs/user_settings.lua` と `monitors.lua` を編集してください。

### 復元

適用時に表示される `BACKUP:` パスを指定して元に戻せます。

```bash
python3 install.py --restore ~/.local/state/kool-dotfiles/backups/<日時> --check
python3 install.py --restore ~/.local/state/kool-dotfiles/backups/<日時>
```

### 旧 Hyprland からの移行（Arch）

稼働中の旧セッションへ Lua 設定を読み込ませず、次回ログインから切り替えます。

```bash
python3 scripts/prepare-legacy-session.py --apply
python3 install.py --profile arch-laptop --apply --no-reload --keep-legacy-session
```

`arch-laptop` は参照機（Intel / eDP-1 / Estonian キーボード）用です。別 PC では `generic` を指定してください。旧設定は `~/.local/state/hyprnerd/legacy-sessions/` に退避されます（カーネル更新後は再起動が必要）。

## 主な操作

| 操作 | キー／マウス |
|---|---|
| ターミナルを開く | `Super+Enter` |
| ウィンドウ／空モニターのフォーカス移動 | `Super+←/→/↑/↓` / `Super+H/J/K/L` |
| ウィンドウ移動（画面端で隣モニターへ） | `Super+Shift+←/→/↑/↓` |
| ウィンドウのリサイズ | `Super+Alt+←/→/↑/↓` |
| タイル／自由配置の全体切替 | `Super+Alt+Space` / バーの `Tile`・`Window` |
| 現在のウィンドウのみ浮動切替 | `Super+Space` |
| マウスで移動／リサイズ | `Super+左ドラッグ` / `Super+右ドラッグ` |
| 前／次のワークスペース（全モニター連動） | `Super+Ctrl+←/→`, `Super+Shift+Tab` / `Super+Tab`, バー中央スクロール |
| 番号でワークスペース切替（1〜10） | `Super+1…0` |
| ワークスペースへ移動（追従／移動のみ） | `Super+Shift+1…0` / `Super+Ctrl+1…0` |
| 前／次のワークスペースへ移動（追従） | `Super+Shift+[` / `Super+Shift+]` |
| ワークスペースを追加 | `Super+Ctrl+N` / バー中央の `+` |
| ワークスペース一覧から選択／移動 | バー中央の番号を左／右クリック |
| モニター配置の編集 | `Super+Alt+D` / `nwg-displays` |
| 日本語入力切替 | `Ctrl+Space` |
| Dock の有効／無効切替 | `Ctrl+Alt+D`（画面下端中央で自動表示） |
| 壁紙を一時的に黒くする／戻す | `Super+Shift+M` |
| ウィンドウを閉じる | `Super+Q` |
| ヘルプ／全キーバインド検索 | `Super+Shift+H` / `Super+Shift+K` |

- **ブラウザー終了確認**: Firefox / Chromium 系は 1 回目の `Super+Q` で確認を表示し、4 秒以内にもう一度押すと閉じます。
- **フォーカス挙動**: マウス移動だけではフォーカスが移りません（クリックで切替）。キーボード移動時はカーソルも追従します。
- **上部バー**: 中央にモニターラベル（`A / B / C`）とワークスペース別のアプリアイコンを表示します。
- **モニター設定**: `nwg-displays` で Apply すると構成ごとに保存され、既存の `monitors.lua` は `.before-nwg-<日時>` へ退避されます。

## 依存関係

- **必須**: Hyprland `0.57.x`, Python 3, Kitty（`0.51.1` 検証済）, `nwg-dock-hyprland` `0.4.11`, Waybar（`0.16.0` 検証済）, Rofi, SwayNotificationCenter, `jq`, `gsettings`, `fontconfig`, `awww`, Kvantum（Qt5/Qt6）
  - Ubuntu で `install-qt-plugins.py` を使う場合は Qt5.15 / Qt6.4, QtSvg, KF5WindowSystem, Qt5X11Extras が必要です。
  - `nwg-dock-hyprland` はパッケージまたは [v0.4.11](https://github.com/nwg-piotr/nwg-dock-hyprland/tree/v0.4.11) からビルドして PATH に配置してください。
- **任意**: `wallust`, `fastfetch`, `hyprlock`, `grim`, `slurp`, `cliphist`, `Quickshell` など（全パッケージ一覧: `docs/installed-packages.tsv`）。

## 構成

```text
home/               dotfiles 本体・壁紙・フォント・テーマ・アイコン
foundation/         LazyVim 最小構成・日本語入力の初期設定
bootstrap.py        基本ツール・Atuin・Mozc の導入
hosts/              ホスト固有設定（NVIDIA 環境変数など）
reference-palette/  参照壁紙一致時に使う固定配色
scripts/            導入・検証・CI・パッケージング用スクリプト
```

<details>
<summary>見た目・テーマ設定の詳細</summary>

| 項目 | 値 |
|---|---|
| 壁紙 | `wall_anime_4K.png`（ハッシュ一致時は固定配色、変更時は Wallust 生成） |
| バー・Dock | 上部 Waybar 30px / 下部自動非表示 Dock 40px |
| 基本色 | 背景 `#191919` / 文字 `#FCF6F3` / 枠 `#72C8C8` / 非アクティブ `#18615F` / アクセント `#FDB417` |
| ウィンドウ | 枠 2px / 角丸 10px / gaps in 6px・out 8px / blur 6×2 / shadow 3・power 1 |
| 透過率 | 共通 `1.0 / 0.9`・Firefox `0.9 / 0.7`・Kitty `0.8 / 0.7`（背景 `0.9`） |
| フォント | Kitty: Noto Sans Mono 12pt / バー・Rofi: JetBrainsMono Nerd Font |
| GTK / Qt | Kali-Dark + Flat-Remix-Blue-Dark / Kvantum `catppuccin-mocha-blue` + Fira Code |

詳細ルールは `home/.config/hypr/UserConfigs/user_window_rules.lua` および `user_desktop.lua` を参照してください。

</details>

## 検証・リリース

Push / PR ごとに GitHub Actions で構文・ハッシュ・適用／復元テストを実行します。`v*` タグの push で GitHub Release を自動作成します。

```bash
python3 scripts/validate.py               # 実環境チェック（docs/validation.json）
python3 scripts/ci.py                     # CI 検証一式
python3 -m unittest discover -s tests -v  # ユニットテスト
python3 scripts/package.py --version 0.2.0
```

## ライセンス・出典

- **コード・設定**: GPL-3.0-or-later（`LICENSE`）。ベース: [LinuxBeginnings/Hyprland-Dots](https://github.com/LinuxBeginnings/Hyprland-Dots/tree/170b69b846b1cd92ebc6d81c17393e17bed8d416)（v2.3.28.3） / [JaKooLit/Hyprland-Dots](https://github.com/JaKooLit/Hyprland-Dots)
- **サードパーティ資材**: 各フォント・テーマ・壁紙は元のライセンスに従います（`THIRD_PARTY.md`, `licenses/`）。
