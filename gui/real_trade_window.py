from PyQt5.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QComboBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QLineEdit, QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer

import pandas as pd

from strategy.real_Ichimoku_Strategy import IchimokuBreakoutStrategyRT

class RealtimeTradeWindow(QWidget):
    def __init__(self, parent=None, account_info=None):
        super().__init__(parent)
        self.setWindowTitle("실시간 자동매매")
        self.setGeometry(250, 100, 700, 500)
        self.account_info = account_info
        self.running = False
        self.strategy = None
        self.df_history = None  # 반드시 실거래 시세 데이터만!
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.status_label = QLabel("연결상태: 대기")
        font = QFont()
        font.setBold(True)
        self.status_label.setFont(font)
        layout.addWidget(self.status_label)

        if self.account_info:
            acc_str = f"계좌번호: {self.account_info.get('login', '-')}, 서버: {self.account_info.get('server', '-')}"
        else:
            acc_str = "계좌정보 없음"
        self.acc_label = QLabel(acc_str)
        layout.addWidget(self.acc_label)

        strat_layout = QHBoxLayout()
        strat_layout.addWidget(QLabel("전략:"))
        self.strategy_cb = QComboBox()
        self.strategy_cb.addItems(["Ichimoku Breakout"])
        strat_layout.addWidget(self.strategy_cb)

        strat_layout.addWidget(QLabel("랏:"))
        self.lot_input = QLineEdit()
        self.lot_input.setPlaceholderText("예: 0.01 (마이크로 랏, 최소 0.01 단위)")
        self.lot_input.setFixedWidth(120)
        self.lot_input.setText("0.01")
        strat_layout.addWidget(self.lot_input)

        strat_layout.addWidget(QLabel("금액:"))
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("예: 10000")
        self.amount_input.setFixedWidth(80)
        strat_layout.addWidget(self.amount_input)

        strat_layout.addWidget(QLabel("심볼:"))
        self.symbol_cb = QComboBox()
        self.symbol_cb.addItems(["GBPJPY", "USDJPY", "EURUSD", "GBPUSD", "XAUUSD"])
        strat_layout.addWidget(self.symbol_cb)

        strat_layout.addStretch()
        layout.addLayout(strat_layout)

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("자동매매 시작")
        self.stop_btn = QPushButton("중지")
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        self.start_btn.clicked.connect(self.start_trading)
        self.stop_btn.clicked.connect(self.stop_trading)

        self.trade_table = QTableWidget(0, 7)
        self.trade_table.setHorizontalHeaderLabels([
            "진입시각", "청산시각", "포지션", "진입가", "청산가", "수익", "랏"
        ])
        self.trade_table.setFixedHeight(180)
        layout.addWidget(self.trade_table)

        self.console = QTextEdit()
        self.console.setPlaceholderText("실시간 로그")
        self.console.setReadOnly(True)
        self.console.setFixedHeight(200)
        layout.addWidget(self.console)

        self.setLayout(layout)
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_tick)

    def start_trading(self):
        try:
            lot = float(self.lot_input.text())
            symbol = self.symbol_cb.currentText()
            self.strategy = IchimokuBreakoutStrategyRT(lot=lot, symbol=symbol)
            self.symbol = symbol
        except Exception:
            QMessageBox.warning(self, "입력오류", "랏은 0.01 단위로 입력하세요!")
            return

        self.running = True
        self.status_label.setText("연결상태: 실시간 거래 중")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.console.append(f"[실시간] 자동매매 시작! (심볼: {self.symbol}, 랏: {lot})")
        # self.df_history = ...  # <--- 여기서 반드시 실거래소 캔들/틱 데이터 준비 (초기 100개 등)
        # 실전에서는 실시간 시세 데이터 수신 루프 등에서 갱신

        self.timer.start(2000)

    def stop_trading(self):
        self.running = False
        self.status_label.setText("연결상태: 대기")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.console.append("[실시간] 자동매매 중지!")
        self.timer.stop()

    def on_tick(self):
        if not self.running or self.strategy is None:
            return

        # 반드시 self.df_history와 current_price는 실거래소 최신 데이터여야 함!
        # 예시: self.df_history = 최신 100개 1분봉 DataFrame
        #       current_price = 현재 호가

        if self.df_history is None:
            return  # 아직 데이터 없음

        # 실전에서는 이 부분에서 실시간 데이터로 self.df_history, current_price를 갱신
        current_price = float(self.df_history['close'].iloc[-1])  # 또는 실시간 호가

        result = self.strategy.on_tick(self.df_history, current_price)
        if result is not None:
            self.process_strategy_result(result)

    def process_strategy_result(self, result):
        sig = result['signal']
        now = result.get('time', pd.Timestamp.now())
        lot_val = self.lot_input.text()
        pos = None
        entry_price, exit_price, profit = None, None, None

        if sig == 'long_entry':
            pos = 'Long'
            entry_price = result['price']
            self.console.append(f"[진입] 롱 진입 {now} 진입가: {entry_price}")
        elif sig == 'short_entry':
            pos = 'Short'
            entry_price = result['price']
            self.console.append(f"[진입] 숏 진입 {now} 진입가: {entry_price}")
        elif sig in ['long_exit_tp', 'long_exit_sl']:
            pos = 'Long'
            entry_price = result['entry']
            exit_price = result['exit']
            profit = round(exit_price - entry_price, 3)
            self.console.append(f"[청산] 롱 {'익절' if sig.endswith('tp') else '손절'} {now} 청산가: {exit_price}, 수익: {profit}")
        elif sig in ['short_exit_tp', 'short_exit_sl']:
            pos = 'Short'
            entry_price = result['entry']
            exit_price = result['exit']
            profit = round(entry_price - exit_price, 3)
            self.console.append(f"[청산] 숏 {'익절' if sig.endswith('tp') else '손절'} {now} 청산가: {exit_price}, 수익: {profit}")

        if 'exit' in result:
            row = self.trade_table.rowCount()
            self.trade_table.insertRow(row)
            self.trade_table.setItem(row, 0, QTableWidgetItem(str(self.strategy.entry_time) if self.strategy.entry_time else "-"))
            self.trade_table.setItem(row, 1, QTableWidgetItem(str(now)))
            self.trade_table.setItem(row, 2, QTableWidgetItem(pos))
            self.trade_table.setItem(row, 3, QTableWidgetItem(str(round(entry_price, 3))))
            self.trade_table.setItem(row, 4, QTableWidgetItem(str(round(exit_price, 3))))
            self.trade_table.setItem(row, 5, QTableWidgetItem(str(round(profit, 3))))
            self.trade_table.setItem(row, 6, QTableWidgetItem(lot_val))

    def append_log(self, text):
        self.console.append(text)
