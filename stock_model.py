import random
import time
import logging
from typing import Dict, List, Any, Tuple

class StockState:
    """각 종목의 현재 가격과 전일 대비 상태를 관리하는 클래스"""
    def __init__(self, initial_price: float):
        self.price = initial_price
        self.prev_price = initial_price

    def update_price(self) -> Tuple[int, str, int, int]:
        """
        가격 변동을 생성하고 부호, 체결량 등을 반환합니다.
        반환: (현재가, 부호, 체결량, 단위체결량)
        """
        change_rate = random.uniform(-0.01, 0.01)
        new_price = self.price * (1 + change_rate)

        # 호가 단위에 맞게 반올림 로직
        if new_price < 1000:
            new_price = round(new_price, 0)
        elif new_price < 10000:
            new_price = round(new_price / 5) * 5
        else:
            new_price = round(new_price / 10) * 10
            
        if new_price < 100:
            new_price = 100.0

        new_price = int(new_price)
        
        # 전일 대비 부호 결정
        diff = new_price - self.prev_price
        sign = "+" if diff > 0 else ("-" if diff < 0 else "")
        
        self.prev_price = self.price
        self.price = new_price
        
        trade_amount = random.randint(10, 500)
        unit_trade_amount = random.randint(1, 50)
        
        return new_price, sign, trade_amount, unit_trade_amount

class StockModel:
    def __init__(self, stock_list: Dict[str, str]):
        self.stock_info: Dict[str, str] = stock_list
        self.stock_states: Dict[str, StockState] = {}
        for code in self.stock_info.keys():
            initial_price = random.randint(500, 1500) * 100
            self.stock_states[code] = StockState(initial_price)
    
    def _generate_single_stock_update(self, stock_code: str) -> Dict[str, Any]:
        """단일 종목의 실시간 데이터 아이템을 생성합니다."""
        if stock_code not in self.stock_states:
            return None # 해당 종목 코드가 없으면 None 반환

        state = self.stock_states[stock_code]
        price, sign, trade_amount, unit_trade_amount = state.update_price()
        stock_name = self.stock_info.get(stock_code, "알 수 없는 종목")
        
        ask_price = price + random.randint(10, 50)
        bid_price = price - random.randint(10, 50)
        
        # This is an "item" in the data list
        return {
            "type": "10", # 실시간 현재가 TR 유형
            "name": "현재가",
            "item": stock_code,
            "values": [
                {"9001": stock_code},
                {"302": stock_name},
                {"10": sign + str(price)},
                {"27": ask_price},
                {"28": bid_price},
                {"908": time.strftime("%H%M%S")},
                {"910": price},
                {"911": trade_amount},
                {"914": price},
                {"915": unit_trade_amount}
            ]
        }

    def get_data(self, trnms: List[str]) -> Dict[str, Any]:
        """요청된 trnm(종목코드) 리스트에 대한 전체 응답을 생성합니다."""
        logging.info(f"Received request for trnms: {trnms}")
        data_items = []
        for code in trnms:
            if code in self.stock_states:
                update_data = self._generate_single_stock_update(code)
                if update_data:
                    data_items.append(update_data)
            else:
                logging.warning(f"Requested trnm '{code}' not found in stock model.")

        if not data_items:
            logging.warning(f"No valid data generated for requested trnms: {trnms}")

        # The protocol expects a single response object
        response = {
            "trnm": "REAL", # This seems to be a container trnm
            "data": data_items
        }
        return response
