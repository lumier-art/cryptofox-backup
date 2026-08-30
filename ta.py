"""
Technical Analysis — CryptoFox framework.
MACD divergence (1d/1w only) + AO confirmation + Volume + MA trend filter.

Priority system:
  P1: Weekly breakout signal (regular divergence + first AO bar + breakout)
  P2: Daily breakout signal (regular divergence + first AO bar + breakout)
  P3: Volume & trend health (confirmation / exhaustion)
  P4: MA50/MA200 trend (golden/death cross)
"""

import sys
import json
import urllib.request
import math

BINANCE_API = "https://api.binance.com/api/v3/klines"

def fetch_klines(symbol, interval="1d", limit=200):
    url = f"{BINANCE_API}?symbol={symbol}&interval={interval}&limit={limit}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    closes = [float(k[4]) for k in data]
    highs = [float(k[2]) for k in data]
    lows = [float(k[1]) for k in data]
    volumes = [float(k[5]) for k in data]
    return closes, highs, lows, volumes


def sma(data, period):
    if len(data) < period:
        return None
    return sum(data[-period:]) / period


def ema(data, period):
    if len(data) < period:
        return None
    multiplier = 2 / (period + 1)
    result = sum(data[:period]) / period
    for price in data[period:]:
        result = (price - result) * multiplier + result
    return result


def rsi(data, period=14):
    if len(data) < period + 1:
        return None
    gains, losses = 0, 0
    for i in range(-period, 0):
        diff = data[i] - data[i - 1]
        if diff > 0:
            gains += diff
        else:
            losses -= diff
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def bb(data, period=20, std_dev=2):
    if len(data) < period:
        return None, None, None
    recent = data[-period:]
    mean = sum(recent) / period
    variance = sum((x - mean) ** 2 for x in recent) / period
    sd = math.sqrt(variance)
    upper = mean + std_dev * sd
    lower = mean - std_dev * sd
    return upper, mean, lower


def macd_line(data, fast=12, slow=26):
    if len(data) < slow:
        return None
    fast_ema = ema(data, fast)
    slow_ema = ema(data, slow)
    if fast_ema is None or slow_ema is None:
        return None
    return fast_ema - slow_ema


def macd_full(data, fast=12, slow=26, signal=9):
    if len(data) < slow + signal:
        return None, None, None
    macd_values = []
    for i in range(slow, len(data) + 1):
        chunk = data[:i]
        m = macd_line(chunk, fast, slow)
        if m is not None:
            macd_values.append(m)
    if len(macd_values) < signal:
        return None, None, None
    sig = ema(macd_values, signal)
    hist = macd_values[-1] - sig
    return macd_values[-1], sig, hist


def awesome_oscillator_full(highs, lows, fast=5, slow=34):
    if len(highs) < slow:
        return None, None
    median = [(highs[i] + lows[i]) / 2 for i in range(len(highs))]
    fast_sum = sum(median[-fast:]) / fast
    slow_sum = sum(median[-slow:]) / slow
    ao = fast_sum - slow_sum
    fast_prev = sum(median[-(fast + 1):-1]) / fast
    slow_prev = sum(median[-(slow + 1):-1]) / slow
    ao_prev = fast_prev - slow_prev
    return ao, ao_prev


