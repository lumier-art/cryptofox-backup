# Heartbeat tasks — run every 24h

## Daily night check (00:00 UTC only)
Task: Повний аналіз 4 активів (BTC, ETH, SOL, PENGU) — такий самий формат як TG.
  - Режим ринку (RISK-ON/OFF/TRANSITION)
  - По кожному: тренд (MA200 + %), MA50/MA200, об'єм, S/R рівні
  - Дивергенції: ТІЛЬКИ НОВІ (1d ≤ 5 bars, 1w ≤ 3 bars). Старі не згадувати.
  - Свіжі Golden/Death Cross — показувати.
  - Вердикт + рекомендація
Run: python3 /home/node/.openclaw/workspace/daily_post.py check → post to @cryprofoxs
Priority: high

## 12:00 UTC — Нічого не робити

## Daily TG post (07:00 UTC)
Task: Повний аналіз 4 активів (BTC, ETH, SOL, PENGU).
  - Тренд (MA200 + %)
  - MA50/MA200 (Golden/Death Cross, або вище/нижче)
  - Об'єм (відносно 50d середнього)
  - Рівні S/R (топ-3 з кількістю дотиків)
  - Дивергенції: ВСІ (і старі, і нові) — це повний звіт
  - Вердикт + рекомендація
Run: python3 /home/node/.openclaw/workspace/daily_post.py tg (generate) → post to @cryprofoxs
Note: 7:00 UTC = 14:00 MYT
Priority: high

## Daily NFT scan (07:00 UTC)
Task: Сканувати Robinhood Chain на нові NFT проекти. Зібрати:
  - Свіжі free mint проекти (Twitter)
  - NFT Calendar дропи
  - OpenSea trending
  - Оцінити кожен за системою score_project()
  - Відправити звіт Lumier
Run: web_search + nft_scanner.py → python3 nft_scanner.py check
Output: Повний звіт з оцінкою 🟢STRONG/🟡WATCH/🔴WEAK
Cron: ✅ nft-scan (0 7 * * * exact) — активний
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
Cron: ✅ github-backup (0 0 * * * exact) — активний, підхоплений гейтвеєм
Priority: medium
