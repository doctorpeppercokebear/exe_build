Flasher Release Package

Files included:
- flasher.exe : Windows executable flasher (Python script bundled with PyInstaller)
- bootloader.bin
- partitions.bin
- firmware.bin
- run_flasher.bat : convenience batch to run flasher and keep console open

Quick start:
1. Ensure USB serial driver is installed for your board.
2. Open a PowerShell and change to this folder.
3. Run the batch or execute the flasher with the COM port:
   .\run_flasher.bat COM42
   or
   .\flasher.exe --port COM42 --baud 460800 --bootloader bootloader.bin --partitions partitions.bin --firmware firmware.bin

Notes:
- Confirm flash addresses (0x1000, 0x8000, 0x10000) match your project partition table before large-scale flashing.
- For safety, verify checksums of binary files before flashing.
