# MEMORY.md

## Клієнт
- Ім'я: Lumier (Telegram: @artistlutik)

## Поточний проект — Продаж сигналів на ACP

### Статус налаштувань
- **ACP агент:** CRYPTOFOX (ID: 01a02f4c-3e1b-792b-b0d0-2c3317370414)
- **EVM гаманець:** 0xeb7389978aaf4011e988a455805f0a7a89a7224a
- **Solana гаманець:** A9npAXFUbewZban2EQzhbf5rrECAAGqVRihEHxDnPfgk
- **Підписанти:** 3 (unrestricted політика), всі працюють
- **Offering:** "cryptofoxs" — $0.10/сигнал + premium $1/30днів
- **Слухач подій:** запущено (events listen --all, data/events.jsonl)

### Правила входу/виходу CryptoFox (оновлено 29.08.2026)

**Пріоритети сигналів:**
- P1: Weekly breakout (regular div + first AO bar + пробій хаю) — головний
- P2: Daily breakout (те саме на денному)
- P3: Volume & trend health (підтвердження, exhaustion)
- P4: MA50/MA200 (контекст)

**Ризик-менеджмент:**
- Макс ризик на 1 позицію: 5% капіталу
- Макс позицій у портфелі: 3
- Макс загальний ризик портфеля: 15%
- Важливий контроль втрат, а не об'єм позиції

**Пірамідінг (Дракенміллер):**
- Probe: 5-10% — regular div + перший AO стовпець
- Confirmation: +15-20% — AO підтверджує
- Pyramid: +20-30% — hidden div + Volume > 1.0x
- Jugular: до 50% — прискорення

**Вихід:**
- Take Profit 1:4 (risk:reward)
- Стоп під локальний мінімум (другий low дивергенції)
- Інвалідація тези: MACD анулювався, AO розвернувся
- Моментум слабшає (AO падає, volume падає)

**Підсилювачі:**
- BTC контекст: BTC breakout → підсилює альти
- Подвійна/потрійна дивергенція → вища вага сигналу

**Тільки 1d/1w** таймфрейми

### Формат ACP сигналу
- Deliverable: JSON з direction, asset, entry, stop_loss, take_profit, conviction, macro_rationale
- Тільки англійською
- S/R рівні: мінімум 3 торки за 100 днів
- Дивергенція: тільки якщо є, не згадувати відсутність
- Основна структура: MA trend, ключові S/R, volume, режим (RISK-ON/OFF/TRANSITION)

## Крон-завдання (в OpenClaw)
- **trading-cycle**: 0 0,12 * * * (00:00 та 12:00 UTC)
- О 00:00 → запустити `python3 daily_post.py check` і відправити в @cryprofoxs
- О 12:00 → ігнорувати (не робити нічого)

### Формат 00:00 UTC (check) — ЩОДЕННИЙ ОГЛЯД
- 4 активи: BTC, ETH, SOL, PENGU
- Режим ринку (RISK-ON/OFF/TRANSITION)
- По кожному: тренд MA200 + %, MA50/MA200, об'єм, S/R рівні
- Дивергенції: ТІЛЬКИ НОВІ (1d ago ≤ 5, 1w ago ≤ 3). Старі не згадувати.
- Golden/Death Cross: показувати якщо стався нещодавно
- Вердикт + рекомендація

### Формат 07:00 UTC (tg) — ЩОДЕННИЙ АНАЛІЗ
- 4 активи: BTC, ETH, SOL, PENGU
- Той самий розпис, але дивергенції: ВСІ (і старі, і нові)
- Повний аналітичний звіт

## Що залишилося
1. ✅ Offering створено (cryptofoxs, $0.10/сигнал + premium $1/30днів)
2. ✅ Аутентифікація на Virtuals
3. ✅ Signer (unrestricted)
4. ❌ ETH на Base для газу (потрібно $1-2)
5. ✅ Слухач подій (events listen, працює)
6. ❌ DegenClaw реєстрація (заблоковано — v2 сирий, проблема з Privy гаманцем)
7. ⏳ Демо-сигнал для Lumier