def find_macd_divergence(prices, macd_values):
    result = {"type": None, "status": "none", "strength": 0}
    if len(prices) < 60 or len(macd_values) < 60:
        return result

    price_lows = []
    price_highs = []
    macd_lows = []
    macd_highs = []
    lookback = min(60, len(prices) - 1)

    for i in range(-lookback, -1):
        if prices[i] < prices[i - 1] and prices[i] < prices[i + 1]:
            price_lows.append((i, prices[i]))
            macd_lows.append((i, macd_values[i]))
        if prices[i] > prices[i - 1] and prices[i] > prices[i + 1]:
            price_highs.append((i, prices[i]))
            macd_highs.append((i, macd_values[i]))

    if len(price_lows) < 2 or len(price_highs) < 2:
        return result

    # Bullish divergence
    last_two_lows = price_lows[-2:]
    last_two_macd_lows = macd_lows[-2:]
    if len(last_two_lows) == 2 and len(last_two_macd_lows) == 2:
        p0, p1 = last_two_lows[0][1], last_two_lows[1][1]
        m0, m1 = last_two_macd_lows[0][1], last_two_macd_lows[1][1]
        if p1 < p0 and m1 > m0:
            result["type"] = "bullish"
            result["status"] = "active"
            result["strength"] = min(1.0, abs((p0 - p1) / p0) * 5)
            return result
        if p1 > p0 and m1 > m0:
            result["type"] = "bullish_hidden"
            result["status"] = "forming"
            result["strength"] = 0.5
            return result

    # Bearish divergence
    last_two_highs = price_highs[-2:]
    last_two_macd_highs = macd_highs[-2:]
    if len(last_two_highs) == 2 and len(last_two_macd_highs) == 2:
        p0, p1 = last_two_highs[0][1], last_two_highs[1][1]
        m0, m1 = last_two_macd_highs[0][1], last_two_macd_highs[1][1]
        if p1 > p0 and m1 < m0:
            result["type"] = "bearish"
            result["status"] = "active"
            result["strength"] = min(1.0, abs((p1 - p0) / p0) * 5)
            return result
        if p1 < p0 and m1 < m0:
            result["type"] = "bearish_hidden"
            result["status"] = "forming"
            result["strength"] = 0.5
            return result

    return result


def find_local_minima(data, window=3):
    minima = []
    for i in range(1, len(data) - 1):
        left = data[max(0, i-window):i]
        right = data[i+1:min(len(data), i+window+1)]
        if data[i] < min(left) and data[i] <= min(right):
            minima.append(i)
    return minima


def find_local_maxima(data, window=3):
    maxima = []
    for i in range(1, len(data) - 1):
        left = data[max(0, i-window):i]
        right = data[i+1:min(len(data), i+window+1)]
        if data[i] > max(left) and data[i] >= max(right):
            maxima.append(i)
    return maxima


def _compute_ao_vals(highs, lows):
    median = [(highs[j] + lows[j]) / 2 for j in range(len(highs))]
    ao_vals = []
    for j in range(34, len(highs) + 1):
        fast_sum = sum(median[j-5:j]) / 5
        slow_sum = sum(median[j-34:j]) / 34
        ao_vals.append(fast_sum - slow_sum)
    return ao_vals


