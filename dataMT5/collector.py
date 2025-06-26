# collector.py
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

def get_mt5_ohlcv(symbol="GBPJPY", timeframe=mt5.TIMEFRAME_M5, n=300):
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return None
    utc_to = datetime.now()
    rates = mt5.copy_rates_from(symbol, timeframe, utc_to, n)
    mt5.shutdown()
    if rates is None or len(rates) == 0:
        print("데이터 없음")
        return None
    df = pd.DataFrame(rates)
    # ↓↓↓ UTC임을 명확하게!
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df['time_local'] = df['time'].dt.tz_convert('Asia/Seoul')
    return df
