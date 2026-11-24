# Arch KooL appearance for Hyprland 0.57

個人用Arch環境の **JaKooLit v2.3.17の実際の見た目**を、Ubuntu 24.04 / Hyprland 0.57.2のLua設定へ移植したdotfilesです。新しいKooLの既定テーマではなく、参照機の壁紙・生成済み配色・上下バー・透過率・実効フォントを収録しています。

設定の土台は LinuxBeginnings/Hyprland-Dots `170b69b846b1cd92ebc6d81c17393e17bed8d416`（v2.3.28.3）。バージョン、QtパッケージURLとSHA-256は `dependencies.lock.json` に固定しています。設定・壁紙・フォント・GTK/Qtテーマ・アイコンは `home/` に含むため、参照PCへのSSH接続は不要です。これはデスクトップ設定の再現用で、OSやHyprland自体のインストーラではありません。

## 再適用

既存のHyprland 0.57.xセッションで、リポジトリのルートから実行します。インストール先は実行ユーザーのホームです。sudoは使用しません。

```bash
# Ubuntu 24.04 amd64: Qt5/Qt6用プラグインを取得・SHA-256照合してユーザー領域に配置
python3 scripts/install-qt-plugins.py

# このUbuntuデスクトップ（NVIDIA、ee/us、HDMI-A-1）用
python3 install.py --profile ubuntu-desktop --check
python3 install.py --profile ubuntu-desktop --apply

# 違うPC: 既存のUserConfigsの入力・モニター設定を引き継ぐ
python3 install.py --profile generic --check
python3 install.py --profile generic --apply
```

`--check` は差分表示だけです。`--apply` は変更する設定を `~/.local/state/kool-dotfiles/backups/日時/` に保存してから適用し、構文を検証し、壁紙・バー・通知・Kittyを再読み込みします。ログアウトしません。既に起動しているGTK/Qtアプリの一部は、次回起動から新しいテーマとフォントを読み込みます。

汎用プロファイルで既存のHyprland設定が別形式の場合は、最初に `home/.config/hypr/UserConfigs/user_settings.lua` と `monitors.lua` を編集してください。`ubuntu-desktop` プロファイルは別PCにそのまま適用しないでください。

## 復元

適用時に表示された `BACKUP:` のディレクトリを指定します。ファイル・ディレクトリ・元のシンボリックリンク・GTKのGSettingsを復元します。

```bash
python3 install.py --restore ~/.local/state/kool-dotfiles/backups/日時 --check
python3 install.py --restore ~/.local/state/kool-dotfiles/backups/日時
```

Qtプラグインなどの追加ランタイムは残りますが、復元した設定では参照されなくなります。既存のNeovim/LazyVim、ROS、Atuin、NoMachineの起動ラッパーはこのリポジトリの置換対象に含めません。BashにはKitty内だけで働く表示用フックを追加し、既存の設定を保持します。

## 再現する値

| 項目 | 値 |
|---|---|
| 壁紙 | `wall_anime_4K.png`、SHA-256 `6ea87df130eeb91675eafa7af3748afff62efed71d10347fae2d5b0b430d570b` |
| バー | `[TOP & BOT] SummitSplit v2` / `[Dark] Latte-Wallust combined.css`、上下30px |
| 基本色 | 背景 `#191919`、文字 `#FCF6F3`、枠 `#72C8C8`、非アクティブ枠 `#18615F`、アクセント `#FDB417` |
| ウィンドウ | 枠2px、角丸10px、内側余白6px・外側8px |
| ぼかし・影 | blur size6 / passes2、shadow range3 / power1 |
| 共通透過率 | active 1.0 / inactive 0.9 / fullscreen 1.0 |
| Firefox | active 0.9 / inactive 0.7（共通値に乗算、非アクティブの実効値0.63） |
| Kitty | active 0.8 / inactive 0.7、背景opacity 0.9（背景の実効値0.72 / 0.567） |
| Kittyフォント | Noto Sans Mono 12pt。参照側のFantasque指定は未インストールで、このフォントにフォールバックしていた |
| バー・メニュー | JetBrainsMono Nerd Font。バーbold 97%、Rofi SemiBold 15 / 13 |
| GTK | Kali-Dark、Adwaita Sans 11、Flat-Remix-Blue-Dark、Adwaita cursor 24 |
| Qt | Kvantum `catppuccin-mocha-blue`、Fira Code Medium 14（固定幅12） |

