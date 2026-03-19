# codex-usage-indicator 仕様

## 目的

`codex-usage-indicator` は、このマシン上の Codex 利用量を素早く確認するための
ローカル indicator である。

このアプリケーションは `/status` のライブ値を再現しない。
ローカルに永続化済みの rollout から、もっとも新しい利用量 snapshot を読む。

## 情報源

情報源は `~/.codex/sessions/**/rollout-*.jsonl` である。

各 rollout ファイルの各行を走査し、次の条件を満たす `event_msg` を探す。

- `payload.type == "token_count"`
- `payload.rate_limits != null`

採用するのは、ファイルの更新時刻が最新のものではなく、
上記条件を満たす `token_count` イベントの `timestamp` が最も新しいものとする。

同じ `timestamp` を持つ候補が複数ある場合は、より利用量が逼迫している方を採用する。
ここで「逼迫している」とは、`used_percent` が大きいことを意味する。

同時刻候補の比較順序は次のとおりとする。

- `primary.used_percent` が大きい方を優先
- `primary.used_percent` が同じなら `secondary.used_percent` が大きい方を優先
- それでも同じなら、実装依存の安定した順序でよい

## 利用量の定義

このアプリケーションが表示する利用量は、次のように定義する。

- indicator を起動しているマシン上の全 rollout を対象にする
- その中で `rate_limits != null` を持つ最新の `token_count` を探す
- その `token_count.rate_limits` を表示値として採用する

したがって、表示値は「全セッションの中で最後に永続化された `rate_limits` snapshot」
であり、ライブ現在値ではない。

## 表示内容

メニューには次を表示する。

- `5h limit`
  - `rate_limits.primary.used_percent` から算出する
  - 表示は `98% left` のような残量表現とする
- `Weekly limit`
  - `rate_limits.secondary.used_percent` から算出する
  - 表示は残量表現とする
- `Plan`
  - `rate_limits.plan_type` を表示する
- `更新`
  - 先頭の時刻は indicator 自身が読み直した時刻
  - 括弧内の時刻は、採用した `token_count` snapshot の時刻

表示例:

- `更新: 21:32:10 (21:16:05)`

この例は、

- indicator 自身は `21:32:10` に更新した
- ただし採用した rollout snapshot は `21:16:05` のものだった

ことを意味する。

## 更新方法

更新方法は次の2つである。

- 30秒ごとのポーリング
- メニューの `今すぐ更新`

どちらも同じ検索ルールを使う。
どちらも `更新: [更新時刻] ([snapshot時刻])` の形式で表示する。

## 保証しないこと

このアプリケーションは、次を保証しない。

- Codex `/status` と完全一致すること
- ターン進行中のライブ利用量を表示すること
- 他マシン上の Codex 利用量を表示すること
- 更新操作によって新しい usage snapshot を強制生成すること

## 実装メモ

この節は仕様本体ではなく、探索方針のメモである。

正しい結果は「全 rollout 中で、`rate_limits != null` を持つ最新 `token_count` を選ぶこと」
で定義される。探索順序は最適化の余地がある。

実装上は、次の方針が望ましい。

- 新しい日付ディレクトリから優先して見る
- 各 rollout では `token_count` のうち `rate_limits != null` の候補だけを対象にする
- より新しい日付で候補が見つからない場合にだけ、古い日付へ広げる
- 必要なら探索対象を直近 N 日に制限できるようにする

注意:

- 単に「最初に見つかった候補」で打ち切ると誤る可能性がある
- 正しさを優先するなら、少なくとも比較対象になりうる候補の `timestamp` は確認する必要がある
