#!/usr/bin/env python3
"""
CryptoFox Daily Post Generator — generates content for Telegram & X.
Run daily at 15:00 UTC for X post, 07:00 UTC for Telegram, 00:00 UTC for check.
"""

import sys
sys.path.insert(0, '/home/node/.openclaw/workspace')
import ta
from datetime import datetime, timezone

ASSETS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "AVAXUSDT", "DOGEUSDT", "LINKUSDT", "BNBUSDT", "VIRTUALUSDT"]
CORE = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "PENGUUSDT"]

def get_bs(sym, tf, macd_min=60):
    c, h, l, _ = ta.fetch_klines(sym, tf, 200)
    return c, ta.find_breakout_signal(c, h, l, macd_min)

def pct(a, b):
    return (a/b - 1) * 100

def asset_analysis(sym, tf="1d"):
    """Return full analysis dict for an asset."""
    c, h, l, v = ta.fetch_klines(sym, tf, 201)
    last = c[-1]
    ma50 = ta.ema(c, 50) or 0
    ma200 = ta.ema(c, 200) or 0
    avg_v = sum(v[-50:]) / 50
    vol_ratio = v[-1] / avg_v if avg_v > 0 else 0
    
    # Trend
    trend = "BULLISH" if last > ma200 else "BEARISH"
    pct_ma200 = pct(last, ma200) if ma200 else 0
    
    # Golden/death cross
    prev_ma50 = ta.ema(c[:-1], 50) if len(c) >= 201 else None
    prev_ma200 = ta.ema(c[:-1], 200) if len(c) >= 201 else None
    cross = None
    if prev_ma50 and prev_ma200 and ma50 and ma200:
        if prev_ma50 <= prev_ma200 and ma50 > ma200:
            cross = "GOLDEN_CROSS"
        elif prev_ma50 >= prev_ma200 and ma50 < ma200:
            cross = "DEATH_CROSS"
    
    # Divergence 1d
    bs_d = ta.find_breakout_signal(c, h, l)
    div_d = None
    if bs_d and bs_d.get("broke_out"):
        div_d = {
            "count": bs_d.get("div_count", 1),
            "entry": bs_d["signal_high"],
            "stop": bs_d["stop_price"],
            "current": last,
            "pct_from_entry": pct(last, bs_d["signal_high"]),
            "bar": bs_d.get("entry_bar", 0),
            "ago": len(c) - bs_d.get("entry_bar", 0),
        }
    
    # Divergence 1w
    cw, hw, lw, _ = ta.fetch_klines(sym, "1w", 100)
    bs_w = ta.find_breakout_signal(cw, hw, lw, 30)
    div_w = None
    if bs_w and bs_w.get("broke_out"):
        div_w = {
            "count": bs_w.get("div_count", 1),
            "entry": bs_w["signal_high"],
            "stop": bs_w["stop_price"],
            "current": cw[-1] if len(cw) > 0 else last,
            "pct_from_entry": pct(cw[-1] if len(cw) > 0 else last, bs_w["signal_high"]),
            "bar": bs_w.get("entry_bar", 0),
            "ago": len(cw) - bs_w.get("entry_bar", 0),
        }
    
    # S/R levels
    sr = ta.find_support_resistance(h, l, c)
    
    return {
        "name": sym.replace("USDT", ""),
        "price": last,
        "ma50": ma50,
        "ma200": ma200,
        "trend": trend,
        "pct_ma200": pct_ma200,
        "cross": cross,
        "vol_ratio": vol_ratio,
        "sr": sr,
        "div_d": div_d,
        "div_w": div_w,
    }

