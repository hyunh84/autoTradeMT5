import pandas as pd
import MetaTrader5 as mt5

def run_strategy(data, log, symbol):
    """
    data가 MT5 모듈 또는 DataFrame인지에 따라 실시간 or 백테스트용으로 분기 처리
    """
    # ─────────────────────────────────────────
    # 🟡 실시간: MT5 객체로부터 데이터 수집
    # ─────────────────────────────────────────
    if isinstance(data, type(mt5)):
        rates = data.copy_rates_from_pos(symbol, data.TIMEFRAME_H1, 0, 80)
        if rates is None or len(rates) < 53:
            log("⚠️ 데이터 부족")
            return
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')

    # ─────────────────────────────────────────
    # 🔵 백테스트: 이미 전달된 DataFrame 사용
    # ─────────────────────────────────────────
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
        if len(df) < 53:
            log("⚠️ 백테스트용 데이터가 부족합니다.")
            return df  # 빈 signal 컬럼이 없는 df 반환됨

    else:
        log("❌ data는 MT5 객체 또는 DataFrame이어야 합니다.")
        return

    # === 일목균형표 계산 ===
    df['conversion'] = (df['high'].rolling(9).max() + df['low'].rolling(9).min()) / 2
    df['base'] = (df['high'].rolling(26).max() + df['low'].rolling(26).min()) / 2
    df['span1'] = (df['conversion'] + df['base']) / 2
    df['span2'] = (df['high'].rolling(52).max() + df['low'].rolling(52).min()) / 2

    # === 최근봉 기준 계산 ===
    i = len(df) - 1
    pip = 0.010
    spread = 3 * pip
    tp_pips = 15 * pip + spread

    conv = df['conversion'].iloc[i]
    conv_prev = df['conversion'].iloc[i - 1]
    base = df['base'].iloc[i]
    base_prev = df['base'].iloc[i - 1]
    span1_26ago = df['span1'].iloc[i - 26]
    span2_26ago = df['span2'].iloc[i - 26]
    kumo_high = max(span1_26ago, span2_26ago)
    kumo_low = min(span1_26ago, span2_26ago)

    high26 = df['high'].iloc[i - 26]
    low26 = df['low'].iloc[i - 26]
    open_price = df['open'].iloc[i]
    close = df['close'].iloc[i]

    # === 진입 조건 계산 ===
    bull_cross = conv > base and conv_prev <= base_prev
    bear_cross = conv < base and conv_prev >= base_prev
    conv_rising = (conv - conv_prev) >= 4 * pip
    conv_falling = (conv_prev - conv) >= 4 * pip

    long_cond = bull_cross and conv > kumo_high and base > kumo_high and close > high26 and close > conv and conv_rising
    short_cond = bear_cross and conv < kumo_low and base < kumo_low and close < low26 and close < conv and conv_falling

    # ─────────────────────────────────────────
    # 실시간: 로그 출력
    # ─────────────────────────────────────────
    if isinstance(data, type(mt5)):
        if long_cond:
            log("🟢 롱 진입 조건 만족")
            log(f"진입가: {close:.3f}, 익절 목표가: {close + tp_pips:.3f}, 손절 조건: 다음봉 시가 < {low26:.3f}")
        elif short_cond:
            log("🔴 숏 진입 조건 만족")
            log(f"진입가: {close:.3f}, 익절 목표가: {close - tp_pips:.3f}, 손절 조건: 다음봉 시가 > {high26:.3f}")
        else:
            log("➖ 진입 조건 없음")

    # ─────────────────────────────────────────
    # 백테스트: 시그널 컬럼 생성 후 반환
    # ─────────────────────────────────────────
    else:
        df["signal"] = None
        if long_cond:
            df.at[i, "signal"] = "long"
        elif short_cond:
            df.at[i, "signal"] = "short"
        else:
            df.at[i, "signal"] = "none"
        return df
