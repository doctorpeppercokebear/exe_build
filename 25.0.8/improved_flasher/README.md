# ESP32-S3 펌웨어 업로드 도구 v2.0

개선된 GUI 기반 ESP32-S3 펌웨어 플래시 도구입니다.

## 주요 특징

✨ **사용자 친화적 GUI**
- 직관적인 그래픽 인터페이스
- 실시간 진행률 표시
- 상세한 로그 출력

🔌 **자동 COM 포트 감지**
- 연결된 모든 시리얼 포트 자동 검색
- 포트 설명과 함께 표시
- 새로고침 버튼으로 즉시 업데이트

📦 **단일 EXE 파일**
- 모든 바이너리 파일 포함
- 추가 설치 불필요
- 어디서나 실행 가능

🛡️ **안전한 업로드**
- 파일 존재 확인
- 업로드 전 확인 대화상자
- 상세한 에러 메시지

---

## 빌드 방법

### 사전 요구사항

- Python 3.8 이상
- PowerShell (Windows)
- 바이너리 파일:
  - `bootloader.bin`
  - `partitions.bin`
  - `firmware.bin`

### 빌드 단계

1. **바이너리 파일 복사**
   
   다음 3개 파일을 `improved_flasher` 폴더로 복사하세요:
   ```
   fluorescence_firware_v3_firmware/release/
   └── bootloader.bin
   └── partitions.bin
   └── firmware.bin
   ```

2. **PowerShell 스크립트 실행**
   
   ```powershell
   cd fluorescence_firware_v3_firmware/improved_flasher
   .\build_exe.ps1
   ```

3. **빌드 완료**
   
   빌드가 완료되면 `dist` 폴더에 `ESP32-S3_Flasher.exe` 파일이 생성됩니다.

### 빌드 스크립트가 하는 일

1. ✓ 필수 바이너리 파일 확인
2. ✓ Python 가상환경 생성 및 활성화
3. ✓ 필요한 패키지 설치 (esptool, pyserial 등)
4. ✓ PyInstaller로 단일 EXE 파일 생성
5. ✓ 빌드 결과 확인

---

## 사용 방법

### 최종 사용자용

1. **프로그램 실행**
   - `ESP32-S3_Flasher.exe` 파일을 더블클릭

2. **COM 포트 선택**
   - ESP32-S3 보드를 USB로 연결
   - 드롭다운에서 해당 포트 선택
   - 포트가 보이지 않으면 "새로고침" 클릭

3. **전송 속도 선택**
   - 기본값: 921600 (권장)
   - 문제 발생 시: 460800 또는 115200 시도

4. **업로드 시작**
   - "펌웨어 업로드 시작" 버튼 클릭
   - 확인 대화상자에서 "예" 선택
   - 진행률과 로그 확인

5. **완료**
   - "업로드 완료" 메시지 확인
   - ESP32-S3 자동 재시작

### 문제 해결

**포트가 감지되지 않을 때:**
- USB 케이블 연결 확인
- USB 드라이버 설치 확인 (CP210x, CH340 등)
- 장치 관리자에서 포트 확인

**업로드 실패 시:**
- 전송 속도를 낮춰보세요 (460800 또는 115200)
- 보드를 부트로더 모드로 진입 (BOOT 버튼 누른 채 연결)
- USB 케이블 교체 시도

**에러 메시지:**
- 로그 창의 상세 메시지 확인
- 빨간색 에러 메시지 참고

---

## 배포

### 방법 1: 단일 EXE 파일 배포 (권장)

```
ESP32-S3_Flasher.exe
```

이 파일 하나만 배포하면 됩니다. 모든 필요한 파일이 포함되어 있습니다.

### 방법 2: 사용 설명서와 함께 배포

```
ESP32-S3_Firmware/
├── ESP32-S3_Flasher.exe
├── 사용설명서.pdf (선택사항)
└── README.txt
```

### 배포 패키지 예시

```
ESP32-S3_Firmware_v25.0.3.zip
└── ESP32-S3_Flasher.exe
└── 사용방법.txt
```

---

## 기술 정보

### 사용된 라이브러리

- **esptool** - ESP32 펌웨어 업로드
- **pyserial** - 시리얼 통신
- **tkinter** - GUI 인터페이스 (Python 기본 내장)
- **PyInstaller** - EXE 빌드

### 플래시 주소

| 파일 | 주소 | 설명 |
|------|------|------|
| bootloader.bin | 0x1000 | 부트로더 |
| partitions.bin | 0x8000 | 파티션 테이블 |
| firmware.bin | 0x10000 | 메인 펌웨어 |

### 지원 보드

- ESP32-S3 시리즈
- 다른 ESP32 보드는 코드 수정 필요 (--chip 파라미터 변경)

---

## 개발자 정보

### 디렉토리 구조

```
improved_flasher/
├── flasher_gui.py          # 메인 GUI 프로그램
├── requirements.txt         # Python 패키지 의존성
├── build_exe.ps1           # 빌드 스크립트
├── README.md               # 이 파일
├── bootloader.bin          # 부트로더 (빌드 시 필요)
├── partitions.bin          # 파티션 테이블 (빌드 시 필요)
├── firmware.bin            # 펌웨어 (빌드 시 필요)
└── dist/                   # 빌드 결과물
    └── ESP32-S3_Flasher.exe
```

### 코드 수정

펌웨어 주소나 보드 타입을 변경하려면 `flasher_gui.py`의 다음 부분을 수정하세요:

```python
command = [
    '--chip', 'esp32s3',      # 보드 타입
    '--port', port,
    '--baud', self.baud_var.get(),
    # ... (중략) ...
    '0x1000', self.bootloader_path,   # 부트로더 주소
    '0x8000', self.partitions_path,   # 파티션 주소
    '0x10000', self.firmware_path     # 펌웨어 주소
]
```

---

## 라이선스

이 도구는 내부 사용 목적으로 제작되었습니다.

---

## 변경 이력

### v2.0 (2024-10-24)
- ✨ GUI 인터페이스 추가
- ✨ 자동 COM 포트 감지
- ✨ 실시간 진행률 표시
- ✨ 상세 로그 출력
- ✨ 단일 EXE 파일로 배포
- ✨ 파일 존재 확인 기능
- ✨ 업로드 전 확인 대화상자

### v1.0
- 기본 커맨드라인 인터페이스
- 수동 COM 포트 입력