def regime_classification():
    """Classify current market regime."""
    btc_a = asset_analysis("BTCUSDT")
    signals = 0
    for a in CORE:
        aa = asset_analysis(a)
        if aa["trend"] == "BULLISH":
            signals += 1
        if aa["div_d"]:
            signals += 1
        if aa["div_w"]:
            signals += 2
        if aa["cross"] == "GOLDEN_CROSS":
            signals += 1
    if signals >= 6:
        return "RISK-ON 🟢"
    elif signals >= 3:
        return "TRANSITION 🟡"
    else:
        return "RISK-OFF 🔴"

def generate_daily_check():
    """
    Midnight check — 00:00 UTC.
    Той самий повний аналіз, що й TG, але дивергенції ТІЛЬКИ НОВІ (свіжі).
    Старі дивергенції не згадувати.
    """
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = ["🦊 CRYPTOFOX — ЩОДЕННИЙ ОГЛЯД", f"📅 {now}", "━"*30, ""]
    
    regime = regime_classification()
    lines.append(f"📊 РЕЖИМ РИНКУ: {regime}")
    lines.append("")
    
    has_new_signal = False
    
    # ── BTC ──
    a = asset_analysis("BTCUSDT")
    lines.append(f"━━━ 🏛️ BTC — ${a['price']:,.0f} ━━━")
    trend_e = "🟢" if a["trend"] == "BULLISH" else "🔴"
    lines.append(f"Тренд: {trend_e} {a['trend']} вище MA200 (${a['ma200']:,.0f}, {a['pct_ma200']:+.1f}%)")
    if a["cross"] == "GOLDEN_CROSS":
        lines.append(f"🟢 Golden Cross: MA50 (${a['ma50']:,.0f}) > MA200 (${a['ma200']:,.0f})")
        has_new_signal = True
    elif a["cross"] == "DEATH_CROSS":
        lines.append(f"🔴 Death Cross: MA50 (${a['ma50']:,.0f}) < MA200 (${a['ma200']:,.0f})")
    elif a["ma50"] > a["ma200"]:
        lines.append(f"MA50: ${a['ma50']:,.0f} 🟢 Вище MA200")
    else:
        lines.append(f"MA50: ${a['ma50']:,.0f} 🔴 Нижче MA200")
    vol_e = "📈 високий" if a["vol_ratio"] > 1.5 else "📊 середній" if a["vol_ratio"] > 0.5 else "📉 низький"
    lines.append(f"Об'єм: {vol_e} ({a['vol_ratio']:.2f}x)")
    if a["div_w"] and a["div_w"]["ago"] <= 3:
        dc = a["div_w"]["count"]
        tag = "🔥🔥🔥 ПОТРІЙНА" if dc >= 3 else "🔥🔥 ПОДВІЙНА" if dc >= 2 else "🔥 НОВА"
        lines.append(f"Сигнал: {tag} тижнева дивергенція ({dc}x)")
        lines.append(f"  Вхід: ${a['div_w']['entry']:,.0f} | Стоп: ${a['div_w']['stop']:,.0f} | Поточна: ${a['price']:,.0f} ({a['div_w']['pct_from_entry']:+.1f}%)")
        has_new_signal = True
    if a["div_d"] and a["div_d"]["ago"] <= 5:
        dc = a["div_d"]["count"]
        tag = "🔥🔥🔥 ПОТРІЙНА" if dc >= 3 else "🔥🔥 ПОДВІЙНА" if dc >= 2 else "🔥 НОВА"
        lines.append(f"Сигнал: {tag} денна дивергенція ({dc}x)")
        lines.append(f"  Вхід: ${a['div_d']['entry']:,.0f} | Стоп: ${a['div_d']['stop']:,.0f}")
        has_new_signal = True
    r_str = " | ".join([f"R{i+1} ${r['price']:,.0f} ({r['touches']}x)" for i, r in enumerate(a["sr"]["resistance"][:3])])
    s_str = " | ".join([f"S{i+1} ${s['price']:,.0f} ({s['touches']}x)" for i, s in enumerate(a["sr"]["support"][:3])])
    if r_str:
        lines.append(f"🔺 Опір: {r_str}")
    if s_str:
        lines.append(f"🔻 Підтр: {s_str}")
    lines.append("")
    
    # ── ETH ──
    a = asset_analysis("ETHUSDT")
    lines.append(f"━━━ 💎 ETH — ${a['price']:,.0f} ━━━")
    trend_e = "🟢" if a["trend"] == "BULLISH" else "🔴"
    lines.append(f"Тренд: {trend_e} {a['trend']} вище MA200 (${a['ma200']:,.0f}, {a['pct_ma200']:+.1f}%)")
    if a["cross"] == "GOLDEN_CROSS":
        lines.append(f"🟢 Golden Cross: MA50 > MA200")
        has_new_signal = True
    elif a["ma50"] > a["ma200"]:
        lines.append(f"MA50: ${a['ma50']:,.0f} 🟢 Вище MA200")
    else:
        lines.append(f"MA50: ${a['ma50']:,.0f} 🔴 Нижче MA200")
    vol_e = "📈 високий" if a["vol_ratio"] > 1.5 else "📊 середній" if a["vol_ratio"] > 0.5 else "📉 низький"
    lines.append(f"Об'єм: {vol_e} ({a['vol_ratio']:.2f}x)")
    if a["div_w"] and a["div_w"]["ago"] <= 3:
        dc = a["div_w"]["count"]
        tag = "🔥🔥🔥 ПОТРІЙНА" if dc >= 3 else "🔥🔥 ПОДВІЙНА" if dc >= 2 else "🔥 НОВА"
        lines.append(f"Сигнал: {tag} тижнева дивергенція ({dc}x)")
        lines.append(f"  Вхід: ${a['div_w']['entry']:,.0f} | Стоп: ${a['div_w']['stop']:,.0f} | Поточна: ${a['price']:,.0f} ({a['div_w']['pct_from_entry']:+.1f}%)")
        has_new_signal = True
    if a["div_d"] and a["div_d"]["ago"] <= 5:
        dc = a["div_d"]["count"]
        tag = "🔥🔥🔥 ПОТРІЙНА" if dc >= 3 else "🔥🔥 ПОДВІЙНА" if dc >= 2 else "🔥 НОВА"
        lines.append(f"Сигнал: {tag} денна дивергенція ({dc}x)")
        lines.append(f"  Вхід: ${a['div_d']['entry']:,.0f} | Стоп: ${a['div_d']['stop']:,.0f}")
        has_new_signal = True
    r_str = " | ".join([f"R{i+1} ${r['price']:,.0f} ({r['touches']}x)" for i, r in enumerate(a["sr"]["resistance"][:3])])
    s_str = " | ".join([f"S{i+1} ${s['price']:,.0f} ({s['touches']}x)" for i, s in enumerate(a["sr"]["support"][:3])])
    if r_str:
        lines.append(f"🔺 Опір: {r_str}")
    if s_str:
        lines.append(f"🔻 Підтр: {s_str}")
    lines.append("")
    
    # ── SOL ──
    a = asset_analysis("SOLUSDT")
    lines.append(f"━━━ ☀️ SOL — ${a['price']:,.2f} ━━━")
    trend_e = "🟢" if a["trend"] == "BULLISH" else "🔴"
    lines.append(f"Тренд: {trend_e} {a['trend']} вище MA200 (${a['ma200']:,.0f}, {a['pct_ma200']:+.1f}%)")
    if a["ma50"] > a["ma200"]:
        lines.append(f"MA50: ${a['ma50']:,.0f} 🟢 Вище MA200")
    else:
        lines.append(f"MA50: ${a['ma50']:,.0f} 🔴 Нижче MA200")
    vol_e = "📈 високий" if a["vol_ratio"] > 1.5 else "📊 середній" if a["vol_ratio"] > 0.5 else "📉 низький"
    lines.append(f"Об'єм: {vol_e} ({a['vol_ratio']:.2f}x)")
    if a["div_w"] and a["div_w"]["ago"] <= 3:
        dc = a["div_w"]["count"]
        tag = "🔥🔥🔥 ПОТРІЙНА" if dc >= 3 else "🔥🔥 ПОДВІЙНА" if dc >= 2 else "🔥 НОВА"
        lines.append(f"Сигнал: {tag} тижнева дивергенція ({dc}x)")
        lines.append(f"  Вхід: ${a['div_w']['entry']:,.2f} | Стоп: ${a['div_w']['stop']:,.2f} | Поточна: ${a['price']:,.2f} ({a['div_w']['pct_from_entry']:+.1f}%)")
        has_new_signal = True
    if a["div_d"] and a["div_d"]["ago"] <= 5:
        dc = a["div_d"]["count"]
        tag = "🔥🔥🔥 ПОТРІЙНА" if dc >= 3 else "🔥🔥 ПОДВІЙНА" if dc >= 2 else "🔥 НОВА"
        lines.append(f"Сигнал: {tag} денна дивергенція ({dc}x)")
        lines.append(f"  Вхід: ${a['div_d']['entry']:,.2f} | Стоп: ${a['div_d']['stop']:,.2f}")
        has_new_signal = True
    r_str = " | ".join([f"R{i+1} ${r['price']:,.0f} ({r['touches']}x)" for i, r in enumerate(a["sr"]["resistance"][:3])])
    s_str = " | ".join([f"S{i+1} ${s['price']:,.0f} ({s['touches']}x)" for i, s in enumerate(a["sr"]["support"][:3])])
    if r_str:
        lines.append(f"🔺 Опір: {r_str}")
    if s_str:
        lines.append(f"🔻 Підтр: {s_str}")
    lines.append("")
    
    # ── PENGU ──
    a = asset_analysis("PENGUUSDT")
    lines.append(f"━━━ 🐧 PENGU — ${a['price']:,.4f} ━━━")
    trend_e = "🟢" if a["trend"] == "BULLISH" else "🔴"
    lines.append(f"Тренд: {trend_e} {a['trend']} вище MA200 (${a['ma200']:,.4f}, {a['pct_ma200']:+.1f}%)")
    if a["cross"] == "GOLDEN_CROSS":
        lines.append(f"🟢 GOLDEN CROSS — MA50 перетнула MA200 вгору!")
        has_new_signal = True
    elif a["cross"] == "DEATH_CROSS":
        lines.append(f"🔴 DEATH CROSS — MA50 нижче MA200")
    elif a["ma50"] > a["ma200"]:
        lines.append(f"MA50: ${a['ma50']:,.4f} 🟢 Вище MA200")
    else:
        lines.append(f"MA50: ${a['ma50']:,.4f} 🔴 Нижче MA200")
    vol_e = "📈 високий" if a["vol_ratio"] > 1.5 else "📊 середній" if a["vol_ratio"] > 0.5 else "📉 низький"
    lines.append(f"Об'єм: {vol_e} ({a['vol_ratio']:.2f}x)")
    if a["div_w"] and a["div_w"]["ago"] <= 3:
        dc = a["div_w"]["count"]
        tag = "🔥🔥🔥 ПОТРІЙНА" if dc >= 3 else "🔥🔥 ПОДВІЙНА" if dc >= 2 else "🔥 НОВА"
        lines.append(f"Сигнал: {tag} тижнева дивергенція ({dc}x)")
        lines.append(f"  Вхід: ${a['div_w']['entry']:,.4f} | Стоп: ${a['div_w']['stop']:,.4f} | Поточна: ${a['price']:,.4f} ({a['div_w']['pct_from_entry']:+.1f}%)")
        has_new_signal = True
    if a["div_d"] and a["div_d"]["ago"] <= 5:
        dc = a["div_d"]["count"]
        tag = "🔥🔥🔥 ПОТРІЙНА" if dc >= 3 else "🔥🔥 ПОДВІЙНА" if dc >= 2 else "🔥 НОВА"
        lines.append(f"Сигнал: {tag} денна дивергенція ({dc}x)")
        lines.append(f"  Вхід: ${a['div_d']['entry']:,.4f} | Стоп: ${a['div_d']['stop']:,.4f}")
        has_new_signal = True
    r_str = " | ".join([f"R{i+1} ${r['price']:,.4f} ({r['touches']}x)" for i, r in enumerate(a["sr"]["resistance"][:3])])
    s_str = " | ".join([f"S{i+1} ${s['price']:,.4f} ({s['touches']}x)" for i, s in enumerate(a["sr"]["support"][:3])])
    if r_str:
        lines.append(f"🔺 Опір: {r_str}")
    if s_str:
        lines.append(f"🔻 Підтр: {s_str}")
    lines.append("")
    
    # ── VERDICT ──
    lines.append("━"*30)
    lines.append("🧠 ВЕРДИКТ:")
    btc_a = asset_analysis("BTCUSDT")
    eth_a = asset_analysis("ETHUSDT")
    sol_a = asset_analysis("SOLUSDT")
    pengu_a = asset_analysis("PENGUUSDT")
    bullish_count = sum(1 for a in [btc_a, eth_a, sol_a, pengu_a] if a["trend"] == "BULLISH")
    if bullish_count >= 3:
        if has_new_signal:
            lines.append("🟢 RISK-ON: Більшість активів у бичачому тренді. Є свіжі сигнали.")
            lines.append("Рекомендація: слідкувати за підтвердженням нових сигналів.")
        else:
            lines.append("🟢 RISK-ON: Більшість активів у бичачому тренді. Нових сигналів немає.")
            lines.append("Рекомендація: утримувати позиції.")
    elif bullish_count >= 2:
        lines.append("🟡 TRANSITION: Змішані сигнали.")
        lines.append("Рекомендація: дрібні проби, чекати підтвердження.")
    else:
        lines.append("🔴 RISK-OFF: Оборона.")
        lines.append("Рекомендація: кеш, хеджі, чекати.")
    lines.append("")
    lines.extend(["━"*30, "🦊 CryptoFox — t.me/cryprofoxs"])
    return "\n".join(lines)


