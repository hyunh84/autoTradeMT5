from PyQt5.QtWidgets import (
	QWidget, QLabel, QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
	QHBoxLayout, QVBoxLayout, QFrame, QApplication, QLineEdit, QSizePolicy, QHeaderView
)
from PyQt5.QtGui import QColor, QFont, QBrush
from PyQt5.QtCore import Qt
import sys

class BacktestWindow(QWidget):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("전략 백테스트")
		self.setGeometry(200, 200, 500, 700)
		self.init_ui()

	def init_ui(self):
		main_layout = QVBoxLayout()
		main_layout.setSpacing(5)
		main_layout.setContentsMargins(10,10,10,10)

		# 전략 선택 박스
		strategy_layout = QHBoxLayout()
		self.strategy_cb = QComboBox()
		self.strategy_cb.addItems(["Ichimoku", "RSI", "MACD"])
		strategy_layout.addWidget(QLabel("전략 선택 박스"))
		strategy_layout.addWidget(self.strategy_cb)
		main_layout.addLayout(strategy_layout)

		# 테스트 시작 버튼(가운데 정렬)
		self.start_btn = QPushButton("테스트 시작")
		self.start_btn.setFixedHeight(36)
		self.start_btn.setStyleSheet("background-color: #1590b2; color: white; font-size: 22px; font-weight: bold;")
		main_layout.addWidget(self.start_btn)

		# 계좌/원금/총수익 테이블
		self.info_table = QTableWidget(2, 4)
		self.info_table.setFixedHeight(85)
		self.info_table.horizontalHeader().setVisible(False)
		self.info_table.verticalHeader().setVisible(False)
		self.info_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
		self.info_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

		# --- 제목 스타일 적용 ---
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

		# 테이블 사이 줄
		line = QFrame()
		line.setFrameShape(QFrame.HLine)
		line.setFrameShadow(QFrame.Sunken)
		line.setFixedHeight(1) 
		main_layout.addWidget(self.info_table)
		# main_layout.addWidget(line)

		# 거래내역 테이블
		self.trade_table = QTableWidget(5, 4)
		self.trade_table.setHorizontalHeaderLabels(["날짜", "포지션", "가격", "수익"])
		self.trade_table.setFixedHeight(160)
		for i in range(4):
			self.trade_table.horizontalHeaderItem(i).setBackground(QBrush(QColor("#156082")))
			self.trade_table.horizontalHeaderItem(i).setForeground(QBrush(Qt.white))
			self.trade_table.horizontalHeaderItem(i).setFont(QFont("", weight=QFont.Bold))
		for r in range(5):
			for c in range(4):
				self.trade_table.setItem(r, c, QTableWidgetItem("${data}"))
		main_layout.addWidget(self.trade_table)

		self.setLayout(main_layout)

if __name__ == "__main__":
	app = QApplication(sys.argv)
	w = BacktestWindow()
	w.show()
	sys.exit(app.exec_())
