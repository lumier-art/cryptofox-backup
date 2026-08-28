# Heartbeat tasks — run every 24h

## Daily market scan + post (07:00 UTC)
Task: Check all signals on 1d/1w, identify new breakout entries, and post to @cryprofoxs
Run: python3 /home/node/.openclaw/workspace/daily_post.py tg (generate), then post to @cryprofoxs
Entry logic: Check for first green AO bar after divergence on closed candle → compute BUY STOP level above candle high
Note: 7:00 UTC = 14:00 MYT
Priority: high

## Daily X post (15:00 UTC) — pending card payment
Run: python3 /home/node/.openclaw/workspace/daily_post.py x | xurl post
Task: Post daily market overview to @Cryptofoxel
Status: Awaiting billing setup on developer.x.com
Priority: medium

## Daily GitHub backup
Run: source /home/node/.openclaw/workspace/.github-backup.env && bash /home/node/.openclaw/workspace/github-backup.sh
Task: Push MEMORY.md, ta.py, SOUL.md, config.json to github.com/gigavers3/cryptofox-backup
Output: Silent — only logs on failure.
Priority: medium
