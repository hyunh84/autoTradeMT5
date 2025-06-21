
# Ichimoku-based Trading Strategy
# Timeframe: 60-minute
# Pip Size: 0.01, Entry Offset: ±4 pip → 0.04
# Indicators used: Ichimoku Cloud

import MetaTrader5 as mt5

def calculate_ichimoku(data):
    high_prices = [x.high for x in data]
    low_prices = [x.low for x in data]
    close_prices = [x.close for x in data]

    conversion = [(max(high_prices[i-9:i]) + min(low_prices[i-9:i])) / 2 if i >= 9 else None for i in range(len(data))]
    base = [(max(high_prices[i-26:i]) + min(low_prices[i-26:i])) / 2 if i >= 26 else None for i in range(len(data))]
    span1 = [(conversion[i] + base[i]) / 2 if conversion[i] and base[i] else None for i in range(len(data))]
    span2 = [(max(high_prices[i-52:i]) + min(low_prices[i-52:i])) / 2 if i >= 52 else None for i in range(len(data))]

    return conversion, base, span1, span2

def is_bullish_cloud(span1_26, span2_26):
    return span1_26 and span2_26 and span1_26 > span2_26

def is_bearish_cloud(span1_26, span2_26):
    return span1_26 and span2_26 and span1_26 < span2_26

def check_entry(data):
    pip_size = 0.01
    offset = 0.04
    if len(data) < 100:
        return None

    conversion, base, span1, span2 = calculate_ichimoku(data)
    i = -1  # current candle
    span1_26 = span1[i - 26]
    span2_26 = span2[i - 26]
    price = data[i].close
    chiko = data[i - 26].close

    # Long conditions
    if (conversion[i-1] < base[i-1] and conversion[i] > base[i] and
        price > conversion[i] > base[i] and is_bullish_cloud(span1_26, span2_26) and
        price > max(span1_26, span2_26) and price - data[i].open >= 0.04 and
        chiko > data[i - 26].high):

        entry_price = price + offset
        tp = entry_price + 0.30
        sl = min(span1_26, span2_26)
        return ("buy", entry_price, tp, sl)

    # Short conditions
    if (conversion[i-1] > base[i-1] and conversion[i] < base[i] and
        price < conversion[i] < base[i] and is_bearish_cloud(span1_26, span2_26) and
        price < min(span1_26, span2_26) and data[i].open - price >= 0.04 and
        chiko < data[i - 26].low):

        entry_price = price - offset
        tp = entry_price - 0.30
        sl = max(span1_26, span2_26)
        return ("sell", entry_price, tp, sl)

    return None

def run_strategy(mt5, log, symbol):  # ← symbol 추가!
    mt5.symbol_select(symbol, True)
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        log(f"[{symbol}] 현재가: {tick.ask}")