# Heartbeat tasks — run every 24h

## Daily night check (00:00 UTC only)
Task: Prices + MA200 trend only for BTC, ETH, SOL. Dry stats. No signal analysis unless NEW signal in last 3 bars.
Run: python3 /home/node/.openclaw/workspace/daily_post.py check
Post to: @cryprofoxs
Note: Якщо сигналу немає — просто ціна + BULLISH/BEARISH відносно MA200. Ніяких розписів.
Priority: high

## 12:00 UTC — Нічого не робити

## Daily TG post (07:00 UTC)
Run: python3 /home/node/.openclaw/workspace/daily_post.py tg (generate) → post to @cryprofoxs
Note: 7:00 UTC = 14:00 MYT
Priority: high

## Daily X post (15:00 UTC) — pending card payment
Run: python3 /home/node/.openclaw/workspace/daily_post.py x | xurl post
Task: Post daily market overview to @Cryptofoxel
Status: Awaiting billing setup on developer.x.com
Priority: medium

## Daily GitHub backup (00:00 UTC)
Run: bash -c 'set -a; source /home/node/.openclaw/workspace/.github-backup.env; set +a; bash /home/node/.openclaw/workspace/github-backup.sh'
Task: Push workspace files to github.com/gigavers3/cryptofox-backup if changed
Output: Silent — only logs on failure.
Priority: medium
