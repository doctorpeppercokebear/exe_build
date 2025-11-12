# ESP32-S3 Firmware Flasher 빌드 스크립트 v25.0.10
# PowerShell 스크립트로 단일 EXE 파일 생성

Write-Host "================================" -ForegroundColor Cyan
Write-Host "ESP32-S3 Flasher v25.0.10 빌드 시작" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 현재 디렉토리 확인
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# 1. 필요한 바이너리 파일 확인
Write-Host "[1/5] 바이너리 파일 확인 중..." -ForegroundColor Yellow

$requiredFiles = @("bootloader.bin", "partitions.bin", "firmware.bin")
$missingFiles = @()

foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
        Write-Host "  ✗ $file - 없음" -ForegroundColor Red
    } else {
        Write-Host "  ✓ $file - 발견" -ForegroundColor Green
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "오류: 다음 파일들을 현재 디렉토리에 복사해주세요:" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "  - $file" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "바이너리 파일들은 다음 위치에서 찾을 수 있습니다:" -ForegroundColor Yellow
    Write-Host "  - fluorescence_firware_v3_firmware/release/" -ForegroundColor Yellow
    Write-Host "  또는" -ForegroundColor Yellow
    Write-Host "  - fluorescence_firware_v3_firmware/25.0.x/" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

Write-Host ""

# 2. Python 가상환경 확인 및 생성
Write-Host "[2/5] Python 환경 설정 중..." -ForegroundColor Yellow

if (-not (Test-Path "venv")) {
    Write-Host "  가상환경 생성 중..." -ForegroundColor Gray
    python -m venv venv
}

# 가상환경 활성화
Write-Host "  가상환경 활성화 중..." -ForegroundColor Gray
& ".\venv\Scripts\Activate.ps1"

Write-Host ""

# 3. 의존성 설치
Write-Host "[3/5] 필요한 패키지 설치 중..." -ForegroundColor Yellow
Write-Host "  pip 업그레이드 중..." -ForegroundColor Gray
python -m pip install --upgrade pip --quiet

Write-Host "  requirements.txt 설치 중..." -ForegroundColor Gray
pip install -r requirements.txt --quiet

Write-Host ""

# 4. PyInstaller로 빌드
Write-Host "[4/5] EXE 파일 빌드 중..." -ForegroundColor Yellow
Write-Host "  이 과정은 1-2분 정도 소요될 수 있습니다..." -ForegroundColor Gray
Write-Host ""

# PyInstaller 명령 실행 (버전 정보가 포함된 이름으로 빌드)
pyinstaller --noconfirm `
    --onefile `
    --windowed `
    --name "v25.0.10_ESP32-S3_Flasher" `
    --icon=NONE `
    --add-data "bootloader.bin;." `
    --add-data "partitions.bin;." `
    --add-data "firmware.bin;." `
    --hidden-import=esptool `
    --hidden-import=serial `
    --hidden-import=serial.tools `
    --hidden-import=serial.tools.list_ports `
    flasher_gui.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "빌드 중 오류가 발생했습니다!" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""

# 5. 빌드 결과 확인
Write-Host "[5/5] 빌드 완료!" -ForegroundColor Yellow

$exePath = "dist\v25.0.10_ESP32-S3_Flasher.exe"

if (-not (Test-Path $exePath)) {
    Write-Host ""
    Write-Host "오류: EXE 파일을 찾을 수 없습니다! 빌드 로그를 확인해주세요." -ForegroundColor Red
    Write-Host ""
    pause
    exit 1
}

# 빌드 성공
$exeSize = (Get-Item $exePath).Length / 1MB
Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "빌드 성공! v25.0.10" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "생성된 파일:" -ForegroundColor Cyan
Write-Host "  위치: $scriptDir\dist\v25.0.10_ESP32-S3_Flasher.exe" -ForegroundColor White
Write-Host "  크기: $([math]::Round($exeSize, 2)) MB" -ForegroundColor White
Write-Host ""
Write-Host "이 EXE 파일은 단독으로 실행 가능하며," -ForegroundColor Yellow
Write-Host "모든 필요한 파일이 포함되어 있습니다." -ForegroundColor Yellow
Write-Host ""
Write-Host "v25.0.10 주요 업데이트:" -ForegroundColor Cyan
Write-Host "  ✓ 실시간 진행률 표시 (퍼센트)" -ForegroundColor Green
Write-Host "  ✓ 단계별 업로드 상태 메시지" -ForegroundColor Green
Write-Host "  ✓ 향상된 사용자 피드백" -ForegroundColor Green
Write-Host ""
Write-Host "배포 방법:" -ForegroundColor Cyan
Write-Host "  1. dist\v25.0.10_ESP32-S3_Flasher.exe 파일만 배포하면 됩니다" -ForegroundColor White
Write-Host "  2. 사용자는 이 파일을 더블클릭하여 실행할 수 있습니다" -ForegroundColor White
Write-Host ""

# dist 폴더 열기 옵션
try {
    $openFolder = Read-Host "빌드된 파일이 있는 폴더를 여시겠습니까? (Y/N)"
    if ($openFolder.Trim().ToUpper() -eq "Y") {
        explorer "dist"
    }
} catch {
    Write-Host "폴더를 열 수 없습니다. 수동으로 dist 폴더를 확인해주세요." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "정리 팁:" -ForegroundColor Cyan
Write-Host "  - build/ 및 __pycache__/ 폴더는 삭제해도 됩니다" -ForegroundColor Gray
Write-Host "  - .spec 파일은 재빌드시 참고용으로 보관할 수 있습니다" -ForegroundColor Gray
Write-Host ""