アプリ別の全ルールは `home/.config/hypr/UserConfigs/user_window_rules.lua` にあります。Ubuntu Snap版Firefoxのクラス `firefox_firefox` とDolphinのクラスを追加しています。`override` を使わず、参照側と同じ透過率の乗算を維持します。

参照壁紙のハッシュが一致するときだけ、`reference-palette/` の配色を復元します。同じ壁紙でもWallustの版や抽出結果によって色が変わる問題を防ぎます。他の壁紙に切り替えた場合は通常のWallust生成が動きます。

デスクトップ機にはノートPCのバッテリーと内蔵バックライトがないため、その2モジュールは表示しません。Caps Lock表示は入力デバイスへの権限を追加せずsysfsのLEDから取得します。CPU温度センサーはインストール時に選びます。Archの更新数表示はUbuntuのAPTキャッシュに置換し、自動的なパッケージ更新は行いません。

## 依存関係

必須: Hyprland **0.57.x**、Python3、Kitty、Waybar（検証0.16.0）、Rofi、SwayNotificationCenter、jq、gsettings、fontconfig、awww/awww-daemon、Qt5/Qt6のKvantum。Ubuntu用プラグインにはQt5.15 / Qt6.4、QtSvg、KF5WindowSystem、Qt5X11Extrasのランタイムが必要です。`install-qt-plugins.py` はリンク先の不足を `ldd` で検査します。

メニュー・ショートカットで使用する補助ツール: wallust、fastfetch、wlogout、hyprlock、hypridle、hyprsunset、grim、slurp、swappy、wl-clipboard、cliphist、playerctl、pamixer、pavucontrol、brightnessctl、bc、yad、notify-send、nm-applet/nmcli、blueman-manager、nwg-look、Quickshell (`qs`)、Dolphin、Firefox、Neovim。これらのOSパッケージや独自配布バイナリは別途準備してください。検証機のパッケージ版は `docs/installed-packages.tsv` に記録しています。

Ubuntu向けQtプラグイン取得はAPTソースを追加しません。Archなどでは、そのOSの `kvantum` / `qt5ct` / `qt6ct` パッケージを利用してください。NVIDIA設定とNoMachineの子プロセス向けLD_PRELOAD除去は `hosts/ubuntu-desktop/user_env.lua` に分離しています。ML4W由来のQt同梱版Quickshellが存在する場合は専用ラッパーでシステムQtプラグインから分離します。

上流の任意TUIバイナリ（dots-tui）は含めません。Rofiのクイック設定を利用します。固定プロファイルを上流更新で上書きしないよう、バーのdotfiles更新ボタンはGitによる更新手順を案内します。

## 検証・変更

```bash
python3 scripts/validate.py
python3 install.py --profile ubuntu-desktop --check
```

検証記録は `docs/validation.json`、プレビューは `docs/preview.png`。変更後はチェックしてから再適用します。生成色の原本は `reference-palette/`、ホスト依存値は `hosts/`、その他のdotfilesは `home/` です。

## 出典

- [LinuxBeginnings / Hyprland-Dots](https://github.com/LinuxBeginnings/Hyprland-Dots/tree/170b69b846b1cd92ebc6d81c17393e17bed8d416): Lua設定、スクリプトとKooL資材（GPL-3.0）。
- [JaKooLit / Hyprland-Dots](https://github.com/JaKooLit/Hyprland-Dots): 参照環境のバー、Rofi、ターミナル構成。
- [Kvantum](https://github.com/tsujan/Kvantum): Qt Widgetsテーマエンジン。Ubuntu Qt6パッケージは公式導入案内に記載されたPapirus PPAより取得。
- [Flat Remix](https://github.com/daniruiz/flat-remix)、[Catppuccin Kvantum](https://github.com/catppuccin/kvantum)、Kali-Dark、Adwaita/Noto/Fira/JetBrains/Victorフォントは各作者の資材です。取得できたライセンス本文を `licenses/` に保持しています。
- 壁紙と参照側テーマはユーザー所有環境から提供された個人用スナップショットです。SSH接続情報や認証情報はこのリポジトリに含めません。
