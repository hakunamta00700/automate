# producer.py
import time
import zmq

context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.bind("tcp://127.0.0.1:5555")  # 포트 열기

i = 0
while True:
    # data = f"data-{i}"
    data =  input("Enter data: ")
    print(f"Sending: {data}")
    socket.send_string(data)
    i += 1
    time.sleep(1)  # 1초마다 전송
