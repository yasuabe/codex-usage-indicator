# codex-usage-indicator

Personal GNOME AppIndicator for Codex usage.

Current Python prototype reads recent `~/.codex/sessions/**/rollout-*.jsonl` files and displays:

- 5h limit
- Weekly limit
- plan type

`Context window` is intentionally out of scope.

## Run

```bash
python3 -m codex_usage_indicator.main --mock
python3 -m codex_usage_indicator.main
```
