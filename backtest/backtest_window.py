from PyQt5.QtWidgets import (
    QWidget,         # ← 이것이 꼭 포함되어 있어야 함
    QVBoxLayout, QLabel, QPushButton,
    QComboBox, QFileDialog, QTextEdit
)

class BacktestWindow(QWidget):
    def __init__(self, *args, **kwargs):  # 인자를 받아도 에러 없게 처리
        super().__init__()

        # === 필요시 인자 활용 예시 ===
        # self.strategy_map = kwargs.get('strategy_map', None)

        self.setWindowTitle("백테스트 실행 창")
        self.setGeometry(200, 200, 500, 400)

        # === 레이아웃 초기화 ===
        layout = QVBoxLayout()

        # === 전략 선택 콤보박스 ===
        self.strategy_combo = QComboBox()
        self.strategies = load_strategies_from_csv()  # strategies.csv에서 전략 로드

        for strategy_name, _ in self.strategies:
            self.strategy_combo.addItem(strategy_name)

        layout.addWidget(QLabel("전략 선택"))
        layout.addWidget(self.strategy_combo)

        # === CSV 파일 선택 버튼 ===
        self.file_button = QPushButton("CSV 파일 선택")
        self.file_button.clicked.connect(self.select_file)
        layout.addWidget(self.file_button)

        # === 백테스트 실행 버튼 ===
        self.run_button = QPushButton("백테스트 실행")
        self.run_button.clicked.connect(self.run_backtest)
        layout.addWidget(self.run_button)

        # === 결과 출력 영역 ===
        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True)
        layout.addWidget(QLabel("결과 출력"))
        layout.addWidget(self.result_output)

        # === 전체 레이아웃 설정 ===
        self.setLayout(layout)

        # === 내부 변수 초기화 ===
        self.selected_file = None  # 사용자가 선택한 CSV 파일 경로
