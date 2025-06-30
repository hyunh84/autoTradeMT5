import sys
from PyQt5.QtWidgets import QApplication, QStackedWidget
from gui.main_dashboard import MainDashboard

import MetaTrader5 as mt5

def get_mt5_account_info(log_fn):
    log_fn("MT5 연결 시도...")
    if not mt5.initialize():
        log_fn(f"MT5 연결 실패! {mt5.last_error()}")
        return None, False
    info = mt5.account_info()
    if info is None:
        log_fn("계좌 정보 없음! MT5 종료")
        mt5.shutdown()
        return None, False
    log_fn("MT5 연결 및 로그인 성공")
    log_fn(f"계좌번호: {info.login}, 잔고: {info.balance} {info.currency}")
    mt5.shutdown()
    return info, True

if __name__ == "__main__":
    app = QApplication(sys.argv)
    stack = QStackedWidget()

    # === 1. 메인 대시보드 위젯 생성 ===
    main_dashboard = MainDashboard()
    stack.addWidget(main_dashboard)   # index 0: 메인

    # === 2. MT5 계좌 연결 및 정보 표시 ===
    account_info, connected = get_mt5_account_info(main_dashboard.append_log)
    main_dashboard.set_connection_status(connected)
    main_dashboard.set_account_info(account_info)

    # === 3. QStackedWidget 기본 세팅 및 실행 ===
    stack.setCurrentIndex(0)      # 첫 화면: 메인 대시보드
    stack.resize(650, 700)
    stack.show()
    sys.exit(app.exec_())
