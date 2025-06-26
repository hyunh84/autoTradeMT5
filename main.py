import sys
from PyQt5.QtWidgets import QApplication, QStackedWidget
from gui.main_dashboard import MainDashboard
from gui.backtest_window import BacktestWindow

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

    # === 1. 각 화면 위젯 생성 ===
    main_dashboard = MainDashboard()
    backtest_window = BacktestWindow()
    stack.addWidget(main_dashboard)   # index 0: 메인
    stack.addWidget(backtest_window)  # index 1: 백테스트

    # === 2. MT5 계좌 연결 및 정보 표시 ===
    account_info, connected = get_mt5_account_info(main_dashboard.append_log)
    main_dashboard.set_connection_status(connected)
    main_dashboard.set_account_info(account_info)

    # === 3. 메뉴 → "백테스트" 선택 시 화면 전환 ===
    def show_backtest():
        stack.setCurrentIndex(1)
    main_dashboard.open_backtest.connect(show_backtest)

    # === 4. 백테스트 → "홈" 버튼 시 메인화면 전환 ===
    def show_main():
        stack.setCurrentIndex(0)
    backtest_window.go_main_signal.connect(show_main)

    # === 5. QStackedWidget 기본 세팅 및 실행 ===
    stack.setCurrentIndex(0)      # 첫 화면: 메인 대시보드
    stack.resize(650, 700)
    stack.show()
    sys.exit(app.exec_())
