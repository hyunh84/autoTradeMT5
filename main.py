import sys
from PyQt5.QtWidgets import QApplication, QStackedWidget
from gui.main_dashboard import MainDashboard
from gui.text_window import BacktestWindow

import MetaTrader5 as mt5

def get_mt5_account_info(log_fn):
    log_fn("MT5 연결 시도...")
    if not mt5.initialize():
        log_fn(f"MT5 연결 실패! {mt5.last_error()}")
        return None, False
    info = mt5.account_info()
    if info is None:
        log_fn("계좌 정보 없음!")
        mt5.shutdown()
        return None, False
    log_fn("MT5 연결 및 로그인 성공")
    log_fn(f"계좌번호: {info.login}, 잔고: {info.balance} {info.currency}")
    mt5.shutdown()
    return info, True

if __name__ == "__main__":
    app = QApplication(sys.argv)
    stack = QStackedWidget()

    main_dashboard = MainDashboard()
    backtest_window = BacktestWindow()
    stack.addWidget(main_dashboard)   # index 0: 메인
    stack.addWidget(backtest_window)  # index 1: 백테스트

    # 연결 + 계좌정보
    account_info, connected = get_mt5_account_info(main_dashboard.append_log)
    main_dashboard.set_connection_status(connected)
    main_dashboard.set_account_info(account_info)

    # 1. 메뉴에서 "백테스트" 시그널 연결 → 화면 전환
    def show_backtest():
        stack.setCurrentIndex(1)
    main_dashboard.open_backtest.connect(show_backtest)

    # 2. 필요하면 백테스트에서 다시 메인으로 돌아오는 시그널도 연결 가능

    stack.setCurrentIndex(0)
    stack.resize(650, 700)
    stack.show()
    sys.exit(app.exec_())
