import argparse
import time
import sys
import hashlib
import os
import re
from scapy.all import sniff, wrpcap
import threading
import signal
import shutil

# 파일 시그니처 정의
FILE_SIGNATURES = {
    
    'pdf': b'%PDF',
    'gif': [b'GIF87a', b'GIF89a'],
    'png': b'\x89PNG\r\n\x1a\n',
    'jpg': [b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xe1', b'\xff\xd8\xff\xe8', b'\xff\xd8\xff\xdb', b'\xff\xd8\xff\xee'],
    'zip': b'PK\x03\x04',
    'exe': b'MZ',
    'msi': b'MZ',  
    'ico': b'\x00\x00\x01\x00',
    'cur': b'\x00\x00\x02\x00',
    'mpg': b'\x00\x00\x01\xb3',
    'doc': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1', b'\xec\xa5\xc1\x00', b'\xbe\x00\x00\x00\xab\x00\x00\x00'],
    'xls': [b'\xfd\xff\xff\xff', b'\xfe\xff'],
    'ppt': [b'\x00\x6e\x1e\xf0', b'\xfd\xff\xff\xff'],
    'mp4': b'\x00\x00\x00\x18ftyp',
    'mov': b'moov',
    'bmp': b'BM',
    'tar': b'ustar',
    'gz': [b'\x1f\x8b\x08', b'\x1f\x9d', b'\x1f\xa0'],
    'avi': b'RIFF',
    'wav': b'RIFF',
    'mp3': [b'ID3', b'\xff\xfb'],
    'psd': b'8BPS',
    'rtf': b'{\\rtf',
    'xml': b'<?xml',
    'json': b'{',
    'flv': b'FLV',
    'rm': b'.RMF',
    'tif': [b'II*\x00', b'MM\x00*'],
    'arj': b'\x60\xea',
    'rar': b'Rar!',
    '3gp': [b'\x00\x00\x00\x14ftyp3gp', b'\x00\x00\x00\x20ftyp3g2'],
    'aac': b'ADIF',
    'amr': b'#!AMR',
    'iso': b'CD001',
    'lha': [b'\x2D\x6C\x68', b'\x2D\x6C\x68\x35'],
    'eps': b'%!PS-Adobe',
    'fli': [b'\xAF\x11', b'\x01\x11\xAF'],
    'qxd': [b'\x00\x00\x49\x49\x58\x50\x52', b'\x00\x00\x4D\x4D\x58\x50\x52'],
    'ai': b'%!PS-Adobe',
    'wma': b'0&\xb2u',
    'wmv': b'0&\xb2u',
    'asf': b'0&\xb2u',
    '7z': b'7z\xbc\xaf\x27\x1c',
    'bz2': b'BZh',
    'cab': b'MSCF',
    'dmg': b'x',
    'jar': b'PK\x03\x04',
    'gzip': b'\x1F\x8B',
    'arc': b'\x1A',
    'jpeg': [b'\xFF\xD8\xFF\xDB', b'\xFF\xD8\xFF\xEE', b'\xFF\xD8\xFF\xE1'],
    'pif': b'\x00',
    'mac': b'\x00\x00\x00\x02',
    'wmf': b'\xd7\xcd\xc6\x9a',
    'mp2': b'\xff\xf3',
    'dbf': [b'\x02', b'\x03'],
    'db': b'\x00\x01',
    'mdb': b'\x00\x01\x00\x00Standard Jet DB',
    'emf': b'\x01\x00\x00\x00',
    'docx': b'PK\x03\x04',
    'pptx': b'PK\x03\x04',
    'xlsx': b'PK\x03\x04',

}

# 랜섬웨어와 관련된 확장자 목록
RANSOMWARE_EXTENSIONS = [
    # 랜섬웨어로 의심되는 확장자 목록

    'locky', 'zepto', 'odin', 'cerber', 'crysis', 'wallet', 'zzzzz', 'ccc', 'exx', 'ecc', 'crypt', 'crab', 'cbf',
    'arena', 'dharma', 'arrow', 'grt', 'ryuk', 'phobos', 'krab', 'fucked', 'crypted', 'satan', 'xrat', 'gandcrab', 
    'cyborg', 'salus', 'ciphered', 'shiva', 'stupid', 'why', 'weapologize', 'grandcrab', 'megacortex', 'revil', 
    'ekvf', 'fairytail', 'exorcist', 'mamba', 'killing_time', 'recovery', 'volcano', 'pscrypt', 'tcps', 'fuxsocy', 
    'heof', 'matrix', 'medusa', 'snake', 'ftcode', 'calipso', 'encrypted', 'vault', 'shariz', 'tor', 'globeimposter', 
    'kogda', 'crypmic', 'bokbot', 'dewar', 'defray', 'greystar', 'pclock', 'moisha', 'zcrypt', 'djvu', 'dotmap', 
    'sodinokibi', 'calipto', 'fun', 'worm', 'inferno', 'medy', 'fudcrypt', 'zohar', 'nig', 'ogre', 'uizsdgpo', 
    'hermes', 'nellyson', 'pay', 'bepow', 'futc', 'suck', 'f**ked', 'foxf***r', 'hotjob', 'gusar', 'jigsaw', 'oklah', 
    'lockfile', 'aesc', 'wb', 'tycoon', 'careto', 'azov', 'conti', 'ragnarok', 'crippled', 'trosy', 'johnny', 'regen', 
    'whatthe', '000', 'hitler', 'somethinghere', 'uw', 'anubi', 'notgotenough', 'justforyou', 'bondy', 'ark', 'kubos', 
    'police', 'aprilfool', 'bitch', 'crisis', 'teerac', 'long', 'infom', 'woswos', 'uw4w', 'ctrb', 'purge', 'fiwlgphz', 
    'platano', 'pro', 'locked', 'eyy', 'whythis', 'k0der', 'joker', 'fucku', 'charm', 'doubleup', 'payup', 'firecrypt', 
    'miyake', 'senpai', 'onspeed', 'fxckoff', 'zer0', 'p0rn', 'beethoven', 'im sorry', 'kuba', 'hahaha', '555', 
    'sexx', 'fuckyou', 'supercrypt', 'gudrotka', 'catchmeifyoucan', 'bambam', 'lucy', 'sadism', 'fedup', 'makop', 
    'alpha', 'master', 'mcafee', 'bastard', 'locki', 'striker', 'grimly', 'cryptolocker', 'kukaracha', 'kraken', 
    'supersystem', 'hot', 'ispy', 'newversion', 'payfast', 'futurat', 'unlock', 'kkk', 'openme', 'blablabla', 
    'goof', 'psycho', 'trigger', 'memeware', 'emotet', 'wannacry', 'notpetya', 'mazefuck', 'mazelocker', 'pegasus', 
    'sodinokibi', 'rdp', 'kodg', 'covm', 'cazw', 'egregor', 'revil', 'recovery', 'sodin', 'kodc', 'gdc', 'gdcb', 
    'grb', 'egregor', 'medusalocker', 'medusa', 'phobos', 'ransom', 'makop', 'mountlocker', 'avoslocker', 'cuba', 
    'kaseya', 'kaseyacrypt', 'blackcat', 'alphv', 'lorenz', 'lockbit', 'abcd', 'lukitus', 'moqs', 'thunderx'

]

# 네트워크 패킷 캡처와 악성 패킷 필터링 기능
stop_sniffing = False  # 패킷 캡처 중지 플래그
pcap_file = 'captured_packets.pcap'  # 패킷 저장 파일
CANARY_VALUE = b'ANTISIG'  # 카나리 값 (특정한 값으로 설정)

def print_ascii_art():  # 프로그램 시작시 표기될 아스키아트 (ANTI SIGNATURE)

    ascii_art = """

    █████╗ ███╗   ██╗████████╗██╗    ███████╗██╗ ██████╗ ███╗   ██╗ █████╗ ████████╗██╗   ██╗██████╗ ███████╗
    ██╔══██╗████╗  ██║╚══██╔══╝██║    ██╔════╝██║██╔════╝ ████╗  ██║██╔══██╗╚══██╔══╝██║   ██║██╔══██╗██╔════╝
    ███████║██╔██╗ ██║   ██║   ██║    ███████╗██║██║  ███╗██╔██╗ ██║███████║   ██║   ██║   ██║██████╔╝█████╗  
    ██╔══██║██║╚██╗██║   ██║   ██║    ╚════██║██║██║   ██║██║╚██╗██║██╔══██║   ██║   ██║   ██║██╔══██╗██╔══╝  
    ██║  ██║██║ ╚████║   ██║   ██║    ███████║██║╚██████╔╝██║ ╚████║██║  ██║   ██║   ╚██████╔╝██║  ██║███████╗
    ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝    ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝
    
    """
    
    print(ascii_art)

def show_loading_effect():  # 로딩 효과 출력

    for _ in range(10):

        sys.stdout.write(". ")    
        sys.stdout.flush()
        
        time.sleep(0.5)
    
    print()

def calculate_file_hash(file_path, hash_algorithm='sha256'):    # 파일 해시 계산
    
    hash_func = hashlib.new(hash_algorithm)
    
    try:
    
        with open(file_path, 'rb') as f:
    
            while chunk := f.read(8192):
    
                hash_func.update(chunk)
    
    except FileNotFoundError:
    
        print(f"Error: {file_path} 파일을 찾을 수 없습니다.")
    
        return None

    return hash_func.hexdigest()

def check_file_integrity(file_path, expected_hash=None):    # 파일 무결성 확인
    
    try:
    
        with open(file_path, 'rb') as f:
    
            file_signature = f.read(20)
    
    except FileNotFoundError:
    
        print(f"Error: {file_path} 파일을 찾을 수 없습니다.")
    
        return
    
    # 파일 확장자 추출
    file_extension = file_path.split('.')[-1].lower()

    # 랜섬웨어 관련 확장자 확인
    is_ransomware_extension = file_extension in RANSOMWARE_EXTENSIONS

    # 파일 시그니처와 확장자 비교
    suspicious = False
    
    if file_extension in FILE_SIGNATURES:
        
        expected_signatures = FILE_SIGNATURES[file_extension]
        
        if not isinstance(expected_signatures, list):
        
            expected_signatures = [expected_signatures]
        
        if any(file_signature.startswith(sig) for sig in expected_signatures):
        
            print(f"{file_path}의 파일 시그니처가 정상입니다. 파일 형식: {file_extension.upper()}")
        
        else:
        
            print(f"경고: {file_path}의 파일 시그니처가 예상과 다릅니다. 파일 형식: {file_extension.upper()}")
        
            suspicious = True
    
    else:
        
        print(f"알 수 없는 확장자입니다: {file_extension}")
        
        suspicious = True

    # 파일이 손상되거나 암호화된 것으로 의심되는 경우
    if suspicious:
        
        if is_ransomware_extension:
        
            print(f"경고: {file_path}의 파일이 암호화되었거나 손상된 것으로 보입니다. 랜섬웨어에 감염된 파일입니다.")
        
        else:
        
            print(f"경고: {file_path}의 파일이 암호화되었거나 손상된 것으로 보입니다. 랜섬웨어 감염 의심 파일입니다.")

    # 해시 무결성 검사 수행
    if expected_hash:
        
        calculated_hash = calculate_file_hash(file_path)
        
        if calculated_hash and calculated_hash != expected_hash:
        
            print(f"경고: {file_path}의 파일 해시 무결성이 훼손되었습니다.")
        
        elif calculated_hash:
        
            print(f"{file_path}의 파일 해시가 무결합니다.")

def check_for_ransomware(file_path):    # 파일 이름 패턴 분석
    
    file_name = file_path.split('/')[-1].lower()
    
    suspicious = False
    
    # 랜섬웨어 의심 확장자
    if any(ext in file_name for ext in RANSOMWARE_EXTENSIONS):
        
        print(f"경고: {file_path}는 랜섬웨어와 관련된 확장자를 포함하고 있습니다.")
        
        suspicious = True
    
    # 랜섬웨어 의심 이름 패턴
    if "readme" in file_name or "decrypt" in file_name:
        
        print(f"경고: {file_path}는 랜섬웨어 관련 파일일 수 있습니다 (이름 패턴 감지됨).")
        
        suspicious = True
    
    if not suspicious:
        
        print(f"{file_path}는 랜섬웨어에 감염되지 않은 정상 파일입니다.")
        
def apply_anti_debugging_and_obfuscation(file_path):  # PE 또는 ELF 파일에 안티디버깅 및 난독화 기법을 적용하는 함수
    
    if not os.path.exists(file_path):
    
        print(f"Error: {file_path} 파일을 찾을 수 없습니다.")
    
        return
    print(f"{file_path}에 안티디버깅 및 난독화 기법을 적용 중입니다...")
    
    anti_debugging_code = b"\xEB\xFE"  # 무한 루프 삽입
    
    with open(file_path, 'ab') as f:
    
        f.write(anti_debugging_code)
    
    with open(file_path, 'ab') as f:
    
        random_bytes = os.urandom(10)
    
        f.write(random_bytes)
    
    print("안티디버깅 및 난독화 기법이 성공적으로 적용되었습니다.")

def detect_anti_debugging_and_obfuscation(file_path):  # 파일에 안티디버깅 및 난독화 기법이 적용되었는지 확인하는 함수
    
    if not os.path.exists(file_path):
    
        print(f"Error: {file_path} 파일을 찾을 수 없습니다.")
    
        return
    
    print(f"{file_path}에 안티디버깅 및 난독화가 적용되었는지 확인 중입니다...")
    
    with open(file_path, 'rb') as f:
    
        content = f.read()
    
        if b"\xEB\xFE" in content:
    
            print(f"{file_path}에 안티디버깅 기법이 적용되었습니다.")
    
        else:
    
            print(f"{file_path}에 안티디버깅 기법이 적용되지 않았습니다.")
            
def remove_anti_debugging_and_obfuscation(file_path):   # 안티디버깅 기법과 난독화 기법을 해제하는 함수
    
    if not os.path.exists(file_path):
    
        print(f"Error: {file_path} 파일을 찾을 수 없습니다.")
    
        return

    print(f"{file_path}에서 안티디버깅 및 난독화 기법을 제거하는 중입니다...")

    # 파일에서 안티디버깅 코드 및 난독화된 바이트 패턴을 찾고 제거
    with open(file_path, 'rb') as f:
    
        content = f.read()

    # 안티디버깅 코드 제거
    content = content.replace(b"\xEB\xFE", b"")

    # 파일을 덮어쓰기 모드로 열고 변경된 내용을 기록
    with open(file_path, 'wb') as f:
    
        f.write(content)

    print("안티디버깅 및 난독화 기법이 성공적으로 제거되었습니다.")
    
def insert_canary(file_path):  # 파일에 카나리 값을 삽입하는 함수
    
    print(f"파일에 삽입된 카나리 값: {CANARY_VALUE.hex()}")
    
    try:
    
        with open(file_path, 'rb+') as f:
    
            f.seek(0, os.SEEK_END)  # 파일 끝으로 이동
            f.write(b'\x00' * 16)   # 빈 공간 확보 (예제: 16바이트)
            f.write(CANARY_VALUE)   # 카나리 값 삽입
    
            print(f"카나리 값이 {file_path}에 성공적으로 삽입되었습니다.")
    
    except FileNotFoundError:
    
        print(f"Error: {file_path} 파일을 찾을 수 없습니다.")

def check_canary_integrity(file_path):  # 파일의 카나리 값 무결성을 체크하는 함수
    
    try:
    
        with open(file_path, 'rb') as f:
    
            f.seek(-len(CANARY_VALUE), os.SEEK_END)  # 파일 끝에서 카나리 값 읽기
    
            stored_canary = f.read(len(CANARY_VALUE))
    
            print(f"파일에서 읽은 카나리 값: {stored_canary.decode()}")

            # 파일의 실제 카나리 값을 검사
            if stored_canary == CANARY_VALUE:
    
                print("카나리 무결성 검증 통과: 파일이 변조되지 않았습니다.")
    
            else:
    
                print("경고: 카나리 무결성 검증 실패! 파일이 변조되었을 수 있습니다.")
    
    except FileNotFoundError:
    
        print(f"Error: {file_path} 파일을 찾을 수 없습니다.")
    
    except Exception as e:
    
        print(f"Error during canary integrity check: {e}")
        
def remove_canary(file_path):  # 파일에서 카나리 값을 제거하는 함수
    
    try:
    
        with open(file_path, 'rb+') as f:
    
            f.seek(-len(CANARY_VALUE), os.SEEK_END)  # 파일 끝에서 카나리 값 읽기 위치로 이동
    
            stored_canary = f.read(len(CANARY_VALUE))

            if stored_canary == CANARY_VALUE:  # 카나리 값이 일치하는지 확인
    
                print(f"카나리 값이 {file_path}에서 감지되었습니다. 제거 중입니다...")
    
                f.seek(-len(CANARY_VALUE), os.SEEK_END)  # 카나리 위치로 다시 이동
                f.truncate(f.tell())  # 파일을 카나리 값 바로 앞에서 자르기
    
                print("카나리 값이 성공적으로 제거되었습니다.")
    
            else:
    
                print("카나리가 파일에 존재하지 않거나 손상되었습니다.")
    
    except FileNotFoundError:
    
        print(f"Error: {file_path} 파일을 찾을 수 없습니다.")
    
    except Exception as e:
    
        print(f"Error during canary removal: {e}")
        
def process_file_with_cp_option(file_path): # -cp 옵션 실행 함수
    
    # temp 폴더 생성
    temp_folder = 'temp'
    
    if not os.path.exists(temp_folder):
    
        os.makedirs(temp_folder)
    
    # 파일 복사
    copied_file_path = os.path.join(temp_folder, os.path.basename(file_path))
    
    shutil.copy2(file_path, copied_file_path)
    
    print(f"{file_path}가 {copied_file_path}로 복사되었습니다.")

    # 원본 파일에 카나리 삽입
    insert_canary(file_path)

    # 복사본 파일의 시그니처 및 확장자 변경
    with open(copied_file_path, 'rb+') as f:
    
        content = f.read()
    
        # 기존 시그니처를 exe 시그니처로 변경
        f.seek(0)
        f.write(FILE_SIGNATURES['exe'] + content[len(FILE_SIGNATURES['exe']):])
    
    new_copied_file_path = os.path.splitext(copied_file_path)[0] + '.exe'
    
    os.rename(copied_file_path, new_copied_file_path)
    
    print(f"복사 파일의 시그니처 및 확장자가 {new_copied_file_path}로 변경되었습니다.")
    
def signal_handler(sig, frame):
    
    global stop_sniffing
    
    stop_sniffing = True
    
    print("\n패킷 캡처 종료 중...")

def packet_callback(packet):    # 캡처된 각 패킷을 처리하는 콜백 함수.  악성 패킷 필터링 로직을 추가할 수 있습니다.
    
    # 패킷 필터링 예제 (악성 패킷 필터링 로직을 추가 가능)
    if packet.haslayer('TCP') and packet['TCP'].dport == 80:
        
        print(f"[INFO] 정상 패킷: {packet.summary()}")
    else:
        
        print(f"[ALERT] 악성 패킷 감지: {packet.summary()}")
        
def start_packet_capture():     # 네트워크 패킷을 캡처하고 처리하는 함수.
    
    print("네트워크 패킷 캡처 시작 (q 키를 눌러 종료)...")
    
    while not stop_sniffing:
    
        sniff(prn=packet_callback, store=0, count=10)
    
    print("패킷 캡처가 종료되었습니다.")

def monitor_network():  # 네트워크 모니터링 프로세스 시작.
    
    global stop_sniffing
    
    stop_sniffing = False
    
    signal.signal(signal.SIGINT, signal_handler)
    
    t = threading.Thread(target=start_packet_capture)
    
    t.start()
    
    while True:
    
        if stop_sniffing:
    
            break
    
        time.sleep(1)
    
    # 패킷을 .pcap 파일로 저장
    print(f"패킷을 {pcap_file} 파일로 저장 중...")
    
    wrpcap(pcap_file, [])  # 여기에 실제 캡처된 패킷을 기록합니다.


def main():
    
    print_ascii_art()
    
    show_loading_effect()
    
    parser = argparse.ArgumentParser(description="Anti Signature 프로그램: 파일 무결성 검사 도구 및 랜섬웨어 감염 여부 확인 도구")
    
    parser.add_argument(
    
        '-f', '--file', 
        type=str, 
        help='무결성을 검사할 파일 경로를 지정하고, 선택적으로 파일 해시 값을 제공할 수 있습니다. 예: -f example.pdf:d41d8cd98f00b204e9800998ecf8427e'
    
    )
    
    parser.add_argument(
    
        '-R', '--ransomware', 
        action='store_true', 
        help='파일의 랜섬웨어 감염 여부를 확인합니다.'
    
    )
    
    parser.add_argument(
        
        '-D', '--apply-debug', 
        action='store_true', 
        help='PE 또는 ELF 파일에 안티디버깅 및 난독화 기법을 적용합니다.'
    
    )
    
    parser.add_argument(
        
        '-dd', '--detect-debug', 
        action='store_true', 
        help='PE 또는 ELF 파일에 안티디버깅 및 난독화 기법이 적용되었는지 확인합니다.'
    
    )
    
    parser.add_argument(
        '-dx', '--remove-debug', 
        action='store_true', 
        help='PE 또는 ELF 파일에서 안티디버깅 및 난독화 기법을 제거합니다.'
    )
    
    parser.add_argument(
        '-net', '--network-monitor', 
        action='store_true', 
        help='네트워크 모니터링 및 악성 패킷 필터링을 수행합니다.'
    )
    
    parser.add_argument(
        '-c', '--canary', 
        action='store_true', 
        help='파일 내의 빈 공간에 카나리를 추가합니다.'
    )
    
    parser.add_argument(
        '-ccheck', '--canary-check', 
        action='store_true', 
        help='파일의 카나리 무결성을 체크합니다.'
    )
    
    parser.add_argument(
        '-cd', '--canary-delete',
        action='store_true',
        help='파일에서 카나리를 제거합니다.'
    )
    
    parser.add_argument(
        '-cp', '--copy-and-process',
        action='store_true',
        help='파일을 temp 폴더로 복사한 후 시그니처를 .exe로 변경합니다. (파일 백업)'
    )
    
    args = parser.parse_args()

    # 파일 경로와 해시 분리
    if args.file:
        
        file_info = args.file.split(':')
        
        file_path = file_info[0]
        
        expected_hash = file_info[1] if len(file_info) > 1 else None

        check_file_integrity(file_path, expected_hash)
        
        if args.ransomware:
        
            check_for_ransomware(file_path)
            
        if args.apply_debug:
            
            apply_anti_debugging_and_obfuscation(file_path)
        
        if args.detect_debug:
            
            detect_anti_debugging_and_obfuscation(file_path)
            
        if args.remove_debug:
            
            remove_anti_debugging_and_obfuscation(file_path)
            
        if args.canary:
            
            insert_canary(file_path)
        
        if args.canary_check:
            
            check_canary_integrity(file_path)
            
        if args.canary_delete:
            
            remove_canary(file_path)
            
        if args.network_monitor:
          
            monitor_network()
            
        if args.copy_and_process:
            
            process_file_with_cp_option(file_path)
    
    else:

        parser.print_help()

if __name__ == "__main__":

    main()
