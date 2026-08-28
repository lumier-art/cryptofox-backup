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
    if mode == "x":
        print(generate_x_post())
    elif mode == "tg":
        print(generate_tg_post())
    else:
        print("=== X ===")
        print(generate_x_post())
        print()
        print("=== TG ===")
        print(generate_tg_post())