#!/usr/bin/env bash
# Hyprnerd quick help. The complete live binding list remains on Super+Shift+K.
set -euo pipefail
runtime="${XDG_RUNTIME_DIR:-/tmp}/hyprnerd"
mkdir -p "$runtime"
exec 9>"$runtime/help.lock"
flock -n 9 || exit 0
rofi -dmenu -i -p 'Hyprnerd ヘルプ' \
  -mesg 'Windows = Super · Escで閉じる · 全キー検索は Windows+Shift+K' \
  -theme-str 'window { width: 800px; } listview { lines: 15; columns: 1; }' <<'KEYS' || true
Windows + Enter                 ターミナルを開く
Windows + H / J / K / L          左 / 下 / 上 / 右のウィンドウ・モニターを選択
Windows + 矢印                  同じ方向のウィンドウ・空のモニターを選択
Windows + Shift + 矢印          タイルを移動・画面端で隣のモニターへ
Windows + Alt + 矢印            ウィンドウのサイズ変更
Windows + Ctrl + ← / →         全モニターのワークスペースを切り替え
Windows + 1 … 0                 ワークスペース1〜10へ
Windows + Shift + 1 … 0         ウィンドウを別のワークスペースへ移動
Windows + Ctrl + N              ワークスペースを追加
Windows + Space                 現在のウィンドウをタイル / 自由配置に切り替え
Windows + Alt + Space           全体のタイル / 自由配置を切り替え
Windows + Q                     閉じる（ブラウザーは4秒以内にもう一度）
Windows + Shift + M             壁紙を一時的に真っ黒 / 元に戻す（配色維持）
Windows + Shift + H             このヘルプを開く
Windows + Shift + K             現在の全キーバインドを検索
Windows + Alt + D               モニター配置の設定
Windows + D                     アプリを起動
Windows + E                     ファイルマネージャー
Windows + W                     壁紙を選択
Ctrl + Space                    日本語入力の切り替え
Ctrl + Alt + D                  自動非表示Dockを有効 / 無効にする
spf（ターミナル内）             ファイル操作・終了した場所を現在のディレクトリにする
KEYS