def generate_tg_post():
    """
    Full analytical TG post — 07:00 UTC
    Режим, макро, 4 core assets з повним розписом, сигнали.
    """
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = ["🦊 CRYPTOFOX — ЩОДЕННИЙ АНАЛІЗ", f"📅 {now}", "━"*30, ""]
    
    regime = regime_classification()
    lines.append(f"📊 РЕЖИМ РИНКУ: {regime}")
    lines.append("")
    
    # ── BTC ──
    a = asset_analysis("BTCUSDT")
    lines.append(f"━━━ 🏛️ BTC — ${a['price']:,.0f} ━━━")
    trend_e = "🟢" if a["trend"] == "BULLISH" else "🔴"
    lines.append(f"Тренд: {trend_e} {a['trend']} вище MA200 (${a['ma200']:,.0f}, {a['pct_ma200']:+.1f}%)")
    if a["cross"] == "GOLDEN_CROSS":
        lines.append(f"🟢 Golden Cross: MA50 (${a['ma50']:,.0f}) > MA200 (${a['ma200']:,.0f}) — бичачий перети��")
    elif a["cross"] == "DEATH_CROSS":
        lines.append(f"🔴 Death Cross: MA50 (${a['ma50']:,.0f}) < MA200 (${a['ma200']:,.0f}) — ведмежий перетин")
    elif a["ma50"] > a["ma200"]:
        lines.append(f"MA50: ${a['ma50']:,.0f} 🟢 Вище MA200 — тренд підтримується")
    else:
        lines.append(f"MA50: ${a['ma50']:,.0f} 🔴 Нижче MA200 — короткостроковий тренд слабший")
    
    vol_e = "📈 високий" if a["vol_ratio"] > 1.5 else "📊 середній" if a["vol_ratio"] > 0.5 else "📉 низький"
    lines.append(f"Об'єм: {vol_e} ({a['vol_ratio']:.2f}x від 50d середнього)")
    
    if a["div_w"]:
        dc = a["div_w"]["count"]
        tag = "🔥🔥🔥 ПОТРІЙНА" if dc >= 3 else "🔥🔥 ПОДВІЙНА" if dc >= 2 else "🔥 ЗВИЧАЙНА"
        lines.append(f"Сигнал: {tag} тижнева дивергенція ({dc}x)")
        lines.append(f"  Вхід: ${a['div_w']['entry']:,.0f} | Стоп: ${a['div_w']['stop']:,.0f}")
        lines.append(f"  Поточна: ${a['price']:,.0f} ({a['div_w']['pct_from_entry']:+.1f}%)")
    if a["div_d"]:
        dc = a["div_d"]["count"]
        tag = "🔥🔥🔥 ПОТРІЙНА" if dc >= 3 else "🔥🔥 ПОДВІЙНА" if dc >= 2 else "🔥 ЗВИЧАЙНА"
        lines.append(f"Сигнал: {tag} денна дивергенція ({dc}x)")
        lines.append(f"  Вхід: ${a['div_d']['entry']:,.0f} | Стоп: ${a['div_d']['stop']:,.0f}")
    
    # S/R
    r_str = " | ".join([f"R{i+1} ${r['price']:,.0f} ({r['touches']}x)" for i, r in enumerate(a["sr"]["resistance"][:3])])
    s_str = " | ".join([f"S{i+1} ${s['price']:,.0f} ({s['touches']}x)" for i, s in enumerate(a["sr"]["support"][:3])])
    if r_str:
        lines.append(f"🔺 Опір: {r_str}")
    if s_str:
        lines.append(f"🔻 Підтр: {s_str}")
    lines.append("")
    
    # ── ETH ──
    a = asset_analysis("ETHUSDT")
    lines.append(f"━━━ 💎 ETH — ${a['price']:,.0f} ━━━")
    trend_e = "🟢" if a["trend"] == "BULLISH" else "🔴"
    lines.append(f"Тренд: {trend_e} {a['trend']} вище MA200 (${a['ma200']:,.0f}, {a['pct_ma200']:+.1f}%)")
    if a["cross"] == "GOLDEN_CROSS":
        lines.append(f"🟢 Golden Cross активний �� MA50 > MA200")
    elif a["ma50"] > a["ma200"]:
        lines.append(f"MA50: ${a['ma50']:,.0f} 🟢 Вище MA200")
    else:
        lines.append(f"MA50: ${a['ma50']:,.0f} 🔴 Нижче MA200")
    
    vol_e = "📈" if a["vol_ratio"] > 1.5 else "📊" if a["vol_ratio"] > 0.5 else "📉"
    lines.append(f"Об'єм: {vol_e} {a['vol_ratio']:.2f}x")
    
    if a["div_w"]:
        dc = a["div_w"]["count"]
        lines.append(f"🔥 Сигнал: тижнева дивергенція ({dc}x) — ${a['div_w']['entry']:,.0f} → ${a['price']:,.0f}")
    if a["div_d"]:
        dc = a["div_d"]["count"]
        lines.append(f"🔥 Сигнал: денна дивергенція ({dc}x) — ${a['div_d']['entry']:,.0f} → ${a['price']:,.0f}")
    
    r_str = " | ".join([f"R{i+1} ${r['price']:,.0f} ({r['touches']}x)" for i, r in enumerate(a["sr"]["resistance"][:3])])
    s_str = " | ".join([f"S{i+1} ${s['price']:,.0f} ({s['touches']}x)" for i, s in enumerate(a["sr"]["support"][:3])])
    if r_str:
        lines.append(f"🔺 Опір: {r_str}")
    if s_str:
        lines.append(f"🔻 Підтр: {s_str}")
    lines.append("")
    
    # ── SOL ──
    a = asset_analysis("SOLUSDT")
    lines.append(f"━━━ ☀️ SOL — ${a['price']:,.2f} ━━━")
    trend_e = "🟢" if a["trend"] == "BULLISH" else "🔴"
    lines.append(f"Тренд: {trend_e} {a['trend']} вище MA200 (${a['ma200']:,.0f}, {a['pct_ma200']:+.1f}%)")
    if a["ma50"] > a["ma200"]:
        lines.append(f"MA50: ${a['ma50']:,.0f} 🟢 Вище MA200 — тренд сильний")
    else:
        lines.append(f"MA50: ${a['ma50']:,.0f} 🔴 Нижче MA200")
    
    vol_e = "📈" if a["vol_ratio"] > 1.5 else "📊" if a["vol_ratio"] > 0.5 else "📉"
    lines.append(f"Об'єм: {vol_e} {a['vol_ratio']:.2f}x")
    
    if a["div_w"]:
        dc = a["div_w"]["count"]
        lines.append(f"🔥 Сигнал: тижнева дивергенція ({dc}x) — ${a['div_w']['entry']:,.2f} → ${a['price']:,.2f}")
    if a["div_d"]:
        dc = a["div_d"]["count"]
        lines.append(f"🔥 Сигнал: денна дивергенція ({dc}x) — ${a['div_d']['entry']:,.2f} → ${a['price']:,.2f}")
    
    r_str = " | ".join([f"R{i+1} ${r['price']:,.0f} ({r['touches']}x)" for i, r in enumerate(a["sr"]["resistance"][:3])])
    s_str = " | ".join([f"S{i+1} ${s['price']:,.0f} ({s['touches']}x)" for i, s in enumerate(a["sr"]["support"][:3])])
    if r_str:
        lines.append(f"🔺 Опір: {r_str}")
    if s_str:
        lines.append(f"🔻 Підтр: {s_str}")
    lines.append("")
    
    # ── PENGU ──
    a = asset_analysis("PENGUUSDT")
    lines.append(f"━━━ 🐧 PENGU — ${a['price']:,.4f} ━━━")
    trend_e = "🟢" if a["trend"] == "BULLISH" else "🔴"
    lines.append(f"Тренд: {trend_e} {a['trend']} вище MA200 (${a['ma200']:,.4f}, {a['pct_ma200']:+.1f}%)")
    if a["cross"] == "GOLDEN_CROSS":
        lines.append(f"🟢 GOLDEN CROSS — MA50 перетнула MA200 вгору! Бичачий сигнал.")
    elif a["cross"] == "DEATH_CROSS":
        lines.append(f"🔴 DEATH CROSS — MA50 нижче MA200, ведмежий перетин")
    elif a["ma50"] > a["ma200"]:
        lines.append(f"MA50: ${a['ma50']:,.4f} 🟢 Вище MA200")
    else:
        lines.append(f"MA50: ${a['ma50']:,.4f} 🔴 Нижче MA200")
    
    vol_e = "📈" if a["vol_ratio"] > 1.5 else "📊" if a["vol_ratio"] > 0.5 else "📉"
    lines.append(f"Об'єм: {vol_e} {a['vol_ratio']:.2f}x")
    
    if a["div_w"]:
        dc = a["div_w"]["count"]
        lines.append(f"🔥 Сигнал: тижнева дивергенція ({dc}x) — ${a['div_w']['entry']:,.4f} → ${a['price']:,.4f}")
    if a["div_d"]:
        dc = a["div_d"]["count"]
        lines.append(f"🔥 Сигнал: денна дивергенція ({dc}x) — ${a['div_d']['entry']:,.4f} → ${a['price']:,.4f}")
    
    r_str = " | ".join([f"R{i+1} ${r['price']:,.4f} ({r['touches']}x)" for i, r in enumerate(a["sr"]["resistance"][:3])])
    s_str = " | ".join([f"S{i+1} ${s['price']:,.4f} ({s['touches']}x)" for i, s in enumerate(a["sr"]["support"][:3])])
    if r_str:
        lines.append(f"🔺 Опір: {r_str}")
    if s_str:
        lines.append(f"🔻 Підтр: {s_str}")
    lines.append("")
    
    # ── MACRO VERDICT ──
    lines.append("━"*30)
    lines.append("🧠 МАКРО-ВЕРДИКТ:")
    
    btc_a = asset_analysis("BTCUSDT")
    eth_a = asset_analysis("ETHUSDT")
    sol_a = asset_analysis("SOLUSDT")
    pengu_a = asset_analysis("PENGUUSDT")
    
    bullish_count = sum(1 for a in [btc_a, eth_a, sol_a, pengu_a] if a["trend"] == "BULLISH")
    signal_count = sum(1 for a in [btc_a, eth_a, sol_a, pengu_a] if a["div_w"] or a["div_d"])
    
    if bullish_count >= 3 and signal_count >= 2:
        lines.append("🟢 RISK-ON: Більшість активів у бичачому тренді. Сигнали підтверджують.")
        lines.append("Рекомендація: концентрація на сильних сигналах. Шукати точки входу.")
    elif bullish_count >= 2:
        lines.append("🟡 TRANSITION: Змішані сигнали. Ринок обирає напрямок.")
        lines.append("Рекомендація: дрібні проби, чекати підтвердження.")
    else:
        lines.append("🔴 RISK-OFF: Більшість активів нижче MA200. Оборона.")
        lines.append("Рекомендація: кеш, хеджі, чекати.")
    
    lines.append("")
    lines.extend(["━"*30, "🦊 CryptoFox — t.me/cryprofoxs", "#CryptoFox #TradingSignals #BTC #ETH #SOL #PENGU"])
    return "\n".join(lines)


