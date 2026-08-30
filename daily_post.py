#!/usr/bin/env python3
"""
CryptoFox Daily Post Generator — generates content for Telegram & X.
Run daily at 15:00 UTC for X post, 8:00 and 20:00 MYT for Telegram.
"""

import sys
sys.path.insert(0, '/home/node/.openclaw/workspace')
import ta
from datetime import datetime, timezone

ASSETS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "AVAXUSDT", "DOGEUSDT", "LINKUSDT", "BNBUSDT", "VIRTUALUSDT"]

def get_bs(sym, tf, macd_min=60):
    c, h, l, _ = ta.fetch_klines(sym, tf, 200)
    return c, ta.find_breakout_signal(c, h, l, macd_min)

def pct(a, b):
    return (a/b - 1) * 100

def generate_daily_check():
    """
    Midnight check — 00:00 UTC
    Prices + MA200 trend + S/R levels for BTC, ETH, SOL.
    Сигнали: дивергенції (1d/1w), пересічення MA50/MA200, пробиття опору/підтримки (2+ торк.).
    Якщо сигналу немає — суха статистика.
    """
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = ["🦊 CRYPTOFOX — Щоденний огляд", f"📅 {now}", "━"*30, ""]
    
    signals_found = []
    
    for sym in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
        c, h, l, v = ta.fetch_klines(sym, "1d", 201)
        last = c[-1]
        ma50 = ta.ema(c, 50)
        ma200 = ta.ema(c, 200)
        trend = "🟢 BULLISH" if last > ma200 else "🔴 BEARISH"
        name = sym.replace("USDT", "")
        
        lines.append(f"{name}: ${last:,.2f}")
        lines.append(f"  MA200: ${ma200:,.2f} | {trend}")
        
        # ── Check MA50/MA200 cross ──
        if ma50 and ma200:
            prev_ma50 = ta.ema(c[:-1], 50) if len(c) >= 201 else None
            prev_ma200 = ta.ema(c[:-1], 200) if len(c) >= 201 else None
            if prev_ma50 and prev_ma200:
                if prev_ma50 <= prev_ma200 and ma50 > ma200:
                    signals_found.append((name, "🟢 GOLDEN CROSS (MA50×MA200)"))
                    lines.append(f"  🟢 GOLDEN CROSS — MA50 перетнула MA200 вгору!")
                elif prev_ma50 >= prev_ma200 and ma50 < ma200:
                    signals_found.append((name, "🔴 DEATH CROSS (MA50×MA200)"))
                    lines.append(f"  🔴 DEATH CROSS — MA50 перетнула MA200 вниз!")
                elif ma50 > ma200:
                    lines.append(f"  MA50: ${ma50:,.2f} 🟢 Вище MA200")
                else:
                    lines.append(f"  MA50: ${ma50:,.2f} 🔴 Нижче MA200")
        
        # ── Check NEW divergences on 1d (last 5 bars) ──
        bs_d = ta.find_breakout_signal(c, h, l)
        if bs_d and bs_d.get("broke_out"):
            entry_bar = bs_d.get("entry_bar", 0)
            if entry_bar >= len(c) - 5:
                dc = bs_d.get("div_count", 1)
                tag = "🔥🔥🔥 TRIPLE" if dc >= 3 else "🔥🔥 DOUBLE" if dc >= 2 else "🔥"
                signals_found.append((name, f"Дивергенція 1d ({dc}x)"))
                lines.append(f"  {tag} НОВА дивергенція 1d ({dc}x) — Вхід: ${bs_d['signal_high']:,.2f}")
        
        # ── Check NEW divergences on 1w ──
        cw, hw, lw, vw = ta.fetch_klines(sym, "1w", 100)
        bs_w = ta.find_breakout_signal(cw, hw, lw, 30)
        if bs_w and bs_w.get("broke_out"):
            entry_bar = bs_w.get("entry_bar", 0)
            if entry_bar >= len(cw) - 3:
                dc = bs_w.get("div_count", 1)
                tag = "🔥🔥🔥 TRIPLE" if dc >= 3 else "🔥🔥 DOUBLE" if dc >= 2 else "🔥"
                signals_found.append((name, f"Дивергенція 1w ({dc}x)"))
                lines.append(f"  {tag} НОВА дивергенція 1w ({dc}x) — Вхід: ${bs_w['signal_high']:,.2f}")
        
        # ── Volume ──
        avg_v = sum(v[-50:])/50
        ratio = v[-1]/avg_v if avg_v > 0 else 0
        vol_emoji = "📈" if ratio > 1.5 else "📊" if ratio > 0.5 else "📉"
        lines.append(f"  Об'єм: {vol_emoji} {ratio:.2f}x")
        
        # ── Support & Resistance levels ──
        sr = ta.find_support_resistance(h, l, c)
        
        # Check for breakouts of strong levels (3+ touches)
        for r in sr["resistance"]:
            if r["touches"] >= 3 and last > r["price"]:
                signals_found.append((name, f"🟢 Пробиття опору ${r['price']:,.2f} ({r['touches']} торк.)"))
                lines.append(f"  🟢 ПРОБИТТЯ ОПОРУ: ${r['price']:,.2f} ({r['touches']} дотиків)")
        for s in sr["support"]:
            if s["touches"] >= 3 and last < s["price"]:
                signals_found.append((name, f"🔴 Пробиття підтримки ${s['price']:,.2f} ({s['touches']} торк.)"))
                lines.append(f"  🔴 ПРОБИТТЯ ПІДТРИМКИ: ${s['price']:,.2f} ({s['touches']} дотиків)")
        
        # Show nearest S/R levels (numbered, touches in brackets)
        r_str = " | ".join([f"R{i+1} ${r['price']:,.0f} ({r['touches']}x)" for i, r in enumerate(sr["resistance"][:3])])
        s_str = " | ".join([f"S{i+1} ${s['price']:,.0f} ({s['touches']}x)" for i, s in enumerate(sr["support"][:3])])
        if r_str:
            lines.append(f"  🔺 Опір: {r_str}")
        if s_str:
            lines.append(f"  🔻 Підтр: {s_str}")
        
        lines.append("")
    
    if signals_found:
        lines.append("━"*30)
        lines.append("📡 АКТИВНІ СИГНАЛИ:")
        for name, sig in signals_found:
            lines.append(f"  {name}: {sig}")
        lines.append("")
    else:
        lines.append("📊 Сигналів немає. Ринок спокійний.")
        lines.append("")

    lines.extend(["━"*30, "🦊 CryptoFox — t.me/cryprofoxs"])
    return "\n".join(lines)