def find_breakout_signal(closes, highs, lows, macd_min=60):
    """
    Find the most recent regular bullish divergence + first AO rising bar.
    Returns dict with signal info or None.
    macd_min: minimum MACD values needed (60 for daily, 30 for weekly)
    """
    macd_values = []
    for i in range(26, len(closes) + 1):
        m = macd_line(closes[:i], 12, 26)
        if m is not None:
            macd_values.append(m)
    if len(macd_values) < macd_min:
        return None

    offset = len(closes) - len(macd_values)

    for i in range(len(closes) - 1, max(60, len(closes) - 60) - 1, -1):
        mi = i - offset
        if mi < 2 or mi >= len(macd_values):
            continue

        p_slice = closes[:i+1]
        p_minima = find_local_minima(p_slice, 3)

        if len(p_minima) < 2:
            continue

        # Check for regular bullish divergences across ALL minima
        # Count how many pairs (not necessarily consecutive) form regular bullish div
        # Hidden div bars between them do NOT invalidate the count
        regular_div_count = 0
        div_prices_list = []
        div_macd_list = []
        last_regular_div_low = None
        last_regular_div_macd = None

        # Scan all minima pairs and count regular bullish divergences
        # Also track the most recent one for the signal
        for idx in range(1, len(p_minima)):
            p0_i = p_minima[idx - 1]
            p1_i = p_minima[idx]
            m0_i = p0_i - offset
            m1_i = p1_i - offset

            if m0_i < 0 or m1_i < 0 or m0_i >= len(macd_values) or m1_i >= len(macd_values):
                continue

            p0 = closes[p0_i]
            p1 = closes[p1_i]
            m0 = macd_values[m0_i]
            m1 = macd_values[m1_i]

            if p1 < p0 and m1 > m0:
                # Regular bullish divergence
                regular_div_count += 1
                div_prices_list.append((p0, p1))
                div_macd_list.append((m0, m1))
                last_regular_div_low = p1
                last_regular_div_low_idx = p1_i
                last_regular_div_macd = (m0, m1)
                last_regular_div_prices = (p0, p1)

        if regular_div_count < 1:
            continue

        # Use the most recent regular divergence pair for the signal
        p0_i = last_regular_div_low_idx
        p1_i = last_regular_div_low_idx
        # Find the actual minima pair for the last regular divergence
        # Scan backwards to find the complete pair
        p0, p1 = last_regular_div_prices
        m0, m1 = last_regular_div_macd
        p1_i = last_regular_div_low_idx
        # Find p0_i (the previous low in the pair)
        for idx in range(1, len(p_minima)):
            if p_minima[idx] == p1_i:
                p0_i = p_minima[idx - 1]
                break

        ao_vals = _compute_ao_vals(highs, lows)
        if len(ao_vals) < 2:
            continue

        ao_offset = len(closes) - len(ao_vals)

        for j in range(p1_i + 1, min(p1_i + 15, len(closes))):
            aj = j - ao_offset
            if aj < 1 or aj >= len(ao_vals):
                continue

            ao = ao_vals[aj]
            ao_prev = ao_vals[aj - 1]

            if aj >= 2:
                ao_prev2 = ao_vals[aj - 2]
                is_first_rising = ao_prev <= ao_prev2 and ao > ao_prev
            else:
                is_first_rising = ao > ao_prev

            if not is_first_rising:
                continue

            signal_high = highs[j]
            signal_close = closes[j]
            stop_price = min(p1, lows[j]) * 0.995
            current_price = closes[-1]
            broke_out = any(highs[k] > signal_high for k in range(j + 1, len(closes)))

            entry_bar = None
            if broke_out:
                for k in range(j + 1, len(closes)):
                    if highs[k] >= signal_high:
                        entry_bar = k
                        break

            result = {
                "found": True,
                "signal_bar": j,
                "signal_close": signal_close,
                "signal_high": signal_high,
                "stop_price": stop_price,
                "div_low": p1,
                "div_low_idx": p1_i,
                "div_macd": (m0, m1),
                "div_prices": (p0, p1),
                "div_count": regular_div_count,
                "div_prices_list": div_prices_list,
                "div_macd_list": div_macd_list,
                "ao_val": ao,
                "ao_prev": ao_prev,
                "above_high": current_price > signal_high,
                "broke_out": broke_out,
                "entry_bar": entry_bar,
            }
            return result

    return None


