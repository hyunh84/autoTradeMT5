from PyQt5.QtWidgets import (
	QWidget, QLabel, QHBoxLayout, QVBoxLayout, QTableWidget, QHeaderView,
	QTableWidgetItem, QTextEdit, QPushButton, QFrame, QMenu, QSizePolicy
)
from PyQt5.QtGui import QColor, QIcon, QPainter, QPixmap, QBrush, QFont
from PyQt5.QtCore import Qt, pyqtSignal

class CircleLabel(QLabel):
	def __init__(self, color=QColor("yellow"), parent=None):
		super().__init__(parent)
		self.color = color
		self.setFixedSize(14, 14)

	def setColor(self, color):
		self.color = color
		self.update()

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setRenderHint(QPainter.Antialiasing)
		painter.setBrush(self.color)
		painter.setPen(Qt.NoPen)
		painter.drawEllipse(0, 0, 14, 14)

class MainDashboard(QWidget):
	open_backtest = pyqtSignal()   # 시그널 선언

	def __init__(self):
		super().__init__()
		self.setWindowTitle("MT5 대시보드")
		self.setGeometry(200, 200, 500, 500)
		self.init_ui()

	def init_ui(self):
		main_layout = QVBoxLayout()
		main_layout.setSpacing(5)  # 전체 간격은 0 (딱 붙게)
		main_layout.setContentsMargins(10, 10, 10, 10)  # 창 바깥 여백

		# 상단: 연결상태 + 햄버거
		top_layout = QHBoxLayout()
		top_layout.addSpacing(5)
		self.status_circle = CircleLabel(QColor("yellow"))
		self.status_label = QLabel("MT5 연결대기")
		self.status_label.setStyleSheet("font-weight: bold;")
		top_layout.addWidget(self.status_circle)
		top_layout.addWidget(self.status_label)
		top_layout.addStretch()

		# 햄버거 버튼(아이콘)
		self.menu_btn = QPushButton()
		self.menu_btn.setFixedSize(34, 34)
		icon = QPixmap(32, 32)
		icon.fill(Qt.transparent)
		painter = QPainter(icon)
		painter.setPen(Qt.black)
		for i in range(3):
			painter.drawLine(6, 8 + i*8, 26, 8 + i*8)
		painter.end()
		self.menu_btn.setIcon(QIcon(icon))
		self.menu_btn.setIconSize(icon.rect().size())
		self.menu_btn.clicked.connect(self.show_menu)
		
		top_layout.addWidget(self.menu_btn)
		top_layout.addSpacing(5)

		# 계좌정보 테이블
		self.account_table = QTableWidget(2, 4)
		self.account_table.setFixedHeight(130)
		self.account_table.horizontalHeader().setVisible(False)
		self.account_table.verticalHeader().setVisible(False)
		self.account_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
		self.account_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
		# ★ 스타일시트로 완전 밀착!
		self.account_table.setStyleSheet("""
			QTableWidget {
				margin: 0px;
				padding: 0px;
				border: none;
			}
			QTableCornerButton::section {
				margin: 0px;
				padding: 0px;
			}
		""")

		# --- 제목 스타일 적용 (예시) ---
		title_bg = QBrush(QColor("#156082"))
		title_fg = QBrush(Qt.white)
		bold_font = QFont()
		bold_font.setBold(True)

		# 계좌
		item = QTableWidgetItem("계좌")
		item.setBackground(title_bg)
		item.setForeground(title_fg)
		item.setFont(bold_font)
		item.setTextAlignment(Qt.AlignCenter)
		self.account_table.setItem(0, 0, item)

		# 잔고
		item = QTableWidgetItem("잔고")
		item.setBackground(title_bg)
		item.setForeground(title_fg)
		item.setFont(bold_font)
		item.setTextAlignment(Qt.AlignCenter)
		self.account_table.setItem(1, 0, item)

		# 통화
		item = QTableWidgetItem("통화")
		item.setBackground(title_bg)
		item.setForeground(title_fg)
		item.setFont(bold_font)
		item.setTextAlignment(Qt.AlignCenter)
		self.account_table.setItem(1, 2, item)

		self.account_table.setSpan(0, 1, 1, 3)
		self.account_table.setEditTriggers(QTableWidget.NoEditTriggers)

		# 콘솔 로그 영역
		self.console = QTextEdit()
		self.console.setPlaceholderText("로그가 여기에 표시됩니다.")
		self.console.setReadOnly(True)
		self.console.setFixedHeight(330)
		# ★ 스타일시트로 완전 밀착!
		self.console.setStyleSheet("""
			QTextEdit {
				font-family: Consolas,monospace;
				margin: 0px;
				padding: 0px;
				border: none;
			}
		""")

		# === 블록 사이 여백 없이 딱 붙여서 배치 ===
		main_layout.addLayout(top_layout)
		main_layout.addWidget(self.account_table)
		main_layout.addWidget(self.console)

		self.setLayout(main_layout)

	def set_connection_status(self, connected: bool):
		if connected:
			self.status_circle.setColor(QColor("green"))  # 또는 green
			self.status_label.setText("MT5 연결성공")
		else:
			self.status_circle.setColor(QColor("yellow"))
			self.status_label.setText("MT5 연결대기")

	def set_account_info(self, account_info):
		if not account_info:
			accNo, balan, curren = "-", "-", "-"
		else:
			accNo = getattr(account_info, 'login', None) or \
					  (account_info.get('login') if hasattr(account_info, 'get') else "-")
			balan = getattr(account_info, 'balance', None) or \
				  (account_info.get('balance') if hasattr(account_info, 'get') else "-")
			curren = getattr(account_info, 'currency', None) or \
				  (account_info.get('currency') if hasattr(account_info, 'get') else "-")
			
		self.account_table.setItem(0, 1, QTableWidgetItem(str(accNo)))
		self.account_table.setItem(1, 1, QTableWidgetItem(str(balan)))
		self.account_table.setItem(1, 3, QTableWidgetItem(str(curren)))

	def show_menu(self):
		menu = QMenu()
		backtest_action = menu.addAction("백테스트")
		action = menu.exec_(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))
		if action == backtest_action:
			self.open_backtest.emit()   # 시그널 발생

	def return_main(self):
		self.backtest_window.close()
		self.show()  # 메인윈도우 다시 표시

	def append_log(self, text):
		self.console.append(text)
