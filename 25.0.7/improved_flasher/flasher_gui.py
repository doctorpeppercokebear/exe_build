#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESP32-S3 Firmware Flasher with GUI
개선된 GUI 기반 펌웨어 업로드 도구
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import sys
import os
import serial.tools.list_ports
import esptool
import io
from contextlib import redirect_stdout, redirect_stderr


class FirmwareFlasher:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32-S3 펌웨어 업로드 도구 v2.0")
        self.root.geometry("700x600")
        self.root.resizable(False, False)

        # 바이너리 파일 경로 설정
        if getattr(sys, "frozen", False):
            # PyInstaller로 빌드된 경우
            self.base_path = sys._MEIPASS
        else:
            # 일반 Python 스크립트 실행
            self.base_path = os.path.dirname(os.path.abspath(__file__))

        self.bootloader_path = os.path.join(self.base_path, "bootloader.bin")
        self.partitions_path = os.path.join(self.base_path, "partitions.bin")
        self.firmware_path = os.path.join(self.base_path, "firmware.bin")

        self.is_flashing = False
        self.setup_ui()
        self.refresh_ports()
        self.check_initial_port()
        self.auto_refresh_ports()
        
    def check_initial_port(self):
        """초기 포트 상태 확인 및 메시지 표시"""
        if self.port_var.get() and "찾을 수 없습니다" not in self.port_var.get():
            self.log("ESP32 장치가 준비되었습니다. '펌웨어 업로드' 버튼을 클릭하세요.", "SUCCESS")
        else:
            self.log("USB 케이블로 ESP32-S3 장치를 연결하세요.", "WARNING")

    def auto_refresh_ports(self):
        """5초마다 자동으로 포트 재검색"""
        if not self.is_flashing:    # 업로드 중이 아닐 때만 포트를 새로고침합니다.
            current_port = self.port_var.get()
            self.refresh_ports()

            # 새로운 포트가 발견되면 알림
            new_port = self.port_var.get()
            if new_port != current_port and "찾을 수 없습니다" not in new_port:  # 점 제거
                self.log(f"새로운 장치 감지: {new_port}", "INFO")

        # 5초 후에 다시 호출
        self.root.after(5000, self.auto_refresh_ports)


    def setup_ui(self):
        """UI 구성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 타이틀
        title_label = ttk.Label(
            main_frame, text="ESP32-S3 펌웨어 업로드", font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # COM 포트 선택
        ttk.Label(main_frame, text="COM 포트:", font=("Arial", 10)).grid(
            row=1, column=0, sticky=tk.W, pady=5
        )

        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(
            main_frame, textvariable=self.port_var, width=30, state="readonly"
        )
        self.port_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 5))

        refresh_btn = ttk.Button(
            main_frame, text="새로고침", command=self.refresh_ports
        )
        refresh_btn.grid(row=1, column=2, pady=5)

        # 전송 속도
        ttk.Label(main_frame, text="전송 속도:", font=("Arial", 10)).grid(
            row=2, column=0, sticky=tk.W, pady=5
        )

        self.baud_var = tk.StringVar(value="921600")
        baud_combo = ttk.Combobox(
            main_frame,
            textvariable=self.baud_var,
            values=["115200", "460800", "921600"],
            width=30,
            state="readonly",
        )
        baud_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 5))

        # 구분선
        ttk.Separator(main_frame, orient="horizontal").grid(
            row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15
        )

        # 파일 정보
        info_frame = ttk.LabelFrame(main_frame, text="펌웨어 파일 정보", padding="10")
        info_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        files_info = [
            ("Bootloader:", self.bootloader_path, "0x0"),
            ("Partitions:", self.partitions_path, "0x8000"),
            ("Firmware:", self.firmware_path, "0x10000"),
        ]

        for idx, (label, path, addr) in enumerate(files_info):
            ttk.Label(info_frame, text=label, font=("Arial", 9, "bold")).grid(
                row=idx, column=0, sticky=tk.W, pady=2
            )

            status = "✓" if os.path.isfile(path) else "✗"
            color = "green" if os.path.isfile(path) else "red"
            status_label = ttk.Label(
                info_frame, text=status, foreground=color, font=("Arial", 10, "bold")
            )
            status_label.grid(row=idx, column=1, padx=5)

            ttk.Label(
                info_frame, text=f"{addr} - {os.path.basename(path)}", font=("Arial", 9)
            ).grid(row=idx, column=2, sticky=tk.W, padx=5)

        # 진행률 바
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame, variable=self.progress_var, maximum=100, length=400
        )
        self.progress_bar.grid(
            row=5, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E)
        )

        # 상태 라벨
        self.status_var = tk.StringVar(value="준비됨")
        status_label = ttk.Label(
            main_frame, textvariable=self.status_var, font=("Arial", 10)
        )
        status_label.grid(row=6, column=0, columnspan=3, pady=5)

        # 로그 영역
        log_frame = ttk.LabelFrame(main_frame, text="로그", padding="5")
        log_frame.grid(
            row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10
        )

        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=12, width=80, font=("Consolas", 9)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 버튼 프레임
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=8, column=0, columnspan=3, pady=10)

        self.flash_btn = ttk.Button(
            btn_frame, text="펌웨어 업로드 시작", command=self.start_flashing, width=25
        )
        self.flash_btn.grid(row=0, column=0, padx=5)

        self.clear_btn = ttk.Button(
            btn_frame, text="로그 지우기", command=self.clear_log, width=15
        )
        self.clear_btn.grid(row=0, column=1, padx=5)

        # 그리드 가중치 설정
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(7, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

    def log(self, message, level="INFO"):
        """로그 메시지 추가"""
        self.log_text.insert(tk.END, f"[{level}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def clear_log(self):
        """로그 지우기"""
        self.log_text.delete(1.0, tk.END)

    def refresh_ports(self):
        """사용 가능한 COM 포트 새로고침 및 ESP32 자동 선택"""
        ports = serial.tools.list_ports.comports()
        port_list = [f"{port.device} - {port.description}" for port in ports]
        
        # ESP32 포트 찾기
        esp32_port = None
        for port in ports:
            # ESP32-S3 관련 키워드 검색
            desc_lower = port.description.lower()
            if any(keyword in desc_lower for keyword in ['esp32', 'cp210', 'ch340', 'serial', 'uart']):
                esp32_port = f"{port.device} - {port.description}"
                break
        
        if not port_list:
            port_list = ["포트를 찾을 수 없습니다"]
            self.log("사용 가능한 COM 포트를 찾을 수 없습니다.", "WARNING")
        else:
            self.log(f"{len(port_list)}개의 COM 포트를 발견했습니다.")
            # ESP32 포트를 찾았으면 자동 선택
            if esp32_port:
                self.log(f"ESP32 장치 자동 감지: {esp32_port}", "SUCCESS")
        
        self.port_combo["values"] = port_list
        
        # 포트 자동 선택
        if esp32_port:
            # ESP32 포트를 우선 선택
            self.port_var.set(esp32_port)
        elif port_list and "찾을 수 없습니다" not in port_list[0]:
            # ESP32가 없으면 첫 번째 포트 선택
            self.port_combo.current(0)


    def check_files(self):
        """필수 파일 존재 확인"""
        files = [
            ("Bootloader", self.bootloader_path),
            ("Partitions", self.partitions_path),
            ("Firmware", self.firmware_path),
        ]

        missing = []
        for name, path in files:
            if not os.path.isfile(path):
                missing.append(name)

        if missing:
            error_msg = f"다음 파일을 찾을 수 없습니다:\n" + "\n".join(missing)
            messagebox.showerror("파일 오류", error_msg)
            self.log(error_msg, "ERROR")
            return False
        return True

    def start_flashing(self):
        """펌웨어 업로드 시작 (자동화 버전)"""
        if self.is_flashing:
            messagebox.showwarning("경고", "이미 업로드가 진행 중입니다.")
            return
        
        # 포트 자동 재검색
        if not self.port_var.get() or "찾을 수 없습니다" in self.port_var.get():
            self.log("포트를 찾을 수 없습니다. 재검색 중...", "WARNING")
            self.refresh_ports()
            
            # 재검색 후에도 포트가 없으면
            if not self.port_var.get() or "찾을 수 없습니다" in self.port_var.get():
                messagebox.showerror(
                    "오류", 
                    "ESP32 장치를 찾을 수 없습니다.\n\n"
                    "1. USB 케이블이 연결되어 있는지 확인하세요.\n"
                    "2. 드라이버가 설치되어 있는지 확인하세요."
                )
                return
        
        # 파일 확인
        if not self.check_files():
            return
        
        # 확인 대화상자 제거 - 바로 실행
        # (원하면 유지 가능)
        port_name = self.port_var.get().split(" - ")[0]
        
        # 스레드로 업로드 실행
        self.is_flashing = True
        self.flash_btn.config(state="disabled")
        self.progress_var.set(0)
        
        thread = threading.Thread(target=self.flash_firmware, args=(port_name,))
        thread.daemon = True
        thread.start()

    def flash_firmware(self, port):
        """실제 펌웨어 업로드 실행"""
        try:
            self.status_var.set("연결 중...")
            self.log(f"\n{'='*60}")
            self.log(f"ESP32-S3 펌웨어 업로드 시작")
            self.log(f"포트: {port}")
            self.log(f"전송 속도: {self.baud_var.get()}")
            self.log(f"{'='*60}\n")

            # esptool 명령 구성
            command = [
                "--chip",
                "esp32s3",
                "--port",
                port,
                "--baud",
                self.baud_var.get(),
                "--no-stub",            # 스텁 사용 안 함
                "--before",
                "default_reset",
                "--after",
                "hard_reset",
                "write_flash",
                "-z",
                "--flash_mode",
                "dio",
                "--flash_freq",
                "80m",
                "--flash_size",
                "detect",
                "0x0",                  # bootloader 주소 수정
                self.bootloader_path,
                "0x8000",
                self.partitions_path,
                "0x10000",
                self.firmware_path,
            ]

            self.progress_var.set(10)
            self.status_var.set("Bootloader 업로드 중...")
            self.log("Bootloader 쓰는 중... (0x0)")

            # esptool 출력을 캡처하여 로그에 표시
            output_buffer = io.StringIO()
            with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
                esptool.main(command)

            # 출력 로그에 표시
            output = output_buffer.getvalue()
            for line in output.split("\n"):
                if line.strip():
                    self.log(line.strip())

            self.progress_var.set(100)
            self.status_var.set("업로드 완료!")
            self.log("\n" + "=" * 60)
            self.log("✓ 펌웨어 업로드가 성공적으로 완료되었습니다!", "SUCCESS")
            self.log("=" * 60 + "\n")

            messagebox.showinfo("성공", "펌웨어 업로드가 완료되었습니다!")

        except Exception as e:
            self.progress_var.set(0)
            self.status_var.set("오류 발생")
            error_msg = f"펌웨어 업로드 중 오류 발생:\n{str(e)}"
            self.log(error_msg, "ERROR")
            messagebox.showerror("오류", error_msg)

        finally:
            self.is_flashing = False
            self.flash_btn.config(state="normal")


def main():
    """메인 함수"""
    root = tk.Tk()
    app = FirmwareFlasher(root)
    root.mainloop()


if __name__ == "__main__":
    main()