def generate_x_post():
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = [f"🦊 #CryptoFox Daily — {now}", ""]
    
    regime = regime_classification()
    lines.append(f"Regime: {regime}")
    lines.append("")
    
    btc_a = asset_analysis("BTCUSDT")
    btc_p = btc_a["price"]
    lines.append(f"BTC ${btc_p:,.0f} | MA200 ${btc_a['ma200']:,.0f} | {btc_a['trend']} {btc_a['pct_ma200']:+.1f}%")
    if btc_a["div_w"]:
        lines.append(f"Weekly divergence {btc_a['div_w']['count']}x — entry ${btc_a['div_w']['entry']:,.0f}")
    lines.append("")
    
    for sym in CORE:
        a = asset_analysis(sym)
        name = a["name"]
        if name == "BTC":
            continue  # already done
        lines.append(f"${name}: {a['trend']} | MA200 ${a['ma200']:,.2f} | {a['pct_ma200']:+.1f}%")
        if a["div_w"]:
            lines.append(f"  Weekly div {a['div_w']['count']}x (entry ${a['div_w']['entry']:,.2f})")
        if a["div_d"]:
            lines.append(f"  Daily div {a['div_d']['count']}x (entry ${a['div_d']['entry']:,.2f})")
    
    lines.append("")
    lines.extend(["#Crypto #Trading #BTC #Macro", "t.me/cryprofoxs"])
    return "\n".join(lines)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "x"
    if mode == "check":
        print(generate_daily_check())
    elif mode == "x":
        print(generate_x_post())
    elif mode == "tg":
        print(generate_tg_post())
    else:
        print("=== X ===")
        print(generate_x_post())
        print()
        print("=== TG ===")
        print(generate_tg_post())
