# Heartbeat tasks — run every 12h (0:00 and 12:00 UTC)

## Daily market scan (1d/1w)
Run: python3 /home/node/.openclaw/workspace/ta.py
Task: Scan all available Binance assets for MACD divergence + AO confirmation on 1d and 1w timeframes.
Output: If divergence found, notify Lumier with signal.
Priority: high