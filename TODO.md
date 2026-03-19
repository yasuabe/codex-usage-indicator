# TODO

- 探索の最適化
  - `~/.codex/sessions` 配下を新しい日付ディレクトリから優先して探索する
  - `rate_limits != null` の `token_count` 候補を効率よく見つける
  - 必要なら探索対象を直近 N 日に制限できるようにする

- ログ出力
  - どの rollout を採用したかを分かるようにする
  - 候補比較の結果と、最終的に選ばれた snapshot の timestamp を記録できるようにする
  - `rate_limits` が見つからなかった場合の理由を追いやすくする
