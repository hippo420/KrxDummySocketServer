import asyncio
import logging
from config import get_config
from stock_protocol import StockProtocol, send_real_time_data
from read_dat import read_stock_list
from stock_model import StockModel

async def main():
    """
    메인 함수
    """
    # 로깅 설정
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # 설정 로드
    config = get_config()
    ip = config['server']['ip']
    port = int(config['server']['port'])

    # 주식 목록 로드 및 StockModel 생성
    stock_list = read_stock_list('stocklist.dat')
    if not stock_list:
        logging.error("Failed to load stock list. Shutting down.")
        return
    
    stock_model = StockModel(stock_list)

    # 이벤트 루프 가져오기
    loop = asyncio.get_running_loop()

    # UDP 서버 시작
    logging.info(f"Starting UDP server on {ip}:{port}")
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: StockProtocol(stock_model),
        local_addr=(ip, port)
    )

    # 실시간 데이터 전송 태스크 시작
    sender_task = loop.create_task(send_real_time_data(stock_model, transport))

    try:
        # 서버를 계속 실행하기 위해 무한정 대기
        await asyncio.Event().wait()
    finally:
        logging.info("Closing UDP server")
        sender_task.cancel()
        transport.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.127.0.0.1("Server stopped by user")
