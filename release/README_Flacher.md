Flasher EXE (Method A)

This folder contains a small Python-based flasher wrapper that uses esptool to write firmware to ESP32/ESP32-S2/ESP32-S3 devices.

Files:
- flasher.py          : Main Python script to flash firmware. Can be bundled into an EXE with PyInstaller.
- requirements.txt    : Python dependencies (esptool, pyserial, pyinstaller)
- build_flasher.ps1   : PowerShell helper to build the EXE on Windows

Quick start (Windows PowerShell):
1) Install Python 3.8+ and add to PATH.
2) Open PowerShell in this folder and install dependencies:
   python -m pip install --upgrade pip
   pip install -r requirements.txt

3) Build EXE without embedding firmware (distribute firmware.bin next to EXE):
   .\build_flasher.ps1

4) Build EXE with embedded firmware (firmware.bin will be included inside the EXE):
   .\build_flasher.ps1 -EmbedFirmware -Firmware firmware.bin

Run examples:
- External firmware file (recommended):
  .\dist\flasher.exe --port COM4 --baud 460800 --firmware firmware.bin --address 0x10000

- Embedded firmware (if you built with -EmbedFirmware):
  .\dist\flasher.exe --port COM4 --baud 460800 --address 0x10000

Notes and caveats:
- For reliable flashing, make sure the correct COM driver is installed and device is placed into bootloader mode if required by your board.
- The script tries to call esptool via Python API when available; PyInstaller bundling should include esptool if installed in the environment.
- When bundling with --onefile + --add-data, PyInstaller extracts the data to a temporary folder at runtime; the script handles that by accepting a firmware path pointing to the extracted file.
- Test the EXE on a Windows machine that has no conflicting AV rules; consider code signing for wide distribution.
