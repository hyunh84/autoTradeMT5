import sys
import os
import csv
import importlib.util
from PyQt5.QtWidgets import (
	QApplication, QMainWindow, QPushButton, QTextEdit, QLabel,
	QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
	QMenu, QToolButton, QHBoxLayout
)
import MetaTrader5 as mt5
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QBrush, QColor
from strategy.mgt_strategy import StrategyManagerWindow  # 전략 관리 창 import
from openai.ai_prompt import AIPrompt

class AutoTradeApp(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("자동매매 프로그램")
		self.setGeometry(100, 100, 500, 600)

		# === 메인 위젯 및 레이아웃 설정 ===
		central_widget = QWidget()
		main_layout = QVBoxLayout()
		main_layout.setContentsMargins(10, 10, 10, 10)

		# === 상단 메뉴 버튼 영역 ===
		top_menu_layout = QHBoxLayout()
		top_menu_layout.setContentsMargins(0, 10, 10, 0)
		top_menu_layout.setAlignment(Qt.AlignRight)

		menu_button = QToolButton()
		menu_button.setText("☰")
		menu_button.setPopupMode(QToolButton.InstantPopup)
		menu_button.setStyleSheet("font-size: 18px;")
		menu = QMenu()
		menu_button.setMenu(menu)
		top_menu_layout.addWidget(menu_button)
		main_layout.addLayout(top_menu_layout)

		# 전략 관리 메뉴 추가
		menu.addSeparator()
		menu.addAction("전략 관리", self.open_strategy_manager)

		# 상태 라벨
		self.status_label = QLabel("🟡 자동매매 대기 중")
		main_layout.addWidget(self.status_label)

		# MT5 연결 상태 라벨
		self.mt5_status_label = QLabel("🔴 MT5 미연결")
		main_layout.addWidget(self.mt5_status_label)

		# MT5 연결 버튼 (메뉴)
		self.connect_button = QPushButton("MT5 연결")
		menu.addAction("MT5 연결", self.connect_mt5)

		# 전략 선택 콤보박스
		self.strategy_selector = QComboBox()
		main_layout.addWidget(self.strategy_selector)
		self.strategy_selector.currentIndexChanged.connect(self.on_strategy_changed)

		# 자동매매 시작/정지 메뉴
		menu.addSeparator()
		menu.addAction("자동매매 시작", self.start_trading)
		menu.addAction("자동매매 정지", self.stop_trading)

		# 계좌 정보 테이블
		self.account_table = QTableWidget()
		self.account_table.setFixedHeight(130)
		self.account_table.setRowCount(4)
		self.account_table.setColumnCount(4)
		self.account_table.verticalHeader().setVisible(False)
		self.account_table.horizontalHeader().setVisible(False)
		self.account_table.setEditTriggers(QTableWidget.NoEditTriggers)
		self.account_table.setSpan(3, 1, 1, 3)

		self.set_label_cell(0, 0, "계좌번호")
		self.set_label_cell(0, 2, "매매통화")
		self.set_value_cell(0, 3, "GBP/JPY")
		self.set_label_cell(1, 0, "잔고")
		self.set_label_cell(1, 2, "통화")
		self.set_label_cell(2, 0, "가용자금")
		self.set_label_cell(2, 2, "증거금")
		self.set_label_cell(3, 0, "브로커")

		self.account_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
		self.account_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.account_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.account_table.setStyleSheet("""
			QTableWidget {
				background-color: white;
				font-size: 13px;
				gridline-color: #444;
				border: 1px solid #444;
			}
		""")
		main_layout.addWidget(self.account_table)

		# AI 프롬프트 메뉴
		menu.addSeparator()
		menu.addAction("AI 프롬프트", self.open_ai_prompt)

		# 로그 출력창
		self.log_box = QTextEdit()
		self.log_box.setReadOnly(True)
		main_layout.addWidget(self.log_box)

		# 최종 레이아웃 설정
		central_widget.setLayout(main_layout)
		self.setCentralWidget(central_widget)

		# 상태 변수 및 타이머
		self.auto_trading_active = False
		self.trade_timer = QTimer()
		self.trade_timer.timeout.connect(self.check_trade_signal)

		# 전략 맵 및 불러오기
		self.strategy_map = {}
		self.load_strategy_list()

	# 테이블 라벨 셀
	def set_label_cell(self, row, col, text, colspan=1):
		item = QTableWidgetItem(text)
		item.setTextAlignment(Qt.AlignCenter)
		item.setBackground(QBrush(QColor("#eee")))
		item.setForeground(QBrush(QColor("#333")))
		font = item.font()
		font.setBold(True)
		item.setFont(font)
		self.account_table.setItem(row, col, item)
		if colspan > 1:
			self.account_table.setSpan(row, col, 1, colspan)

	# 테이블 값 셀
	def set_value_cell(self, row, col, text):
		item = QTableWidgetItem(text)
		item.setTextAlignment(Qt.AlignCenter)
		self.account_table.setItem(row, col, item)

	# MT5 연결
	def connect_mt5(self):
		if not mt5.initialize():
			self.log(f"[❌] MT5 연결 실패: {mt5.last_error()}")
			self.mt5_status_label.setText("🔴 MT5 연결 실패")
			return
		self.log("✅ MT5 연결 성공!")
		self.mt5_status_label.setText("🟢 MT5 연결됨")
		account = mt5.account_info()
		if account is None:
			self.log("[⚠️] 계정 정보 불러오기 실패")
			return
		self.set_value_cell(0, 1, str(account.login))
		self.set_value_cell(1, 1, f"{account.balance:.2f}")
		self.set_value_cell(1, 3, account.currency)
		self.set_value_cell(2, 1, f"{account.equity:.2f}")
		self.set_value_cell(2, 3, f"{account.margin:.2f}")
		self.set_value_cell(3, 1, account.company)

	# 자동매매 시작
	def start_trading(self):
		selected = self.strategy_selector.currentText()
		if selected == "전략을 선택하세요":
			self.log("⚠️ 전략이 선택되지 않았습니다.")
			return
		self.status_label.setText("🟢 자동매매 실행 중")
		self.auto_trading_active = True
		self.trade_timer.start(5000)
		self.log(f"{selected} 전략으로 자동매매 시작됨 (5초 간격 체크)")
		self.show_toast(f"{selected}로 매매전략이 적용되었습니다.")

	# 자동매매 정지
	def stop_trading(self):
		mt5.shutdown()
		self.auto_trading_active = False
		self.trade_timer.stop()
		self.mt5_status_label.setText("🔴 MT5 연결 종료됨")
		self.status_label.setText("🔴 자동매매 정지됨")
		self.log("자동매매 정지 및 MT5 연결 종료.")

	# 전략 변경 시 자동 정지
	def on_strategy_changed(self):
		if self.auto_trading_active:
			self.auto_trading_active = False
			self.trade_timer.stop()
			self.status_label.setText("🟡 자동매매 대기 중")
			self.log("⚠️ 전략이 변경되어 자동매매가 중지되었습니다.")

	# 자동매매 시 전략 실행
	def check_trade_signal(self):
		if not self.auto_trading_active:
			return
		selected = self.strategy_selector.currentText()
		if selected == "전략을 선택하세요":
			self.log("⚠️ 전략이 선택되지 않았습니다.")
			return
		strategy_path = self.strategy_map.get(selected)
		if not strategy_path or not os.path.exists(strategy_path):
			self.log(f"[전략 오류] 경로 없음: {strategy_path}")
			return
		try:
			spec = importlib.util.spec_from_file_location("custom_strategy", strategy_path)
			strategy_module = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(strategy_module)
			symbol = "GBPJPY"  # ✅ 고정된 매매 심볼 설정
			mt5.symbol_select(symbol, True)
			if hasattr(strategy_module, "run_strategy"):
				strategy_module.run_strategy(mt5, self.log, symbol)
			else:
				self.log("⚠️ run_strategy 함수가 정의되어 있지 않습니다.")
		except Exception as e:
			self.log(f"[전략 실행 실패] {e}")

	# 토스트 메시지
	def show_toast(self, message):
		self.toast = QLabel(message, self)
		self.toast.setStyleSheet("""
			QLabel {
				background-color: #444;
				color: white;
				padding: 10px 20px;
				border-radius: 5px;
				font-size: 13px;
			}
		""")
		self.toast.adjustSize()
		x = self.width() - self.toast.width() - 30
		y = self.height() - self.toast.height() - 30
		self.toast.setGeometry(x, y, self.toast.width(), self.toast.height())
		self.toast.show()
		QTimer.singleShot(3000, self.toast.hide)

	# 전략 관리 창 열기
	def open_strategy_manager(self):
		self.strategy_window = StrategyManagerWindow()
		self.strategy_window.show()

	# 전략 리스트 로딩
	def load_strategy_list(self):
		self.strategy_selector.clear()
		self.strategy_selector.addItem("전략을 선택하세요")
		self.strategy_map.clear()
		try:
			with open("strategies.csv", newline='', encoding='utf-8') as f:
				reader = csv.DictReader(f)
				for row in reader:
					title = row["title"]
					filepath = row["filepath"]
					self.strategy_selector.addItem(title)
					self.strategy_map[title] = filepath
		except Exception as e:
			self.log(f"[전략 불러오기 실패] {e}")

	# 로그 출력
	def log(self, message):
		self.log_box.append(message)

	# 프로그램 종료 시 정리
	def closeEvent(self, event):
		try:
			if hasattr(self, "strategy_window") and self.strategy_window.isVisible():
				self.strategy_window.close()
		except Exception:
			pass
		event.accept()

	# AI 프롬프트 화면 전환
	def open_ai_prompt(self):
		self.ai_prompt = AIPrompt()
		self.ai_prompt.show()

# 프로그램 실행
if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = AutoTradeApp()
	window.show()
	sys.exit(app.exec_())
