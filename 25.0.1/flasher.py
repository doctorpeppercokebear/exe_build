import esptool
import sys 
import os

def main():
    # 바이너리 파일 경로
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bootloader = os.path.join(script_dir, 'bin', 'bootloader.bin')
    partitions = os.path.join(script_dir,'partitions.bin')
    firmware = os.path.join(script_dir, 'firmware.bin')

        # 디버깅: 경로 출력
    print(f"스크립트 디렉토리: {script_dir}")
    print(f"Bootloader 경로: {bootloader}")
    print(f"  존재 여부: {os.path.isfile(bootloader)}")
    print(f"Partitions 경로: {partitions}")
    print(f"  존재 여부: {os.path.isfile(partitions)}")
    print(f"Firmware 경로: {firmware}")
    print(f"  존재 여부: {os.path.isfile(firmware)}")
    print()

    # 파일 존재 확인
    if not all([os.path.isfile(f) for f in [bootloader, partitions, firmware]]):
        print("Error: One or more binary files are missing.")
        input("엔터를 눌러 종료")
        return
    
    print("ESP32-S3 firmware flasher")
    print("=" * 50)
    port = input("COM 포트 입력하세요 (예시: com4): ").strip()

    if not port:
        print("포트를 입력하지 않았습니다.")
        input("엔터를 눌러 종료")
        return
    
    print(f"\n{port}에 펌웨어를 업로드 합니다.")

    # esptool을 사용하여 펌웨어 업로드
    command = [
        '--chip', 'esp32s3',
        '--port', port,
        '--baud', '921600',
        '--before', 'default-reset',     # 하이픈 사용
        '--after', 'hard-reset',          # 하이픈 사용
        'write-flash', '-z',              # 하이픈 사용
        '--flash-mode', 'dio',            # 하이픈 사용
        '--flash-size', 'detect',         # 하이픈 사용
        '0x1000', bootloader,
        '0x8000', partitions,
        '0x10000', firmware
    ]


    try:
        esptool.main(command)
        print("\n펌웨어 업로드가 완료되었습니다.")
    except Exception as e:
        print(f"\n펌웨어 업로드 중 오류가 발생했습니다: {e}")

    input("엔터를 눌러 종료")

if __name__ == "__main__":
    main()# flasher.py