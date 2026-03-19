# codex-usage-indicator

Ubuntu (GNOME) のトップバーに Codex の利用量を表示する AppIndicator です。

## Requirements

- Ubuntu / GNOME
- `cargo`
- `pkg-config`
- `libgtk-3-dev`
- `libayatana-appindicator3-dev`

```bash
sudo apt install cargo pkg-config libgtk-3-dev libayatana-appindicator3-dev
```

## 情報源

Rust 実装は `~/.codex/sessions/**/rollout-*.jsonl` を読み取り、
`rate_limits != null` を持つ最新の `token_count` snapshot を表示します。

詳しい仕様は [docs/SPEC.md](./docs/SPEC.md) を参照してください。

## Development Run

```bash
cargo run -- ~/.codex/sessions
cargo run --bin indicator
```

## Installer

`install.sh` はユーザー領域にインストールし、ランチャーと自動起動設定を作成します。

- install dir: `~/.local/share/codex-usage-indicator`
- launcher: `~/.local/bin/codex-usage-indicator`
- autostart: `~/.config/autostart/codex-usage-indicator.desktop`

### Install

```bash
./install.sh
```

### Install Options

```bash
./install.sh --dry-run       # 変更せず内容だけ表示
./install.sh --no-autostart  # 自動起動を作らない
./install.sh --start-now     # インストール後に即起動
```

## Uninstaller

`uninstall.sh` はインストール先とランチャー、自動起動設定を削除します。

### Uninstall

```bash
./uninstall.sh
```

### Uninstall Options

```bash
./uninstall.sh --dry-run  # 変更せず内容だけ表示
./uninstall.sh --no-stop  # 実行中プロセス停止をスキップ
```
