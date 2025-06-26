import numpy as np
import pandas as pd

class IchimokuBreakoutStrategy():
    def __init__(self, pip=0.010):
        self.pip = pip
        self.spread = 3 * pip
        self.tp_pips = 15 * pip + self.spread
        self.sl_pips = 15 * pip

    def calculate_ichimoku(self, df):
        df = df.copy()
        df['conversion'] = (df['high'].rolling(9).max() + df['low'].rolling(9).min()) / 2
        df['base'] = (df['high'].rolling(26).max() + df['low'].rolling(26).min()) / 2
        df['leading_span1'] = ((df['conversion'] + df['base']) / 2).shift(26)
        df['leading_span2'] = ((df['high'].rolling(52).max() + df['low'].rolling(52).min()) / 2).shift(26)
        df['kumo_high'] = df[['leading_span1', 'leading_span2']].max(axis=1)
        df['kumo_low'] = df[['leading_span1', 'leading_span2']].min(axis=1)
        df['high26'] = df['high'].shift(26)
        df['low26'] = df['low'].shift(26)
        return df

    def run(self, df, log_fn=None):
        if log_fn is None:
            log_fn = print  # fallback

        # ---- [시간대 변환 구간 추가] ----
        if not pd.api.types.is_datetime64_any_dtype(df['time']):
            df['time'] = pd.to_datetime(df['time'])
        if df['time'].dt.tz is None:
            df['time'] = df['time'].dt.tz_localize('UTC')
        df['time_local'] = df['time'].dt.tz_convert('Asia/Seoul')
        # ---- --------------------- ----

        df = self.calculate_ichimoku(df)
        df['signal'] = 0

        # --- 진입조건 계산 (NaN 구간 방지, 트레이딩뷰 타이밍 동기화!) ---
        bull_cross = (df['conversion'] > df['base']) & (df['conversion'].shift(1) <= df['base'].shift(1))
        bear_cross = (df['conversion'] < df['base']) & (df['conversion'].shift(1) >= df['base'].shift(1))
        conversion_rising = (df['conversion'] - df['conversion'].shift(1)) >= 4 * self.pip
        conversion_falling = (df['conversion'].shift(1) - df['conversion']) >= 4 * self.pip

        long_cond = (
            bull_cross &
            (df['conversion'] > df['kumo_high']) &
            (df['base'] > df['kumo_high']) &
            (df['close'] > df['high26']) &
            (df['close'] > df['conversion']) &
            conversion_rising
        )
        short_cond = (
            bear_cross &
            (df['conversion'] < df['kumo_low']) &
            (df['base'] < df['kumo_low']) &
            (df['close'] < df['low26']) &
            (df['close'] < df['conversion']) &
            conversion_falling
        )
        valid_cond = (
            df['conversion'].notnull() & df['base'].notnull() &
            df['kumo_high'].notnull() & df['kumo_low'].notnull() &
            df['high26'].notnull() & df['low26'].notnull()
        )
        long_cond &= valid_cond
        short_cond &= valid_cond

        df['signal'] = 0
        df.loc[long_cond.shift(1, fill_value=False), 'signal'] = 1
        df.loc[short_cond.shift(1, fill_value=False), 'signal'] = -1

        # --- 거래내역을 위한 trades 리스트 준비 ---
        trades = []
        position = 0
        entry_price = 0
        entry_time = None
        entry_idx = None
        entry_time_local = None

        for i in range(len(df)):
            # 진입
            if position == 0 and df['signal'].iat[i] == 1:
                position = 1
                entry_price = df['close'].iat[i]
                entry_time = df['time'].iat[i]
                entry_time_local = df['time_local'].iat[i]
                entry_idx = i
                if log_fn: log_fn(f"[Long 진입] {df['time_local'].iat[i]} / 진입가: {entry_price}")

            elif position == 0 and df['signal'].iat[i] == -1:
                position = -1
                entry_price = df['close'].iat[i]
                entry_time = df['time'].iat[i]
                entry_time_local = df['time_local'].iat[i]
                entry_idx = i
                if log_fn: log_fn(f"[Short 진입] {df['time_local'].iat[i]} / 진입가: {entry_price}")

            # 롱 청산 (익절/손절)
            if position == 1:
                # 익절
                if df['close'].iat[i] >= entry_price + self.tp_pips:
                    exit_price = df['close'].iat[i]
                    exit_time = df['time'].iat[i]
                    exit_time_local = df['time_local'].iat[i]
                    pnl = exit_price - entry_price
                    trades.append({
                        '진입시각': entry_time_local,
                        '청산시각': exit_time_local,
                        '포지션': 'Long',
                        '진입가': entry_price,
                        '청산가': exit_price,
                        '수익': pnl
                    })
                    if log_fn: log_fn(f"[Long 익절] {exit_time_local} / 청산가: {exit_price}")
                    position = 0
                # 손절
                elif (i > entry_idx) and (df['open'].iat[i] < df['low26'].iat[i]):
                    exit_price = df['open'].iat[i]
                    exit_time = df['time'].iat[i]
                    exit_time_local = df['time_local'].iat[i]
                    pnl = exit_price - entry_price
                    trades.append({
                        '진입시각': entry_time_local,
                        '청산시각': exit_time_local,
                        '포지션': 'Long',
                        '진입가': entry_price,
                        '청산가': exit_price,
                        '수익': pnl
                    })
                    if log_fn: log_fn(f"[Long 손절] {exit_time_local} / 청산가: {exit_price}")
                    position = 0

            # 숏 청산 (익절/손절)
            if position == -1:
                # 익절
                if df['close'].iat[i] <= entry_price - self.tp_pips:
                    exit_price = df['close'].iat[i]
                    exit_time = df['time'].iat[i]
                    exit_time_local = df['time_local'].iat[i]
                    pnl = entry_price - exit_price
                    trades.append({
                        '진입시각': entry_time_local,
                        '청산시각': exit_time_local,
                        '포지션': 'Short',
                        '진입가': entry_price,
                        '청산가': exit_price,
                        '수익': pnl
                    })
                    if log_fn: log_fn(f"[Short 익절] {exit_time_local} / 청산가: {exit_price}")
                    position = 0
                # 손절
                elif (i > entry_idx) and (df['open'].iat[i] > df['high26'].iat[i]):
                    exit_price = df['open'].iat[i]
                    exit_time = df['time'].iat[i]
                    exit_time_local = df['time_local'].iat[i]
                    pnl = entry_price - exit_price
                    trades.append({
                        '진입시각': entry_time_local,
                        '청산시각': exit_time_local,
                        '포지션': 'Short',
                        '진입가': entry_price,
                        '청산가': exit_price,
                        '수익': pnl
                    })
                    if log_fn: log_fn(f"[Short 손절] {exit_time_local} / 청산가: {exit_price}")
                    position = 0

        # trades 리스트 → DataFrame 반환 (소수점 3자리로 포맷)
        trade_df = pd.DataFrame(trades)
        float_cols = ['진입가', '청산가', '수익']
        for col in float_cols:
            if col in trade_df.columns:
                trade_df[col] = trade_df[col].round(3)
        return trade_df
