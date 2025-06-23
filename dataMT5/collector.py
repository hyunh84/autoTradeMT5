# dataMT5/collector.py
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

def initialize_mt5():
    if not mt5.initialize():
        raise RuntimeError("MT5 초기화 실패")
    return True

def fetch_ohlcv(symbol="GBPJPY", timeframe=mt5.TIMEFRAME_H1, count=500, save_path=None):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None:
        raise ValueError(f"데이터를 가져오지 못함: {symbol}")
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')  # timestamp → datetime 변환

    # ✅ 저장 경로가 지정되었으면 CSV로 저장
    if save_path:
        df.to_csv(save_path, index=False)
        print(f"✅ 데이터 저장 완료: {save_path}")

    return df

if __name__ == "__main__":
    initialize_mt5()
    df = fetch_ohlcv(save_path="ohlcv.csv")
    print(df.tail())
