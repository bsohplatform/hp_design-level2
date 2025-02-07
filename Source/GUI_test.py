import sys
import subprocess
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton


class PDFViewer(QMainWindow):
    def __init__(self, pdf_path):
        super().__init__()
        self.setWindowTitle("Open PDF with External Viewer")
        self.resize(300, 100)

        self.pdf_path = pdf_path  # PDF 파일 절대 경로 설정

        # 메인 위젯과 레이아웃 설정
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # PDF 열기 버튼 추가
        open_button = QPushButton("Open PDF")
        open_button.clicked.connect(self.open_pdf)
        layout.addWidget(open_button)

    def open_pdf(self):
        try:
            # 시스템의 기본 PDF 뷰어로 PDF 파일 열기
            if sys.platform == "win32":  # Windows
                subprocess.run(["start", self.pdf_path], shell=True)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", self.pdf_path])
            else:  # Linux/Unix
                subprocess.run(["xdg-open", self.pdf_path])
        except Exception as e:
            print(f"Failed to open PDF: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # PDF 파일 절대 경로 설정 (수정 필요)
    pdf_file_path = r"D:\absolute\path\to\your\file.pdf"  # 여기에 PDF 파일 절대 경로 입력

    # PDFViewer 실행
    viewer = PDFViewer(pdf_file_path)
    viewer.show()
    sys.exit(app.exec())
