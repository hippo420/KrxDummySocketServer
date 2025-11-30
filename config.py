import codecs
import ast
import time
import codecs
from typing import Dict


# --- DB 설정 (PostgreSQL) ---
# 사용자가 실제 환경에 맞게 수정해야 합니다.
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "stockdb"
DB_USER = "stockuser"
DB_PASSWORD = "password"


def _load_from_db() -> Dict[str, str]:
    """PostgreSQL 데이터베이스에서 주식 목록을 불러옵니다."""
    import psycopg2  # 이 함수 안에서만 import 하여 psycopg2가 없는 경우를 대비합니다.
    conn = None
    max_retries = 3
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            cur = conn.cursor()
            # 실제 테이블과 컬럼명에 맞게 SQL 쿼리를 수정해야 합니다.
            cur.execute("SELECT isu_srt_cd, isu_nm FROM info_stock")
            rows = cur.fetchall()
            cur.close()
            print("Successfully loaded stock data from PostgreSQL.")
            return {row[0]: row[1] for row in rows}
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            print(f"DB connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)  # 1초 대기 후 재시도
            else:
                print("Could not connect to the database after multiple retries.")
                raise  # 마지막 시도 실패 시 예외를 다시 발생시켜 fallback 로직으로 넘어갑니다.
        finally:
            if conn:
                conn.close()


def _load_from_dat_file() -> Dict[str, str]:
    """stocklist.dat 파일에서 주식 목록을 불러옵니다.
    
    파일 내용은 ["코드", "이름"], ["코드", "이름"] 형태의 리스트 문자열로 가정합니다.
    """
    print("Attempting to load stock data from stocklist.dat as a fallback.")
    stock_data = {}
    
    # ⚠️ codecs 모듈에 ast나 다른 표준 모듈이 포함되어 있지 않으므로 
    #    코드가 실행될 환경에 'ast' 모듈이 import 되어 있어야 합니다.
    #    (위 코드 블록에는 ast와 List, Dict를 import 했습니다.)
    
    try:
        # UTF-8 인코딩으로 파일을 읽습니다.
        with codecs.open('stocklist.dat', 'r', encoding='utf-8') as f:
            # 파일 전체 내용을 하나의 문자열로 읽습니다.
            data_string = f.read()
            
            # 1. 문자열 전처리: 줄바꿈 제거 및 전체를 유효한 리스트 형식으로 감싸기
            #    데이터가 ["코드", "이름"], ["코드", "이름"],... 형태로 되어 있다고 가정
            clean_string = data_string.strip()
            # 줄바꿈을 쉼표로 대체하여 하나의 긴 리스트처럼 만듭니다.
            clean_string = clean_string.replace(']\n', '],').replace('\n', '')
            
            # 전체 문자열을 [ ]로 감싸서 유효한 파이썬 리스트 형태로 만듭니다.
            if not clean_string.startswith('['):
                clean_string = '[' + clean_string
            if not clean_string.endswith(']'):
                clean_string = clean_string + ']'
                
            # 2. ast.literal_eval을 사용하여 문자열을 파이썬 객체로 변환
            #    (안전하게 문자열을 리스트 구조로 파싱)
            stock_list: List[List[str]] = ast.literal_eval(clean_string)
            
            # 3. 리스트를 딕셔너리 형태로 변환
            stock_data = {code.strip(): name.strip() for code, name in stock_list}
            
        print("Successfully loaded stock data from stocklist.dat.")
        
    except FileNotFoundError:
        print("Warning: stocklist.dat not found. Using an empty stock list.")
    except (ValueError, SyntaxError) as e:
        # ast.literal_eval 또는 데이터 변환 과정에서 오류 발생 시 처리
        print(f"Error reading stocklist.dat: Data format error (Expected Python list format). {e}. Using an empty stock list.")
        stock_data = {} # 오류 발생 시 빈 딕셔너리 반환
    except Exception as e:
        print(f"Error reading stocklist.dat: {e}. Using an empty stock list.")
        stock_data = {}
        
    return stock_data


def _initialize_stock_data() -> Dict[str, str]:
    """
    주식 데이터를 초기화합니다.
    1. PostgreSQL에서 로드를 시도합니다. (최대 3회 재시도)
    2. DB 연결 실패 시 stocklist.dat 파일에서 로드를 시도합니다.
    """
    try:
        # psycopg2가 설치되어 있는지 확인하고 DB 로드를 시도합니다.
        import importlib
        importlib.import_module('psycopg2')
        return _load_from_db()
    except ImportError:
        print("psycopg2 is not installed. Falling back to stocklist.dat.")
        return _load_from_dat_file()
    except Exception:
        # _load_from_db에서 재시도 후에도 실패한 경우
        return _load_from_dat_file()


# --- 서버 설정 ---
HOST = '127.0.0.1'
UDP_PORT = 9999
TCP_PORT = 10000        # TCP 포트 추가
WEBSOCKET_PORT = 10001  # WebSocket 포트 추가 (미사용)

REAL_TR_TYPE = "10" # 현재가 TR 명 (가정)
REAL_SEND_INTERVAL = 0.5 # 실시간 데이터 전송 간격 (초 단위)

# --- 주식 데이터 초기화 ---
STOCK_DATA: Dict[str, str] = _initialize_stock_data()


def get_config() -> Dict:
    """서버 설정 값을 딕셔너리 형태로 반환합니다."""
    return {
        'server': {
            'ip': HOST,
            'port': UDP_PORT
        },
        'tcp': {
            'port': TCP_PORT
        },
        'websocket': {
            'port': WEBSOCKET_PORT
        },
        'realtime': {
            'tr_type': REAL_TR_TYPE,
            'interval': REAL_SEND_INTERVAL
        }
    }


# --- 유효한 API 키 목록 ---
VALID_API_KEYS = {
    "testkey123",
}

# 데이터 로딩 결과 확인
if not STOCK_DATA:
    print("Warning: Stock data is empty. The server might not function as expected.")
else:
    print(f"Loaded {len(STOCK_DATA)} stock items.")
