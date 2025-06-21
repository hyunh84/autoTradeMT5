from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QHBoxLayout, QSizePolicy
)
from PyQt5.QtCore import Qt

class AIPrompt(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChatGPT 프롬프트")
        self.setMinimumSize(500, 600)

        # 전체 레이아웃
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # 출력 영역 (ChatGPT 응답)
        self.response_area = QTextEdit()
        self.response_area.setReadOnly(True)
        self.response_area.setPlaceholderText("여기에 ChatGPT 응답이 표시됩니다...")
        self.response_area.setStyleSheet("font-size: 13px; background-color: #f9f9f9;")
        layout.addWidget(QLabel("💬 ChatGPT 응답"))
        layout.addWidget(self.response_area, stretch=3)

        # 입력 영역
        layout.addWidget(QLabel("✍️ 입력"))
        self.input_area = QTextEdit()
        self.input_area.setPlaceholderText("메시지를 입력하세요...")
        self.input_area.setFixedHeight(100)
        self.input_area.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.input_area, stretch=1)

        # 전송 버튼
        button_layout = QHBoxLayout()
        self.send_button = QPushButton("전송")
        self.send_button.setStyleSheet("font-size: 14px; padding: 8px;")
        self.send_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.send_button.clicked.connect(self.handle_send)
        button_layout.addStretch()
        button_layout.addWidget(self.send_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def handle_send(self):
        user_input = self.input_area.toPlainText().strip()
        if not user_input:
            return

        # 추후 OpenAI API와 연동 시 여기서 응답 처리
        self.append_conversation("👤 사용자", user_input)
        self.input_area.clear()

        # === ChatGPT 응답 시뮬레이션 (테스트용) ===
        dummy_reply = "이건 ChatGPT의 예시 응답입니다. 실제 API와 연결하면 이 부분을 바꿔주세요."
        self.append_conversation("🤖 ChatGPT", dummy_reply)

    def append_conversation(self, speaker, message):
        self.response_area.append(f"<b>{speaker}:</b><br>{message}<br>")
