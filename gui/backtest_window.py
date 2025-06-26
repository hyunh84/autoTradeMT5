from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QTextEdit,
    QHBoxLayout, QVBoxLayout, QLineEdit, QHeaderView, QSizePolicy, QFileDialog
)
from PyQt5.QtGui import QColor, QFont, QBrush
from PyQt5.QtCore import Qt, pyqtSignal
import sys
import pandas as pd

import MetaTrader5 as mt5
from strategy.Ichimoku_Strategy import IchimokuBreakoutStrategy
from dataMT5.collector import get_mt5_ohlcv

STRATEGY_DICT = {
    "Ichimoku Breakout": IchimokuBreakoutStrategy,
}

class BacktestWindow(QWidget):
    go_main_signal = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.setWindowTitle("전략 백테스트")
        self.setGeometry(200, 200, 700, 700)  # 가로폭 살짝 넓힘
        self.last_trade_df = None  # 백테스트 결과 저장용
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # ---------- [GO Main] ----------
        btnTop_layout = QHBoxLayout()
        btnTop_layout.setSpacing(5)
        self.go_home_btn = QPushButton('홈')
        self.go_home_btn.setFixedHeight(34)
        self.go_home_btn.setStyleSheet("width: 100%; font-size: 15px; background-color: #cccccc; font-weight: bold;")
        self.go_home_btn.clicked.connect(self.go_main)
        btnTop_layout.addWidget(self.go_home_btn)
        main_layout.addLayout(btnTop_layout)

        # ---------- [상단 : 전략 선택] ----------
        top_layout = QHBoxLayout()
        self.strategy_cb = QComboBox()
        self.strategy_cb.addItems(list(STRATEGY_DICT.keys()))
        top_layout.addWidget(QLabel("전략 선택 박스"))
        top_layout.addWidget(self.strategy_cb)
        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        # ---------- [테스트 시작 버튼] ----------
        self.start_btn = QPushButton("테스트 시작")
        self.start_btn.setFixedHeight(36)
        self.start_btn.setStyleSheet("background-color: #1590b2; color: white; font-size: 22px; font-weight: bold;")
        self.start_btn.clicked.connect(self.run_backtest)
        main_layout.addWidget(self.start_btn)

        # ---------- [엑셀 저장 버튼] ----------
        self.save_btn = QPushButton("엑셀로 저장")
        self.save_btn.setFixedHeight(30)
        self.save_btn.clicked.connect(self.save_to_excel)
        main_layout.addWidget(self.save_btn)

        # ---------- [계좌/원금/총수익 테이블] ----------
        self.info_table = QTableWidget(2, 4)
        self.info_table.setFixedHeight(85)
        self.info_table.horizontalHeader().setVisible(False)
        self.info_table.verticalHeader().setVisible(False)
        self.info_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.info_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.info_table.setStyleSheet("""
            QTableWidget {
                margin: 0px; padding: 0px; border: none;
            }
            QTableCornerButton::section {
                background: white; border: none; margin: 0px;
            }
        """)
        title_bg = QBrush(QColor("#156082"))
        title_fg = QBrush(Qt.white)
        bold_font = QFont()
        bold_font.setBold(True)

        tblItem = QTableWidgetItem("종목")
        tblItem.setBackground(title_bg)
        tblItem.setForeground(title_fg)
        tblItem.setFont(bold_font)
        tblItem.setTextAlignment(Qt.AlignCenter)
        self.info_table.setItem(0, 0, tblItem)
        self.info_table.setItem(0, 1, QTableWidgetItem("GBPJPY, Great Britain Pound vs Japanese Yen "))
        tblItem = QTableWidgetItem("투자금")
        tblItem.setBackground(title_bg)
        tblItem.setForeground(title_fg)
        tblItem.setFont(bold_font)
        tblItem.setTextAlignment(Qt.AlignCenter)
        self.info_table.setItem(1, 0, tblItem)

        self.input_invest = QLineEdit()
        self.input_invest.setPlaceholderText("금액 입력")
        self.info_table.setCellWidget(1, 1, self.input_invest)

        tblItem = QTableWidgetItem("총 수익")
        tblItem.setBackground(title_bg)
        tblItem.setForeground(title_fg)
        tblItem.setFont(bold_font)
        tblItem.setTextAlignment(Qt.AlignCenter)
        self.info_table.setItem(1, 2, tblItem)
        self.info_table.setSpan(0, 1, 1, 3)

        main_layout.addWidget(self.info_table)

        # ---------- [거래내역 테이블] ----------
        self.trade_table = QTableWidget(0, 6)
        self.trade_table.setHorizontalHeaderLabels(
            ["진입시각", "청산시각", "포지션", "진입가", "청산가", "수익"]
        )
        self.trade_table.setFixedHeight(300)
        self.trade_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.trade_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.trade_table.setStyleSheet("""
            QTableWidget {
                margin: 0px; padding: 0px; border: none;
            }
            QTableCornerButton::section {
                border: none; margin: 0px; padding: 0px;
            }
        """)
        main_layout.addWidget(self.trade_table)

        # ---------- [콘솔 로그 영역] ----------
        self.console = QTextEdit()
        self.console.setPlaceholderText("로그가 여기에 표시됩니다.")
        self.console.setReadOnly(True)
        self.console.setFixedHeight(330)
        self.console.setStyleSheet("""
        QTextEdit {
            font-family: Consolas,monospace; margin: 0px; padding: 0px; border: none;
        }
        """)
        main_layout.addWidget(self.console)

        self.setLayout(main_layout)

    def go_main(self):
        self.go_main_signal.emit()

    def run_backtest(self):
        df = get_mt5_ohlcv(symbol="GBPJPY", n=10_000, timeframe=mt5.TIMEFRAME_H1)
        if df is None:
            self.console.append("캔들 데이터 없음! MT5 연결 또는 심볼 확인.")
            return

        if not pd.api.types.is_datetime64_any_dtype(df['time']):
            df['time'] = pd.to_datetime(df['time'])
        if df['time'].dt.tz is None:
            df['time'] = df['time'].dt.tz_localize('UTC')
        df['time_local'] = df['time'].dt.tz_convert('Asia/Seoul')

        strategy_name = self.strategy_cb.currentText()
        StrategyClass = STRATEGY_DICT[strategy_name]
        strategy = StrategyClass()

        # columns: 진입시각, 청산시각, 포지션, 진입가, 청산가, 수익
        trade_df = strategy.run(df, self.console.append)

        # ★ 소수점 3자리로 통일 (UI와 엑셀 모두!)
        float_cols = ['진입가', '청산가', '수익']
        for col in float_cols:
            if col in trade_df.columns:
                trade_df[col] = trade_df[col].round(3)

        self.last_trade_df = trade_df   # 저장
        self.update_trade_table(trade_df)
        self.update_total_pnl(trade_df)
        self.console.append(f"{strategy_name} 테스트 완료! 총 수익: {trade_df['수익'].sum():.3f}")

    def update_trade_table(self, trade_df):
        self.trade_table.setRowCount(len(trade_df))
        for i, row in trade_df.iterrows():
            # 진입/청산시각을 사람이 읽기 좋게 변환
            entry_time = row.get('진입시각', '')
            exit_time = row.get('청산시각', '')
            if hasattr(entry_time, 'strftime'):
                entry_time = entry_time.strftime('%Y-%m-%d %H:%M')
            if hasattr(exit_time, 'strftime'):
                exit_time = exit_time.strftime('%Y-%m-%d %H:%M')
            self.trade_table.setItem(i, 0, QTableWidgetItem(str(entry_time)))
            self.trade_table.setItem(i, 1, QTableWidgetItem(str(exit_time)))
            self.trade_table.setItem(i, 2, QTableWidgetItem(str(row.get('포지션', ''))))
            # 소수점 3자리로 표시
            self.trade_table.setItem(i, 3, QTableWidgetItem(f"{row.get('진입가', 0):.3f}"))
            self.trade_table.setItem(i, 4, QTableWidgetItem(f"{row.get('청산가', 0):.3f}"))
            self.trade_table.setItem(i, 5, QTableWidgetItem(f"{row.get('수익', 0):.3f}"))

    def update_total_pnl(self, trade_df):
        total_pnl = trade_df['수익'].sum()
        self.info_table.setItem(1, 3, QTableWidgetItem(f"{total_pnl:.3f}"))

    def save_to_excel(self):
        if not hasattr(self, 'last_trade_df') or self.last_trade_df is None or self.last_trade_df.empty:
            self.console.append("저장할 거래내역이 없습니다!")
            return

        df = self.last_trade_df.copy()
        # 소수점 3자리 고정
        float_cols = ['진입가', '청산가', '수익']
        for col in float_cols:
            if col in df.columns:
                df[col] = df[col].round(3)

        # 엑셀 저장 전 datetime 컬럼의 타임존 정보 제거
        for col in ['진입시각', '청산시각']:
            if col in df.columns and pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.tz_localize(None)

        fname, _ = QFileDialog.getSaveFileName(self, "엑셀 파일로 저장", "", "Excel Files (*.xlsx)")
        if fname:
            df.to_excel(fname, index=False)
            self.console.append(f"엑셀 파일로 저장됨: {fname}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = BacktestWindow()
    w.show()
    sys.exit(app.exec_())
