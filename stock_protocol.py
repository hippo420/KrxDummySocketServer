import asyncio
import json
import logging
from stock_model import StockModel

# 클라이언트별 구독 정보를 관리하는 딕셔너리
# { "api_key": {"trnms": ["H0STASP0", "H0STCNT0"], "addr": ("127.0.0.1", 12345)} }
client_subscriptions = {}

class StockProtocol(asyncio.DatagramProtocol):
    def __init__(self, stock_model: StockModel):
        self.stock_model = stock_model
        self.transport = None
        super().__init__()

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        loop = asyncio.get_event_loop()
        try:
            request = json.loads(data.decode())
            api_key = request.get("api_key")
            trnm = request.get("trnm")
            refresh = request.get("refresh", "1")  # 기본값을 "1"로 설정

            if not api_key:
                logging.warning(f"API key is missing from request: {addr}")
                return

            # refresh="1" 이면 구독 정보 초기화 및 trnm 등록
            if refresh == "1":
                client_subscriptions[api_key] = {"trnms": [trnm] if trnm else [], "addr": addr}
                logging.info(f"Subscribed: {api_key}, trnm: {trnm}, addr: {addr}")

            # refresh="0" 이면 구독 정보 삭제
            elif refresh == "0":
                if api_key in client_subscriptions:
                    del client_subscriptions[api_key]
                    logging.info(f"Unsubscribed: {api_key}")
                    # 구독 해지 시 응답을 보낼 필요가 있다면 여기에 추가
                    response_data = {"result": "success", "message": "Unsubscribed successfully."}
                    self.transport.sendto(json.dumps(response_data, ensure_ascii=False).encode('utf-8'), addr)
                return # 구독 해지 후에는 데이터 전송 없이 종료

            # refresh 값이 다른 경우, 기존 구독에 trnm 추가
            else:
                if api_key in client_subscriptions:
                    if trnm and trnm not in client_subscriptions[api_key]["trnms"]:
                        client_subscriptions[api_key]["trnms"].append(trnm)
                        logging.info(f"Added trnm: {trnm} for api_key: {api_key}")
                else:
                    # refresh=1 없이 요청이 오면 새로 구독
                    client_subscriptions[api_key] = {"trnms": [trnm] if trnm else [], "addr": addr}
                    logging.info(f"Implicitly Subscribed: {api_key}, trnm: {trnm}, addr: {addr}")


            # 현재 구독 정보에 따라 응답 생성
            if api_key in client_subscriptions:
                subscribed_trnms = client_subscriptions[api_key].get("trnms", [])
                if subscribed_trnms:
                    response_data = self.stock_model.get_data(subscribed_trnms)
                    self.transport.sendto(json.dumps(response_data, ensure_ascii=False).encode('utf-8'), addr)
                else:
                    logging.warning(f"No trnms subscribed for api_key: {api_key}")
            else:
                logging.warning(f"Request received from unsubscribed api_key: {api_key}")


        except json.JSONDecodeError:
            logging.error(f"Failed to decode JSON from {addr}: {data.decode()}")
        except Exception as e:
            logging.exception(f"Error processing datagram from {addr}: {e}")

    def error_received(self, exc):
        logging.error('Error received:', exc)

    def connection_lost(self, exc):
        logging.info("Connection closed")

async def send_real_time_data(stock_model: StockModel, transport: asyncio.DatagramTransport):
    """주기적으로 구독 클라이언트에게 실시간 데이터를 전송합니다."""
    while True:
        await asyncio.sleep(1) # 1초마다 데이터 전송
        if not client_subscriptions:
            continue

        for api_key, sub_info in list(client_subscriptions.items()):
            try:
                addr = sub_info.get("addr")
                trnms = sub_info.get("trnms")
                if addr and trnms:
                    real_time_data = stock_model.get_data(trnms)
                    transport.sendto(json.dumps(real_time_data, ensure_ascii=False).encode('utf-8'), addr)
            except Exception as e:
                logging.error(f"Error sending real-time data to {api_key}: {e}")
