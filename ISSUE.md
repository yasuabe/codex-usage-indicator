# 現在の問題点

## 要約

現在の `codex-usage-indicator` は、Codex のライブ使用量を日常判断に使える精度で表示できていない。

現実装は `~/.codex/sessions/**/rollout-*.jsonl` に保存された `token_count.rate_limits` を読んでいるが、これは `/status` のライブ表示とは一致しないことがある。そのため、インジケーターが `0%` 近辺でも、実際の `/status` では数％消費している、というズレが起こる。

## 現時点の判断

- rollout はライブ値の一次情報としては不適切
- ただし rollout 自体が無意味なのではなく、通常ターン完了後の永続化先としては使える
- 理想条件は「ログイン以外は一度も Codex を使ったことのない環境でも動くこと」
- したがって本命課題は「`/status` の内部保存先」ではなく、「新規環境で使用量をどう安定取得するか」
- `tmux` 依存の方式は、新規環境要件と合わないため不採用

## 確認できた事実

- `/status` だけでは、少なくとも直後には `rollout` と `state_5.sqlite.threads` への永続化を確認できなかった
- interactive セッションで通常入力 `hi` を 1 回送ると、`rollout` と `state_5.sqlite.threads` が生成された
- その rollout には `token_count.rate_limits` が入り、`primary.used_percent` / `secondary.used_percent` を確認できた
- 通常ターン中の `token_count` は少なくとも 2 回出ていた
  - 先に `info = null` の rate limit 更新
  - 後で token usage を含む確定値
- `gpt-5.1-codex-mini` でも通常ターン後に同様の永続化が起き、`rate_limits.limit_id` は `codex` のままだった
- セッション終了時の追加 flush は、少なくとも今回の観測では確認できなかった

## 失敗した案

- `codex exec -m gpt-5.1-codex-mini hi`
  - rollout は生成されたが `token_count.rate_limits = null`
- `codex --no-alt-screen -m gpt-5.1-codex-mini hi`
  - 起動時 prompt 引数扱いでは `token_count.rate_limits = null`
- PTY 経由の `/status` 取得
  - フッター断片までは取れたが、必要な `5h limit` / `Weekly limit` 本文は安定取得できていない
- `tmux` を使った補助実験
  - 安定成功に至らず、かつ最終実装の依存にもできない

## 未解決

- `tmux` なしで、interactive セッション起動後に通常ターンを 1 回だけ安全に送る方法があるか
- もしくは `tmux` なしで `/status` 表示の必要行だけを安定取得できるか

## 次に見るべきこと

1. `tmux` 非依存で interactive セッションへ 1 ターン送る方法を探す
2. それが無理なら、`/status` 表示の取得経路を再調査する
3. どちらも難しければ、Codex 実装の静的調査に寄せる
