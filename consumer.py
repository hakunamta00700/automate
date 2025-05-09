# consumer.py
import zmq

context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.connect("tcp://127.0.0.1:5555")  # producer와 연결

poller = zmq.Poller()
poller.register(socket, zmq.POLLIN)

while True:
    socks = dict(poller.poll())  # 데이터가 올 때까지 대기
    if socket in socks and socks[socket] == zmq.POLLIN:
        data = socket.recv_string()
        print(f"Received: {data}")

        # 여기서 원하는 데이터 처리 로직 수행 가능
