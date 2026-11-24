# hyprnerd

[![CI](https://github.com/hama6767/hyprnerd/actions/workflows/ci.yml/badge.svg)](https://github.com/hama6767/hyprnerd/actions/workflows/ci.yml)

Arch 環境（JaKooLit v2.3.17）の見た目を Ubuntu 24.04 / Hyprland 0.57.2 の Lua 設定へ再現した dotfiles です。

![Desktop preview](docs/preview.png)
![Desktop demo](docs/demo.gif)

- **再現性重視**: 壁紙・配色・フォント・GTK/Qt テーマを `home/` に同梱し、バージョンとハッシュを `dependencies.lock.json` で固定
- **バックアップ**: デスクトップ設定は `sudo` 不要。基本道具のパッケージ導入にはsudoを使用し、既存設定やAtuin履歴を退避・保持
- **対象外**: OS や Hyprland 本体のインストーラではありません（既存の Hyprland 0.57.x 環境向け）

## 基本道具の自動インストール

Ubuntu 24.04 / 26.04 と Arch Linux（x86_64）では、リポジトリ取得後に次を実行します。

```bash
python3 bootstrap.py --check
python3 bootstrap.py --apply
```

Neovim 0.12.6、LazyVim、lazygit 0.66.3、LazyDon 0.1.4、Atuin 18.25.1、tree-sitter、ripgrep、fdを導入します。公式リリースのURLとSHA-256、LazyVimのプラグインコミットを固定しています。実行ファイルは `~/.local/opt/hyprnerd-tools/` に配置し、`~/.local/bin/` へリンクします。Neovimは相対行番号を標準にし、現在行は絶対行番号を表示します。

Fcitx5 + Mozcと日本語フォントもパッケージから導入し、`Ctrl+Space` で日本語入力を切り替えます。既存のキーボードグループとGTKテーマは維持します。Hyprland 0.57用の起動処理とキー割り当てはデスクトップ設定に含みます。入力方式を読み込んでいない既存アプリは再起動してください。

Bash起動時のFastfetch／Neofetchは実行しません。AtuinはBashと既存のZsh設定へ組み込みますが、アカウント登録やクラウド同期の新規設定はしません。既存のAtuin設定・履歴、LazyDonのアカウントはリポジトリに含めません。Atuinの既存DBは更新前にSQLiteのオンラインバックアップを取ります。

既存のLazyVimは独自プラグインと設定を保持し、相対行番号だけ追加します。他のNeovim設定は退避してから同梱の最小構成を配置します。変更前の設定・リンク・DBは `~/.local/state/hyprnerd/bootstrap-backups/日時/` に保存します。必要なパッケージが導入済みなら `--skip-packages`、プラグイン取得を次回起動まで遅らせるなら `--skip-plugins`、GUIの入力エンジンを起動しないなら `--no-session` を付けます。`--check` は読み取り専用です。

パッケージ導入にはsudoが必要です。Archでは部分更新を避けるため、パッケージ処理に `pacman -Syu` を使います。既存OSを更新したくない場合は依存を確認して `--skip-packages` を使用してください。基本道具の導入はHyprlandのバージョンを変更しません。デスクトップの全設定は引き続き **Hyprland 0.57.x** が必要で、0.52などの稼働中セッションへLua設定を読み込ませません。

```bash
python3 scripts/check-foundation.py
# 続いて、既存のHyprland 0.57セッションへ下記のデスクトップ設定を適用
```

## セットアップ / 再適用

リポジトリを取得し、Hyprland セッション上から実行します。

```bash
git clone https://github.com/hama6767/hyprnerd.git && cd hyprnerd

# 任意: 公式 Kitty（x86_64）および Ubuntu 24.04 向け Qt5/Qt6 プラグインをユーザー領域へ導入
python3 scripts/install-kitty.py
python3 scripts/install-qt-plugins.py

# 汎用 PC（既存の入力・モニター設定を引き継ぐ）
python3 install.py --profile generic --check
python3 install.py --profile generic --apply

# 専用デスクトップ（NVIDIA / ee,us / HDMI-A-1）※別 PC には使用しないこと
python3 install.py --profile ubuntu-desktop --check
python3 install.py --profile ubuntu-desktop --apply
```

- `--check` は差分表示のみ。`--apply` は `~/.local/state/kool-dotfiles/backups/<日時>/` へ退避後、構文検証してログアウトせずに即時反映します。
- `generic` で既存設定の形式が異なる場合は、先に `home/.config/hypr/UserConfigs/user_settings.lua` と `monitors.lua` を編集してください。

### 旧Hyprlandからの移行

Archの古いセッションを更新する場合は、OS全体の更新と必要なデスクトップ依存の導入後、設定を退避してから適用します。稼働中の旧セッションへ新しいLua設定は読み込ませません。

```bash
python3 scripts/prepare-legacy-session.py --apply
python3 install.py --profile arch-laptop --apply --no-reload --keep-legacy-session
```

`arch-laptop` は参照機のIntel / eDP-1 / Estonianキーボード用です。別PCでは `generic` とそのPCの入力・モニター設定を使用してください。旧設定は `~/.local/state/hyprnerd/legacy-sessions/` に保持し、互換用 `hyprland.conf` を残します。次回ログインからHyprland 0.57が `hyprland.lua` を使用します。カーネル更新後は再起動が必要です。

## 主な操作

上部 Waybar の `Tile` / `Window` で全体のタイル／自由配置を切り替えられます（再起動後も保持）。ワークスペースは全モニター連動で切り替わり、画面下端中央へのカーソル移動で自動非表示 Dock が現れます。

| 操作 | キー／マウス |
|---|---|
| ターミナルを開く（共有プロセス再利用） | `Super+Enter` |
| 全体のタイル／自由配置を切り替え | `Super+Alt+Space` / バーの `Tile`・`Window` |
| 現在のウィンドウのみ浮動切り替え | `Super+Space` |
| ウィンドウの移動／サイズ変更 | `Super+左ドラッグ` / `Super+右ドラッグ` |
| 前／次のデスクトップ（全モニター） | `Super+Ctrl+←/→`、`Super+Shift+Tab` / `Super+Tab`、バー中央スクロール |
| 番号で切り替え（1〜10） | `Super+1…0` |
| ウィンドウを移動（追従／移動のみ） | `Super+Shift+1…0` / `Super+Ctrl+1…0` |
| 前／次へウィンドウを移動（追従） | `Super+Shift+[` / `Super+Shift+]` |
| デスクトップを追加 | `Super+Ctrl+N` / バー中央の `+` |
| 一覧から選択／ウィンドウ移動 | バー中央の番号を左／右クリック |
| 日本語入力を切り替え | `Ctrl+Space` |
| Dock の有効／無効を切り替え | `Ctrl+Alt+D` |

## 復元

適用時に表示される `BACKUP:` パスを指定すると、設定ファイル・シンボリックリンク・GTK GSettings を元に戻せます。

```bash
python3 install.py --restore ~/.local/state/kool-dotfiles/backups/<日時> --check
python3 install.py --restore ~/.local/state/kool-dotfiles/backups/<日時>
```

## 依存関係

- **必須**: Hyprland `0.57.x`, Python 3, Kitty（`0.51.1` 検証済）, `nwg-dock-hyprland` `0.4.11`, Waybar（`0.16.0` 検証済）, Rofi, SwayNotificationCenter, `jq`, `gsettings`, `fontconfig`, `awww`, Kvantum（Qt5/Qt6）
  - Ubuntu で `install-qt-plugins.py` を使う場合は Qt5.15 / Qt6.4、QtSvg、KF5WindowSystem、Qt5X11Extras のランタイムが必要です（Arch 等では OS パッケージを使用）。
  - `nwg-dock-hyprland` はパッケージまたは [v0.4.11](https://github.com/nwg-piotr/nwg-dock-hyprland/tree/v0.4.11) からビルドして PATH 内に配置してください。
- **補助ツール**: `wallust`, `fastfetch`, `hyprlock`, `grim`, `slurp`, `cliphist`, `Quickshell` 等は必要に応じて導入してください（検証環境の全パッケージは `docs/installed-packages.tsv` を参照）。

## 構成と再現仕様

```text
home/               dotfiles 本体・壁紙・フォント・テーマ・アイコン
foundation/         LazyVim最小構成と日本語入力の初期設定
bootstrap.py        基本道具・Atuin・Mozcの自動導入
hosts/              ホスト固有設定（NVIDIA 環境変数など）
reference-palette/  参照壁紙一致時に使う固定配色
scripts/            導入・検証・CI・パッケージング用スクリプト
```

<details>
<summary>再現する見た目・設定値の詳細</summary>

| 項目 | 値 |
|---|---|
| 壁紙 | `wall_anime_4K.png`（ハッシュ一致時のみ固定配色を適用、変更時は Wallust 生成） |
| バー・Dock | 上部 Waybar 30px / 下部自動非表示 Dock（40px、画面領域非予約） |
| 基本色 | 背景 `#191919` / 文字 `#FCF6F3` / 枠 `#72C8C8` / 非アクティブ `#18615F` / アクセント `#FDB417` |
| ウィンドウ | 枠 2px / 角丸 10px / gaps in 6px・out 8px / blur 6×2 / shadow 3・power 1 |
| 透過率 | 共通 `1.0 / 0.9`・Firefox `0.9 / 0.7`（乗算）・Kitty `0.8 / 0.7`（背景 `0.9`） |
| フォント | Kitty: Noto Sans Mono 12pt / バー・Rofi: JetBrainsMono Nerd Font |
| GTK / Qt | Kali-Dark + Flat-Remix-Blue-Dark / Kvantum `catppuccin-mocha-blue` + Fira Code |

アプリ別ルールと詳細設定は `home/.config/hypr/UserConfigs/user_window_rules.lua` および `user_desktop.lua` を参照してください。

</details>

## 検証・開発・リリース

Ubuntu 24.04 / 26.04 でPython 3.12 / 3.14を検証します。両Ubuntu環境とArch rollingコンテナでは、基本道具とMozcを実際にインストールし、LazyVimの起動・相対行番号・AtuinのBash組み込みまで確認します。GUI/GPUや物理キー入力の検証は実機で別途行います。

Push / PR ごとに GitHub Actions でインストーラのテスト（チェック・適用・冪等性・復元）、Lua/Bash 構文検証、ハッシュ整合性チェックを実行します。タグ（`v*`）を push するとアーカイブとチェックサム付きで GitHub Release を公開します。

```bash
python3 scripts/validate.py               # 実環境チェック（記録: docs/validation.json）
python3 scripts/ci.py                     # CI 検証一式
python3 -m unittest discover -s tests -v  # ユニットテスト
python3 scripts/package.py --version 0.2.0
```

上流の実行時に不要な開発テスト57ファイルは配布用ホームから除外し、本リポジトリのテストは `tests/` に保持しています。新規LazyVimには未使用サンプルを含めません。

## 出典・ライセンス

- **コード・設定**: GPL-3.0-or-later（`LICENSE`）。ベースは [LinuxBeginnings/Hyprland-Dots](https://github.com/LinuxBeginnings/Hyprland-Dots/tree/170b69b846b1cd92ebc6d81c17393e17bed8d416)（v2.3.28.3）および [JaKooLit/Hyprland-Dots](https://github.com/JaKooLit/Hyprland-Dots)。
- **サードパーティ資材**: Kvantum、Flat Remix、Catppuccin Kvantum、Kali-Dark、各フォントおよび壁紙は元のライセンスに従います（詳細は `THIRD_PARTY.md` および `licenses/`）。
