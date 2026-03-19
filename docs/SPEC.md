# codex-usage-indicator 仕様

## 目的

このマシン上の Codex 利用量を、GNOME トップバーから素早く確認する。

## 制約

- `/status` のライブ値を再現するものではない
- 表示値はローカルに永続化済みの rollout snapshot であり、リアルタイムの現在値ではない
- ターン進行中のライブ利用量は反映されない
- 他マシン上の Codex 利用量は対象外である
- 更新操作が新しい usage snapshot の生成を強制することはない

## 情報源

`~/.codex/sessions/**/rollout-*.jsonl`

## 選択ルール

全 rollout ファイルの各行を走査し、次の条件を満たす `event_msg` を探す。

- `payload.type == "token_count"`
- `payload.rate_limits != null`

条件を満たす候補のうち、`timestamp` が最も新しいものを採用する。
ファイルの更新時刻ではなく、イベント自体の `timestamp` で判断する。

同じ `timestamp` を持つ候補が複数ある場合は、より利用量が逼迫している方を採用する。
ここで「逼迫している」とは、`used_percent` が大きいことを意味する。

同時刻候補の比較順序は次のとおりとする。

- `primary.used_percent` が大きい方を優先
- `primary.used_percent` が同じなら `secondary.used_percent` が大きい方を優先
- それでも同じなら、実装依存の安定した順序でよい

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

どちらも同じ選択ルールを使う。
どちらも `更新: [更新時刻] ([snapshot時刻])` の形式で表示する。

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