def generate_x_post():
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = [f"🦊 #CryptoFox Daily — {now}", ""]
    
    btc_c, btc_bs = get_bs("BTCUSDT", "1w", 30)
    btc_p = btc_c[-1]
    if btc_bs:
        lines.append(f"BTC ${btc_p:,.0f} 🟢 Weekly breakout {pct(btc_p, btc_bs['signal_high']):+.1f}%")
    else:
        lines.append(f"BTC ${btc_p:,.0f} 🟡")
    lines.append("")
    
    for sym in ASSETS + ["BTCUSDT"]:
        c, bs = get_bs(sym, "1w", 30)
        if bs:
            p = c[-1]
            name = sym.replace("USDT", "")
            dc = bs.get('div_count', 1)
            tag = "🔥🔥🔥 TRIPLE" if dc >= 3 else "🔥🔥 DOUBLE" if dc >= 2 else "🔥"
            lines.append(f"{tag} {name} ${p:,.2f} {pct(p, bs['signal_high']):+.1f}%")
    
    for sym in ASSETS[:5]:
        c, bs = get_bs(sym, "1d")
        if bs:
            p = c[-1]
            name = sym.replace("USDT", "")
            dc = bs.get('div_count', 1)
            tag = "🔥🔥🔥" if dc >= 3 else "🔥🔥" if dc >= 2 else "🟠"
            lines.append(f"{tag} {name} ${p:,.2f} {pct(p, bs['signal_high']):+.1f}%")
    
    lines.extend(["", "#Crypto #Trading #BTC #Macro", "t.me/cryprofoxs"])
    return "\n".join(lines)

def generate_tg_post():
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = [f"🦊 CRYPTOFOX DAILY SCAN", f"📅 {now}", "━"*30, ""]
    
    btc_c, btc_bs = get_bs("BTCUSDT", "1w", 30)
    btc_p = btc_c[-1]
    lines.append(f"🏛️ BTC: ${btc_p:,.2f}")
    if btc_bs:
        lines.append(f"🔥 BTC Weekly: +{pct(btc_p, btc_bs['signal_high']):.1f}% від входу ${btc_bs['signal_high']:,.0f}")
    lines.append("")
    
    lines.append("🔥 P1 WEEKLY BREAKOUT:")
    found = False
    for sym in ASSETS:
        c, bs = get_bs(sym, "1w", 30)
        if bs:
            found = True
            p = c[-1]
            name = sym.replace("USDT", "")
            dc = bs.get('div_count', 1)
            tag = "🔥🔥🔥 TRIPLE" if dc >= 3 else "🔥🔥 DOUBLE" if dc >= 2 else "🟢"
            lines.append(f"  {tag}: {name} ${p:,.2f} (+{pct(p, bs['signal_high']):.1f}%)")
            lines.append(f"    Вхід: ${bs['signal_high']:,.2f} | Стоп: ${bs['stop_price']:,.2f}")
    if not found:
        lines.append("  Немає активних")
    lines.append("")
    
    lines.append("🟠 P2 DAILY BREAKOUT:")
    found = False
    for sym in ASSETS[:7]:
        c, bs = get_bs(sym, "1d")
        if bs:
            found = True
            p = c[-1]
            name = sym.replace("USDT", "")
            dc = bs.get('div_count', 1)
            tag = "🔥🔥🔥 TRIPLE" if dc >= 3 else "🔥🔥 DOUBLE" if dc >= 2 else "🟢"
            lines.append(f"  {tag}: {name} ${p:,.2f} (+{pct(p, bs['signal_high']):.1f}%)")
    if not found:
        lines.append("  Немає активних")
    lines.append("")
    
    lines.append("📊 P3 VOLUME:")
    for sym in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
        c, h, l, v = ta.fetch_klines(sym, "1d", 200)
        avg = sum(v[-50:])/50
        ratio = v[-1]/avg if avg > 0 else 0
        name = sym.replace("USDT", "")
        emoji = "🟢" if ratio > 1.5 else "🟡" if ratio > 0.5 else "🔴"
        lines.append(f"  {emoji} {name}: {ratio:.2f}x")
    lines.append("")
    
    lines.append("🔵 P4 MA50/MA200:")
    for sym in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
        c, _, _, _ = ta.fetch_klines(sym, "1d", 200)
        ma50 = ta.ema(c, 50)
        ma200 = ta.ema(c, 200)
        name = sym.replace("USDT", "")
        if ma50 and ma200:
            s = "🟢 Golden Cross" if ma50 > ma200 else "🔴"
            lines.append(f"  {name}: {s} (MA50 ${ma50:,.0f} | MA200 ${ma200:,.0f})")
    lines.append("")
    
    lines.extend(["━"*30, "🦊 CryptoFox — t.me/cryprofoxs", "#CryptoFox #TradingSignals #BTC"])
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