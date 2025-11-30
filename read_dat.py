import codecs
import ast
from typing import Dict, List

def read_stock_list(file_path: str) -> Dict[str, str]:
    """
    지정된 .dat 파일에서 주식 목록을 읽어 딕셔너리로 반환합니다.
    파일 내용은 [["코드1", "이름1"], ["코드2", "이름2"]] 형태의 리스트 문자열로 가정합니다.
    """
    print(f"Attempting to load stock data from {file_path}.")
    stock_data = {}
    
    try:
        # UTF-8 인코딩으로 파일을 읽습니다.
        with codecs.open(file_path, 'r', encoding='utf-8') as f:
            data_string = f.read()
            
            # ast.literal_eval을 사용하여 문자열을 파이썬 객체로 안전하게 변환합니다.
            # 이 방식은 eval()보다 훨씬 안전합니다.
            stock_list: List[List[str]] = ast.literal_eval(data_string)
            
            # 리스트를 딕셔너리 형태로 변환합니다 (예: {"005930": "삼성전자"})
            stock_data = {code.strip(): name.strip() for code, name in stock_list}
            
        print(f"Successfully loaded {len(stock_data)} stock items from {file_path}.")
        
    except FileNotFoundError:
        print(f"Warning: {file_path} not found. Using an empty stock list.")
    except (ValueError, SyntaxError) as e:
        print(f"Error reading {file_path}: Data format error. Check if the file content is a valid Python list of lists. Error: {e}. Using an empty stock list.")
        stock_data = {}
    except Exception as e:
        print(f"An unexpected error occurred while reading {file_path}: {e}. Using an empty stock list.")
        stock_data = {}
        
    return stock_data