def _print_breakout_signal(bs, closes, label, current_price):
    """Helper to print a formatted breakout signal block."""
    if bs and bs["found"]:
        div_count = bs.get("div_count", 1)
        if div_count >= 3:
            strength = f"⭐ TRIPLE DIVERGENCE ({div_count}x)"
            emoji = "🔥🔥🔥"
        elif div_count == 2:
            strength = f"⭐ DOUBLE DIVERGENCE"
            emoji = "🔥🔥"
        else:
            strength = "Regular"
            emoji = "🟢"

        print(f"  {emoji} {strength} DETECTED ({label})")
        print(f"      Total regular bullish divergences: {div_count}")
        print(f"")
        if div_count > 1:
            print(f"  📋 Divergence sequence (oldest → latest):")
            for idx, (pp, mm) in enumerate(zip(bs.get('div_prices_list', []), bs.get('div_macd_list', []))):
                arrow = " ← latest" if idx + 1 == len(bs.get('div_prices_list', [])) else ""
                print(f"     #{idx+1}: ${pp[0]:>8,.2f} → ${pp[1]:>8,.2f} | MACD: {mm[0]:.2f} → {mm[1]:.2f}{arrow}")
            print(f"")

        print(f"     Most recent pair: ${bs['div_prices'][0]:,.2f} → ${bs['div_prices'][1]:,.2f} (lower low)")
        print(f"     MACD: {bs['div_macd'][0]:.2f} → {bs['div_macd'][1]:.2f} (higher low)")
        print(f"")
        print(f"  📊 Signal Candle (First AO Rising Bar):")
        print(f"     Close: ${bs['signal_close']:,.2f}")
        print(f"     High:  ${bs['signal_high']:,.2f}  ← breakout level")
        print(f"     AO: {bs['ao_prev']:.2f} → {bs['ao_val']:.2f} (started rising)")
        print(f"")
        print(f"  🎯 Entry: Break above ${bs['signal_high']:,.2f}")
        print(f"  🛑 Stop:  Below ${bs['stop_price']:,.2f}")
        print(f"")
        if bs["broke_out"]:
            pnl_pct = (current_price / bs['signal_high'] - 1) * 100
            print(f"  ✅ ALREADY BROKE OUT {'✅' if pnl_pct > 0 else '❌'}")
            print(f"     Run-up: {pnl_pct:+.1f}% from entry")
        else:
            print(f"  ⏳ WAITING — price hasn't broken signal high yet")
            print(f"     Current: ${current_price:,.2f} vs Signal High: ${bs['signal_high']:,.2f}")
            dist = (bs['signal_high'] / current_price - 1) * 100
            if dist > 0:
                print(f"     Need +{dist:.1f}% to trigger")
    else:
        print(f"  No active breakout signal")
        print(f"  (Wait for regular bullish divergence + first AO rising bar)")


