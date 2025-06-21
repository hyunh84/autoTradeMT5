import csv
import os
import shutil
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHBoxLayout, QMessageBox, QLineEdit, QFileDialog, QHeaderView
)
from PyQt5.QtCore import Qt


class StrategyManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("전략 관리")
        self.setGeometry(200, 200, 650, 500)

        self.strategy_file = "strategies.csv"  # 전략 목록 CSV 파일
        self.selected_filepath = None          # 사용자가 선택한 전략 파일 경로

        # === 메인 위젯과 레이아웃 ===
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # === 전략 등록 입력 UI ===
        form_layout = QHBoxLayout()
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("전략 제목 입력")
        self.file_button = QPushButton("파일 선택")
        self.register_button = QPushButton("등록")

        self.file_button.clicked.connect(self.select_file)
        self.register_button.clicked.connect(self.register_strategy)

        form_layout.addWidget(self.title_input)
        form_layout.addWidget(self.file_button)
        form_layout.addWidget(self.register_button)
        main_layout.addLayout(form_layout)

        # === 전략 목록 테이블 ===
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["NO", "제목", "동작"])
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 150)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ccc;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                font-weight: bold;
                text-align: center;
                border: 1px solid #888;
            }
        """)
        main_layout.addWidget(self.table)

        # === 하단 버튼 영역 ===
        btn_layout = QHBoxLayout()
        apply_btn = QPushButton("적용")
        close_btn = QPushButton("닫기")
        apply_btn.clicked.connect(self.apply_strategy)
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(apply_btn)
        btn_layout.addWidget(close_btn)
        main_layout.addLayout(btn_layout)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.load_strategies()

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "전략 파일 선택", "", "Python Files (*.py);;All Files (*)"
        )
        if file_path:
            self.selected_filepath = file_path
            self.file_button.setText("📁 선택됨")

    def register_strategy(self):
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "입력 오류", "전략 제목을 입력하세요.")
            return
        if not self.selected_filepath:
            QMessageBox.warning(self, "파일 오류", "전략 파일을 선택하세요.")
            return

        # ✅ 고정된 저장 폴더: strategy/myStrategy
        strategy_dir = os.path.join("strategy", "myStrategy")
        os.makedirs(strategy_dir, exist_ok=True)

        # ✅ 선택한 파일을 해당 폴더로 복사
        try:
            filename = os.path.basename(self.selected_filepath)
            dest_path = os.path.join(strategy_dir, filename)
            shutil.copy(self.selected_filepath, dest_path)
        except Exception as e:
            QMessageBox.warning(self, "파일 복사 오류", f"전략 파일 복사 실패: {e}")
            return

        # ✅ CSV 기록 추가
        file_exists = os.path.exists(self.strategy_file)
        with open(self.strategy_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["title", "filepath"])
            writer.writerow([title, dest_path])

        QMessageBox.information(self, "등록 완료", f"{title} 전략이 등록되었습니다.")
        self.title_input.clear()
        self.file_button.setText("파일 선택")
        self.selected_filepath = None
        self.load_strategies()

    def load_strategies(self):
        self.table.setRowCount(0)
        if not os.path.exists(self.strategy_file):
            return

        with open(self.strategy_file, newline='', encoding='utf-8') as csvfile:
            reader = list(csv.DictReader(csvfile))
            self.table.setRowCount(len(reader))

            for row, item in enumerate(reader):
                title = item["title"]
                filepath = item["filepath"]

                self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
                self.table.setItem(row, 1, QTableWidgetItem(title))

                dl_btn = QPushButton("다운로드")
                dl_btn.setFixedWidth(70)
                dl_btn.setStyleSheet("font-size: 12px; padding: 2px;")
                dl_btn.clicked.connect(lambda _, f=filepath: self.download_file(f))

                del_btn = QPushButton("삭제")
                del_btn.setFixedWidth(60)
                del_btn.setStyleSheet("font-size: 12px; padding: 2px;")
                del_btn.clicked.connect(lambda _, r=row: self.delete_strategy(r))

                btn_layout = QHBoxLayout()
                btn_layout.setContentsMargins(0, 0, 0, 0)
                btn_layout.setSpacing(5)
                btn_layout.setAlignment(Qt.AlignCenter)
                btn_layout.addWidget(dl_btn)
                btn_layout.addWidget(del_btn)

                btn_widget = QWidget()
                btn_widget.setLayout(btn_layout)
                self.table.setCellWidget(row, 2, btn_widget)

    def delete_strategy(self, row):
        if not os.path.exists(self.strategy_file):
            return

        with open(self.strategy_file, newline='', encoding='utf-8') as f:
            strategies = list(csv.DictReader(f))

        target = strategies[row]
        filepath = target["filepath"]

        reply = QMessageBox.question(
            self, "삭제 확인", f"전략 '{target['title']}'을(를) 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            QMessageBox.warning(self, "파일 삭제 실패", f"파일 삭제 중 오류: {e}")

        del strategies[row]
        with open(self.strategy_file, "w", newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["title", "filepath"])
            writer.writeheader()
            writer.writerows(strategies)

        self.load_strategies()

    def download_file(self, filepath):
        if not os.path.exists(filepath):
            QMessageBox.warning(self, "오류", "원본 전략 파일이 존재하지 않습니다.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "전략 파일 저장", os.path.basename(filepath)
        )
        if save_path:
            try:
                shutil.copy(filepath, save_path)
                QMessageBox.information(self, "다운로드 완료", "파일이 성공적으로 저장되었습니다.")
            except Exception as e:
                QMessageBox.warning(self, "다운로드 실패", f"파일 저장 중 오류: {e}")

    def apply_strategy(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "알림", "전략을 선택해주세요.")
            return
        name = self.table.item(row, 1).text()
        QMessageBox.information(self, "전략 적용", f"{name} 전략을 적용했습니다.")
