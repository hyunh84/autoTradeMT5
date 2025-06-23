# backtest/backtester.py

import pandas as pd
import importlib.util
import os

def run_backtest(strategy_path, log, symbol="GBPJPY", csv_path="data/GBPJPY_H1.csv"):
    """
    선택한 전략 파일을 불러와 .csv 데이터를 기반으로 백테스트를 수행

    Parameters:
        strategy_path (str): 사용자 전략 파일 경로
        log (function): 로그 출력 함수 (GUI에서 전달)
        symbol (str): 종목명 (기본값: GBPJPY)
        csv_path (str): OHLCV csv 파일 경로

    Returns:
        pd.DataFrame: 전략 실행 후 시그널이 포함된 DataFrame (없으면 None 반환)
    """

    # 1️⃣ 전략 파일이 존재하는지 확인
    if not os.path.exists(strategy_path):
        log(f"[❌] 전략 파일을 찾을 수 없음: {strategy_path}")
        return None

    # 2️⃣ csv 파일이 존재하는지 확인
    if not os.path.exists(csv_path):
        log(f"[❌] CSV 데이터 파일 없음: {csv_path}")
        return None

    # 3️⃣ CSV 데이터 로드
    df = pd.read_csv(csv_path)
    if len(df) < 53:
        log("⚠️ 백테스트용 데이터가 부족합니다.")
        return None

    # 4️⃣ 열 이름 확인 및 리네이밍 (필수 열: time, open, high, low, close)
    expected = {"time", "open", "high", "low", "close"}
    if not expected.issubset(set(df.columns)):
        log("⚠ CSV에 필수 컬럼이 누락됨: open, high, low, close, time")
        return None

    # 5️⃣ 전략 파일 로드
    spec = importlib.util.spec_from_file_location("custom_strategy", strategy_path)
    strategy_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(strategy_module)

    # 6️⃣ 전략 함수 실행 (DataFrame, 로그함수, 심볼 전달)
    try:
        if hasattr(strategy_module, "run_strategy"):
            df_result = strategy_module.run_strategy(df, log, symbol)
            if df_result is not None and "signal" in df_result.columns:
                log("✅ 백테스트 완료")
                return df_result
            else:
                log("⚠ 'signal' 컬럼이 없습니다. 전략 로직을 확인하세요.")
                return None
        else:
            log("⚠️ run_strategy 함수가 정의되어 있지 않습니다.")
            return None
    except Exception as e:
        log(f"[전략 실행 오류] {e}")
        return None