def analyze(symbol, interval="1d", limit=200):
    print(f"\n{'='*60}")
    print(f"  CryptoFox Analysis — {symbol} ({interval})")
    print(f"{'='*60}")

    try:
        closes, highs, lows, volumes = fetch_klines(symbol, interval, limit)
    except Exception as e:
        print(f"  ERROR fetching data: {e}")
        return

    if len(closes) < 60:
        print(f"  ERROR: Not enough data ({len(closes)} bars)")
        return

    current_price = closes[-1]
    current_vol = volumes[-1]
    print(f"\n  Current Price: ${current_price:,.2f}")

    # --- MOVING AVERAGES (Trend Layer) ---
    print(f"\n  ─── MOVING AVERAGES (Trend Filter) ───")
    current_ma50 = ema(closes, 50)
    current_ma200 = ema(closes, 200)

    if current_ma50:
        print(f"  MA50:  ${current_ma50:,.2f}  ({'ABOVE' if current_price > current_ma50 else 'BELOW'})")
    if current_ma200:
        print(f"  MA200: ${current_ma200:,.2f}  ({'ABOVE' if current_price > current_ma200 else 'BELOW'})")

    ma_trend = "NEUTRAL"
    if current_ma50 and current_ma200:
        if current_price > current_ma50 and current_ma50 > current_ma200:
            ma_trend = "BULLISH (50 > 200)"
        elif current_price < current_ma50 and current_ma50 < current_ma200:
            ma_trend = "BEARISH (50 < 200)"
        elif current_price > current_ma50 and current_price > current_ma200:
            ma_trend = "BULLISH-BIAS (above both)"
        elif current_price < current_ma50 and current_price < current_ma200:
            ma_trend = "BEARISH-BIAS (below both)"
        else:
            ma_trend = "MIXED (between MAs)"
    print(f"  Trend: {ma_trend}")

    if current_ma50:
        dist_pct = (current_price - current_ma50) / current_ma50 * 100
        print(f"  Distance from MA50: {dist_pct:+.2f}%")
        if abs(dist_pct) > 20:
            print(f"  ⚠️  Overextended from MA50 ({abs(dist_pct):.1f}% > 20%)")

    # --- BOLLINGER BANDS ---
    print(f"\n  ─── BOLLINGER BANDS ───")
    bb_upper, bb_mid, bb_lower = bb(closes, 20, 2)
    if bb_upper:
        print(f"  Upper: ${bb_upper:,.2f}")
        print(f"  Mid:   ${bb_mid:,.2f}")
        print(f"  Lower: ${bb_lower:,.2f}")
        if current_price >= bb_upper:
            print(f"  ⚠️  Price at/above upper band — extended")
        elif current_price <= bb_lower:
            print(f"  Price at/below lower band — potential bounce")

    # --- MACD DIVERGENCE ---
    print(f"\n  ─── MACD DIVERGENCE ───")
    current_macd, current_sig, current_hist = macd_full(closes, 12, 26, 9)
    if current_macd is not None:
        print(f"  MACD: {current_macd:.4f}")
        print(f"  Signal: {current_sig:.4f}")
        print(f"  Histogram: {current_hist:.4f} ({'POSITIVE' if current_hist > 0 else 'NEGATIVE'})")

        macd_values = []
        for i in range(26, len(closes) + 1):
            m = macd_line(closes[:i], 12, 26)
            if m is not None:
                macd_values.append(m)
        if len(macd_values) >= 60:
            div = find_macd_divergence(closes, macd_values)
            if div["type"]:
                emoji = "🟢" if "bullish" in div["type"] else "🔴"
                print(f"  {emoji} Divergence: {div['type'].upper()} ({div['status']})")
                print(f"  Strength: {div['strength']:.2f}")
            else:
                print(f"  No divergence detected")

    # --- AWESOME OSCILLATOR ---
    print(f"\n  ─── AWESOME OSCILLATOR ───")
    ao, ao_prev = awesome_oscillator_full(highs, lows, 5, 34)
    if ao is not None:
        print(f"  AO: {ao:.4f}")
        if ao_prev is not None:
            print(f"  AO Prev: {ao_prev:.4f}")
            if ao > 0 and ao_prev > 0:
                if ao > ao_prev:
                    print(f"  AO Saucer: BULLISH (green, rising)")
                else:
                    print(f"  AO Saucer: BEARISH (green, falling)")
            elif ao < 0 and ao_prev < 0:
                if ao < ao_prev:
                    print(f"  AO Saucer: BEARISH (red, falling)")
                else:
                    print(f"  AO Saucer: BULLISH (red, rising)")
            else:
                print(f"  AO: crossing zero line")

    # --- VOLUME ---
    print(f"\n  ─── VOLUME ───")
    avg_vol = sum(volumes[-50:]) / 50
    vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1
    print(f"  Current Volume: {current_vol:,.0f}")
    print(f"  Avg Volume (50): {avg_vol:,.0f}")
    print(f"  Volume Ratio: {vol_ratio:.2f}x")
    if vol_ratio > 1.5:
        print(f"  ⚠️  Elevated volume")
    elif vol_ratio < 0.5:
        print(f"  Low volume")

    # --- SUPPORT / RESISTANCE ---
    print(f"\n  ─── SUPPORT / RESISTANCE ───")
    lookback = min(100, len(lows))
    recent_lows = sorted(lows[-lookback:])
    recent_highs = sorted(highs[-lookback:], reverse=True)
    support_levels = []
    resistance_levels = []
    for l in recent_lows[:5]:
        if l < current_price:
            support_levels.append(l)
    for h in recent_highs[:5]:
        if h > current_price:
            resistance_levels.append(h)
    if support_levels:
        for s in sorted(set(round(x) for x in support_levels), reverse=True)[:3]:
            print(f"  Support: ${s:,.0f}")
    if resistance_levels:
        for r in sorted(set(round(x) for x in resistance_levels))[:3]:
            print(f"  Resistance: ${r:,.0f}")

    # ====================================================================
    # 🔥 PRIORITY SIGNAL SUMMARY
    # ====================================================================
    print(f"\n{'='*60}")
    print(f"  🔥 PRIORITY SIGNAL SUMMARY")
    print(f"{'-'*60}")

    # ─── BTC CONTEXT (market leader check) ───
    if symbol != "BTCUSDT":
        print(f"\n  ═══ BTC CONTEXT (MARKET LEADER) ═══")
        print(f"  (BTC divergences amplify altcoin signals)")
        try:
            b_closes, b_highs, b_lows, _ = fetch_klines("BTCUSDT", "1d", 200)
            b_weekly = None
            try:
                bw_closes, bw_highs, bw_lows, _ = fetch_klines("BTCUSDT", "1w", 200)
                b_weekly = find_breakout_signal(bw_closes, bw_highs, bw_lows, macd_min=30)
            except:
                pass
            b_daily = find_breakout_signal(b_closes, b_highs, b_lows)

            btc_weekly_active = b_weekly is not None and not b_weekly.get("broke_out", False)
            btc_weekly_triggered = b_weekly is not None and b_weekly.get("broke_out", False)
            btc_daily_active = b_daily is not None and not b_daily.get("broke_out", False)
            btc_daily_triggered = b_daily is not None and b_daily.get("broke_out", False)

            if btc_weekly_active or btc_weekly_triggered:
                print(f"  🟢 BTC Weekly breakout signal {'ACTIVE' if btc_weekly_active else 'TRIGGERED'} — BULLISH BIAS")
                print(f"     This amplifies all altcoin signals (liquidity flow)")
            elif btc_daily_active or btc_daily_triggered:
                print(f"  🟢 BTC Daily breakout signal {'ACTIVE' if btc_daily_active else 'TRIGGERED'} — positive context")
            else:
                # Check if BTC has any divergence forming (even without first AO bar)
                b_macd = []
                for i in range(26, len(b_closes) + 1):
                    m = macd_line(b_closes[:i], 12, 26)
                    if m is not None: b_macd.append(m)
                if len(b_macd) >= 60:
                    b_div = find_macd_divergence(b_closes, b_macd)
                    if b_div["type"] and "bullish" in b_div["type"]:
                        print(f"  🟡 BTC has {b_div['type']} divergence forming — altcoins may benefit")
                    else:
                        print(f"  ⚪ BTC has no active divergence — altcoins need own strong signal")
                else:
                    print(f"  ⚪ BTC data insufficient")

            btc_price = b_closes[-1]
            print(f"  BTC current: ${btc_price:,.2f}")
        except Exception as e:
            print(f"  ⚠️  Could not fetch BTC data: {e}")
    else:
        print(f"\n  ═══ BTC CONTEXT ═══")
        print(f"  (This is BTC itself — analyzing as primary asset)")

    # ─── P1: WEEKLY BREAKOUT ───
    print(f"\n  ═══ PRIORITY 1: WEEKLY ═══")
    print(f"  (regular divergence + first AO bar + breakout)")
    if interval == "1w":
        wbs = find_breakout_signal(closes, highs, lows, macd_min=30)
        _print_breakout_signal(wbs, closes, "WEEKLY", current_price)
    else:
        try:
            w_closes, w_highs, w_lows, _ = fetch_klines(symbol, "1w", 200)
            wbs = find_breakout_signal(w_closes, w_highs, w_lows, macd_min=30)
            _print_breakout_signal(wbs, w_closes, "WEEKLY", w_closes[-1])
        except Exception as e:
            print(f"  ⚠️  Could not fetch weekly data: {e}")

    # ─── P2: DAILY BREAKOUT ───
    print(f"\n  ═══ PRIORITY 2: DAILY ═══")
    print(f"  (regular divergence + first AO bar + breakout)")
    bs = find_breakout_signal(closes, highs, lows)
    _print_breakout_signal(bs, closes, "DAILY", current_price)

    # ─── P3: VOLUME & TREND HEALTH ───
    print(f"\n  ═══ PRIORITY 3: VOLUME & TREND HEALTH ═══")
    print(f"  (confirms trend / warns of exhaustion)")
    avg_vol_50 = sum(volumes[-50:]) / 50
    vol_ratio = current_vol / avg_vol_50 if avg_vol_50 > 0 else 0
    print(f"  Volume ratio: {vol_ratio:.2f}x avg")

    vol_short = sum(volumes[-10:]) / 10
    vol_longer = sum(volumes[-20:-10]) / 10 if len(volumes) >= 20 else 0
    vol_trend = ""
    if vol_longer > 0:
        vol_change = (vol_short / vol_longer - 1) * 100
        vol_trend = f" (last 10 bars {vol_change:+.1f}% vs prior 10)"

    if vol_ratio > 1.5:
        print(f"  🟢 Elevated volume — trend healthy{vol_trend}")
    elif vol_ratio > 0.8:
        print(f"  🟡 Normal volume{vol_trend}")
    elif vol_ratio > 0.5:
        print(f"  🟡 Below avg — low participation{vol_trend}")
    else:
        print(f"  🔴 Low volume — weak conviction, may exhaust{vol_trend}")

    # Volume exhaustion check
    if len(volumes) >= 30:
        recent_10 = sum(volumes[-10:]) / 10
        prior_20 = sum(volumes[-30:-10]) / 20
        if prior_20 > 0:
            exhaustion = recent_10 / prior_20
            if exhaustion < 0.6:
                print(f"  ⚠️  Volume dropping significantly ({exhaustion:.1f}x vs prev 20)")
                print(f"     Trend exhausting — tight stops warranted")
            elif exhaustion < 0.8:
                print(f"  👀 Volume declining ({exhaustion:.1f}x vs prev 20)")

    # AO momentum check
    if ao is not None and ao_prev is not None:
        if ao < 0 and ao > ao_prev:
            print(f"  📈 AO rising from negative — momentum building")
        elif ao > 0 and ao < ao_prev:
            print(f"  📉 AO falling from positive — momentum fading")

    # Hidden divergence + volume = pyramiding signal
    if div is not None and div.get("type") == "bullish_hidden":
        if vol_ratio > 1.0:
            print(f"  🏗️ Hidden divergence + elevated volume — pyramiding opportunity")
            print(f"     (add to existing position if in an active trend)")
        elif vol_ratio > 0.5:
            print(f"  👀 Hidden divergence detected — but volume low ({vol_ratio:.2f}x)")
            print(f"     (wait for volume confirmation before pyramiding)")

    # ─── P4: MA50/MA200 TREND ───
    print(f"\n  ═══ PRIORITY 4: MA50/MA200 TREND ═══")
    print(f"  (golden cross / death cross / alignment)")
    if current_ma50 and current_ma200:
        print(f"  MA50:  ${current_ma50:,.2f}")
        print(f"  MA200: ${current_ma200:,.2f}")
        print(f"  Distance from MA50: {dist_pct:+.2f}%")

        if len(closes) >= 201:
            prev_ma50 = ema(closes[:-1], 50)
            prev_ma200 = ema(closes[:-1], 200)
            if prev_ma50 and prev_ma200:
                if prev_ma50 <= prev_ma200 and current_ma50 > current_ma200:
                    print(f"  🟢 GOLDEN CROSS — MA50 crossed above MA200!")
                elif prev_ma50 >= prev_ma200 and current_ma50 < current_ma200:
                    print(f"  🔴 DEATH CROSS — MA50 crossed below MA200!")
                elif current_ma50 > current_ma200:
                    print(f"  🟢 MA50 > MA200 — bullish alignment")
                    print(f"     Spread: ${current_ma50 - current_ma200:,.2f}")
                else:
                    print(f"  🔴 MA50 < MA200 — bearish alignment")
                    print(f"     Spread: ${current_ma50 - current_ma200:,.2f}")

        if abs(dist_pct) > 20:
            print(f"  ⚠️  Overextended from MA50 ({abs(dist_pct):.1f}%)")
    else:
        print(f"  Insufficient data")

    print(f"\n{'='*60}\n")


