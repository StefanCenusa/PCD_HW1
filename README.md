# PCD_HW1

This implementation offers a client/server pair working over UDP for sending files.

For streaming:
python server.py recv_file 9000 1
python client.py file 127.0.0.1 9000 9001 1


For stop and wait:
python server.py recv_file 9000 0
python client.py file 127.0.0.1 9000 9001 0
