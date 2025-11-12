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
import re
import time
from contextlib import redirect_stdout, redirect_stderr


class FirmwareFlasher:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32-S3 펌웨어 업로드 도구 v2.0")
        self.root.geometry("800x700")
        self.root.resizable(True, True)  # 사용자가 크기 조절 가능하게 변경
        self.root.minsize(700, 600)  # 최소 크기 설정

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
            self.log(
                "ESP32 장치가 준비되었습니다. '펌웨어 업로드' 버튼을 클릭하세요.",
                "SUCCESS",
            )
        else:
            self.log("USB 케이블로 ESP32-S3 장치를 연결하세요.", "WARNING")

    def auto_refresh_ports(self):
        """5초마다 자동으로 포트 재검색"""
        if not self.is_flashing:  # 업로드 중이 아닐 때만 포트를 새로고침합니다.
            current_port = self.port_var.get()
            self.refresh_ports()

            # 새로운 포트가 발견되면 알림
            new_port = self.port_var.get()
            if (
                new_port != current_port and "찾을 수 없습니다" not in new_port
            ):  # 점 제거
                self.log(f"새로운 장치 감지: {new_port}", "INFO")

        # 30초 후에 다시 호출
        self.root.after(30000, self.auto_refresh_ports)

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

        # 진행률 바와 퍼센트 표시
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=5, column=0, columnspan=3, pady=15, sticky=(tk.W, tk.E))
        progress_frame.columnconfigure(0, weight=1)  # 가운데 정렬을 위한 설정

        # 퍼센트 라벨 (가운데 정렬)
        self.percent_var = tk.StringVar(value="0%")
        percent_label = ttk.Label(
            progress_frame, textvariable=self.percent_var, font=("Arial", 10, "bold")
        )
        percent_label.grid(row=0, column=0, pady=(0, 5))

        # 진행률 바 (가운데 정렬)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var, maximum=100, length=450
        )
        self.progress_bar.grid(row=1, column=0, pady=(0, 5), padx=20)

        # 상태 라벨 (가운데 정렬)
        self.status_var = tk.StringVar(value="준비됨")
        status_label = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            font=("Arial", 10),
            anchor="center",
        )
        status_label.grid(row=6, column=0, columnspan=3, pady=10)

        # 로그 영역
        log_frame = ttk.LabelFrame(main_frame, text="로그", padding="5")
        log_frame.grid(
            row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10
        )

        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=15, width=90, font=("Consolas", 9), wrap=tk.WORD
        )
        self.log_text.grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5
        )

        # 버튼 프레임
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=8, column=0, columnspan=3, pady=15)

        self.flash_btn = ttk.Button(
            btn_frame, text="펌웨어 업로드 시작", command=self.start_flashing, width=28
        )
        self.flash_btn.grid(row=0, column=0, padx=10, pady=5)

        self.clear_btn = ttk.Button(
            btn_frame, text="로그 지우기", command=self.clear_log, width=18
        )
        self.clear_btn.grid(row=0, column=1, padx=10, pady=5)

        # 그리드 가중치 설정 - 창 크기 조정 시 레이아웃 최적화
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(7, weight=1)  # 로그 영역이 확장되도록

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
            if any(
                keyword in desc_lower
                for keyword in ["esp32", "cp210", "ch340", "serial", "uart"]
            ):
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
                    "2. 드라이버가 설치되어 있는지 확인하세요.",
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

            # 각 파일별 업로드 진행률 관리
            files_to_flash = [
                ("Bootloader", self.bootloader_path, "0x0"),
                ("Partitions", self.partitions_path, "0x8000"),
                ("Firmware", self.firmware_path, "0x10000"),
            ]

            total_files = len(files_to_flash)

            # 연결 단계
            self.update_progress(5, "ESP32-S3에 연결 중... (5%)")

            # esptool 명령 구성
            command = [
                "--chip",
                "esp32s3",
                "--port",
                port,
                "--baud",
                self.baud_var.get(),
                "--no-stub",
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
                "0x0",
                self.bootloader_path,
                "0x8000",
                self.partitions_path,
                "0x10000",
                self.firmware_path,
            ]

            # 연결 완료
            self.update_progress(10, "연결 완료, 펌웨어 업로드 시작... (10%)")

            # esptool 실행 (출력을 실시간으로 캡처)
            self.run_esptool_with_progress(command)

            self.update_progress(100, "업로드 완료! (100%)")
            self.log("\n" + "=" * 60)
            self.log("✓ 펌웨어 업로드가 성공적으로 완료되었습니다!", "SUCCESS")
            self.log("=" * 60 + "\n")

            messagebox.showinfo("성공", "펌웨어 업로드가 완료되었습니다!")

        except Exception as e:
            self.update_progress(0, "오류 발생")
            error_msg = f"펌웨어 업로드 중 오류 발생:\n{str(e)}"
            self.log(error_msg, "ERROR")
            messagebox.showerror("오류", error_msg)

        finally:
            self.is_flashing = False
            self.flash_btn.config(state="normal")

    def update_progress(self, percentage, status_text):
        """진행률과 상태 업데이트"""
        self.progress_var.set(percentage)
        self.percent_var.set(f"{int(percentage)}%")
        self.status_var.set(status_text)
        self.root.update_idletasks()

    def run_esptool_with_progress(self, command):
        """esptool 실행하면서 진행률 추적"""
        import subprocess
        import sys

        # esptool 프로세스 실행
        process = subprocess.Popen(
            [sys.executable, "-m", "esptool"] + command[1:],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
        )

        current_phase = "연결"
        file_names = ["Bootloader", "Partitions", "Firmware"]
        file_addresses = ["0x00000000", "0x00008000", "0x00010000"]
        current_file_index = -1
        base_progress = 10  # 연결 완료 후 시작 진행률
        phase_progress_range = 90 / 4  # 연결(10%) + 3개 파일(각 22.5%) = 100%

        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break

            if output:
                line = output.strip()
                self.log(line)

                # 연결 완료 감지
                if "Chip is ESP32-S3" in line:
                    self.update_progress(15, "ESP32-S3 감지 완료... (15%)")

                elif "Uploading stub" in line:
                    self.update_progress(20, "업로드 스텁 준비 중... (20%)")

                # 각 파일 쓰기 시작 감지
                elif "Writing" in line and "at 0x" in line:
                    # 주소로 현재 파일 파악
                    for i, addr in enumerate(file_addresses):
                        if addr.replace("0x", "0x").lower() in line.lower():
                            if current_file_index != i:
                                current_file_index = i
                                current_phase = file_names[i]
                                base_file_progress = 25 + (i * phase_progress_range)
                                self.update_progress(
                                    base_file_progress,
                                    f"{current_phase} 업로드 시작... ({int(base_file_progress)}%)",
                                )
                            break

                    # 진행률 패턴 매칭 (예: "Writing at 0x00008000... (100 %)")
                    progress_match = re.search(r"\((\d+)\s*%\)", line)
                    if progress_match and current_file_index >= 0:
                        file_percent = int(progress_match.group(1))

                        # 전체 진행률 계산 (각 파일당 22.5% 할당)
                        base_file_progress = 25 + (
                            current_file_index * phase_progress_range
                        )
                        total_progress = base_file_progress + (
                            file_percent * phase_progress_range / 100
                        )

                        current_file = file_names[current_file_index]
                        status_text = (
                            f"{current_file} 업로드 중... ({int(total_progress)}%)"
                        )

                        self.update_progress(total_progress, status_text)

                # 파일 완료 감지
                elif "Hash of data verified" in line and current_file_index >= 0:
                    completed_file = file_names[current_file_index]
                    completion_progress = 25 + (
                        (current_file_index + 1) * phase_progress_range
                    )
                    status_text = (
                        f"{completed_file} 완료! ({int(completion_progress)}%)"
                    )
                    self.update_progress(completion_progress, status_text)

                    # 다음 파일 예고 (마지막 파일이 아닌 경우)
                    if current_file_index < len(file_names) - 1:
                        time.sleep(0.5)  # 잠시 완료 상태 표시
                        next_file = file_names[current_file_index + 1]
                        status_text = (
                            f"{next_file} 준비 중... ({int(completion_progress)}%)"
                        )
                        self.update_progress(completion_progress, status_text)

                # 하드 리셋 감지
                elif "Hard resetting" in line:
                    self.update_progress(95, "장치 재시작 중... (95%)")

                # 오류 감지
                elif "Error" in line or "Failed" in line:
                    self.log(f"오류 감지: {line}", "ERROR")

        # 프로세스 완료 대기
        return_code = process.wait()
        if return_code != 0:
            raise Exception(f"esptool 실행 실패 (코드: {return_code})")


def main():
    """메인 함수"""
    root = tk.Tk()
    app = FirmwareFlasher(root)
    root.mainloop()


if __name__ == "__main__":
    main()