def find_support_resistance(highs, lows, closes, lookback=120, min_touches=3, cluster_pct=0.015):
    """
    Find key support and resistance levels from candle data.
    
    Args:
        highs: list of high prices (most recent last)
        lows: list of low prices (most recent last)
        closes: list of close prices (most recent last)
        lookback: number of candles to analyze (default 100)
        min_touches: minimum touches for a level (default 1)
        cluster_pct: merge levels within this %% distance (default 1.5%%)
    
    Returns:
        dict with 'support' and 'resistance' lists of sorted levels
    """
    if len(highs) < lookback:
        lookback = len(highs) - 1
    
    h = highs[-lookback:]
    l = lows[-lookback:]
    c = closes[-lookback:]
    current_price = c[-1]
    
    # Find swing highs (resistance) — local maxima with 3-bar window
    swing_highs = []
    for i in range(2, len(h) - 2):
        if h[i] > h[i-1] and h[i] > h[i-2] and h[i] >= h[i+1] and h[i] >= h[i+2]:
            swing_highs.append(h[i])
    
    # Find swing lows (support) — local minima with 3-bar window
    swing_lows = []
    for i in range(2, len(l) - 2):
        if l[i] < l[i-1] and l[i] < l[i-2] and l[i] <= l[i+1] and l[i] <= l[i+2]:
            swing_lows.append(l[i])
    
    # Also add long wicks (rejection from a level)
    for i in range(1, len(c) - 1):
        upper_wick = h[i] - max(c[i], c[i-1])
        lower_wick = min(c[i], c[i-1]) - l[i]
        body = abs(c[i] - c[i-1])
        if body > 0 and upper_wick > body * 2.0:
            swing_highs.append(h[i])
        if body > 0 and lower_wick > body * 2.0:
            swing_lows.append(l[i])
    
    def cluster_levels(values, pct):
        if not values:
            return []
        sorted_vals = sorted(values)
        clusters = [[sorted_vals[0]]]
        for v in sorted_vals[1:]:
            if abs(v - clusters[-1][0]) / clusters[-1][0] < pct:
                clusters[-1].append(v)
            else:
                clusters.append([v])
        result = []
        for cl in clusters:
            if len(cl) >= min_touches:
                result.append({
                    "price": round(sum(cl) / len(cl), 2),
                    "touches": len(cl)
                })
        return result
    
    resistances = cluster_levels(swing_highs, cluster_pct)
    supports = cluster_levels(swing_lows, cluster_pct)
    
    # Filter: resistance above current, support below current
    # Keep only nearest 5 on each side, sorted by distance
    resistances = sorted([r for r in resistances if r["price"] > current_price], key=lambda x: x["price"])[:5]
    supports = sorted([s for s in supports if s["price"] < current_price], key=lambda x: -x["price"])[:5]
    
    return {
        "support": supports,
        "resistance": resistances,
        "current_price": current_price
    }


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sr":
        sym = sys.argv[2] if len(sys.argv) > 2 else "BTCUSDT"
        c, h, l, v = fetch_klines(sym, "1d", 150)
        sr = find_support_resistance(h, l, c)
        print(f"\n{'='*60}")
        print(f"  SUPPORT & RESISTANCE — {sym}")
        print(f"  Current: \${sr['current_price']:,.2f}")
        print(f"{'='*60}")
        print(f"\n  RESISTANCE:")
        for i, r in enumerate(sr['resistance'][:5], 1):
            dist = (r['price'] / sr['current_price'] - 1) * 100
            print(f"    R{i}: \${r['price']:,.2f}  ({dist:+.2f}%)  [{r['touches']} торк.]")
        print(f"\n  SUPPORT:")
        for i, s in enumerate(sr['support'][:5], 1):
            dist = (s['price'] / sr['current_price'] - 1) * 100
            print(f"    S{i}: \${s['price']:,.2f}  ({dist:+.2f}%)  [{s['touches']} торк.]")
        print()
        sys.exit(0)

    sym = sys.argv[1] if len(sys.argv) > 1 else "BTCUSDT"
    iv = sys.argv[2] if len(sys.argv) > 2 else "1d"
    lim = int(sys.argv[3]) if len(sys.argv) > 3 else 200

    if iv not in ("1d", "1w"):
        print("Only 1d and 1w timeframes are supported")
        sys.exit(1)

    analyze(sym.upper(), iv, lim)
