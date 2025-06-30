import pandas as pd

class IchimokuBreakoutStrategyRT:
    def __init__(self, pip=0.01, tp_pips=0.18, sl_pips=0.15, lot=0.01, symbol=None):
        self.pip = pip
        self.tp_pips = tp_pips
        self.sl_pips = sl_pips
        self.lot = lot
        self.symbol = symbol
        self.position = 0
        self.entry_price = None
        self.entry_time = None

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

    def check_entry_signal(self, df):
        df = self.calculate_ichimoku(df)
        i = len(df) - 1
        if i < 52 + 26:
            return 0
        bull_cross = (df['conversion'].iat[i] > df['base'].iat[i]) and (df['conversion'].iat[i-1] <= df['base'].iat[i-1])
        bear_cross = (df['conversion'].iat[i] < df['base'].iat[i]) and (df['conversion'].iat[i-1] >= df['base'].iat[i-1])
        conversion_rising = (df['conversion'].iat[i] - df['conversion'].iat[i-1]) >= 4 * self.pip
        conversion_falling = (df['conversion'].iat[i-1] - df['conversion'].iat[i]) >= 4 * self.pip

        valid = all(pd.notnull([
            df['conversion'].iat[i], df['base'].iat[i], df['kumo_high'].iat[i], df['kumo_low'].iat[i],
            df['high26'].iat[i], df['low26'].iat[i]
        ]))

        long_cond = (
            bull_cross and
            df['conversion'].iat[i] > df['kumo_high'].iat[i] and
            df['base'].iat[i] > df['kumo_high'].iat[i] and
            df['close'].iat[i] > df['high26'].iat[i] and
            df['close'].iat[i] > df['conversion'].iat[i] and
            conversion_rising and valid
        )
        short_cond = (
            bear_cross and
            df['conversion'].iat[i] < df['kumo_low'].iat[i] and
            df['base'].iat[i] < df['kumo_low'].iat[i] and
            df['close'].iat[i] < df['low26'].iat[i] and
            df['close'].iat[i] < df['conversion'].iat[i] and
            conversion_falling and valid
        )
        if long_cond:
            return 1
        elif short_cond:
            return -1
        else:
            return 0

    def on_tick(self, df, current_price):
        """
        df: 반드시 실시간으로 받아온 진짜 GBPJPY(등) 최신 봉 시계열 (최신 100개 정도)
        current_price: 실시간 틱/호가 (진짜 거래소에서 받은 값)
        """
        if self.position == 0:
            signal = self.check_entry_signal(df)
            if signal == 1:
                self.position = 1
                self.entry_price = current_price
                self.entry_time = df['time'].iloc[-1]
                return {
                    'signal': 'long_entry',
                    'price': current_price,
                    'time': self.entry_time,
                    'symbol': self.symbol
                }
            elif signal == -1:
                self.position = -1
                self.entry_price = current_price
                self.entry_time = df['time'].iloc[-1]
                return {
                    'signal': 'short_entry',
                    'price': current_price,
                    'time': self.entry_time,
                    'symbol': self.symbol
                }
            else:
                return None

        if self.position == 1:
            tp = self.entry_price + self.tp_pips
            sl = self.entry_price - self.sl_pips
            if current_price >= tp:
                result = {
                    'signal': 'long_exit_tp',
                    'entry': self.entry_price,
                    'exit': tp,
                    'time': df['time'].iloc[-1],
                    'symbol': self.symbol
                }
                self.position = 0
                self.entry_price = None
                self.entry_time = None
                return result
            elif current_price <= sl:
                result = {
                    'signal': 'long_exit_sl',
                    'entry': self.entry_price,
                    'exit': sl,
                    'time': df['time'].iloc[-1],
                    'symbol': self.symbol
                }
                self.position = 0
                self.entry_price = None
                self.entry_time = None
                return result
            return None

        if self.position == -1:
            tp = self.entry_price - self.tp_pips
            sl = self.entry_price + self.sl_pips
            if current_price <= tp:
                result = {
                    'signal': 'short_exit_tp',
                    'entry': self.entry_price,
                    'exit': tp,
                    'time': df['time'].iloc[-1],
                    'symbol': self.symbol
                }
                self.position = 0
                self.entry_price = None
                self.entry_time = None
                return result
            elif current_price >= sl:
                result = {
                    'signal': 'short_exit_sl',
                    'entry': self.entry_price,
                    'exit': sl,
                    'time': df['time'].iloc[-1],
                    'symbol': self.symbol
                }
                self.position = 0
                self.entry_price = None
                self.entry_time = None
                return result
            return None
