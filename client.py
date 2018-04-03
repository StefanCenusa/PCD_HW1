import datetime
import signal
import socket
import sys
import time
import utils


def shutdown():
    if log_file:
        log_file.write("TRANSMISSION INCOMPLETE\n")
        log_file.write("Segments sent:\t\t" + str(sent) + "\n")
        log_file.write("Segments retransmitted:\t" + str(retransmitted) + "\n")
        log_file.close()

    if send_file:
        send_file.close()

    if ack_sock:
        ack_sock.close()

    if send_sock:
        send_sock.close()

    exit(1)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, shutdown)

    try:
        filename = sys.argv[1]
        remote_ip = socket.gethostbyname(sys.argv[2])
        remote_port = int(sys.argv[3])
        local_port = int(sys.argv[4])

    except IndexError, TypeError:
        exit('usage: ./client.py <filename> <remote_IP> <remote_port> <local_port_num>')

    try:
        send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        send_sock.bind(("", local_port))

        ack_sock = socket.socket()
        ack_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ack_sock.bind(("", local_port))
        ack_sock.listen(1)
    except socket.error:
        exit('Error creating socket.')

    seqnum = 0
    acknum = 0
    final = False
    sent = 0
    retransmitted = 0

    try:
        send_file = open(filename)
    except:
        exit("Unable to open " + filename)

    log_file = sys.stdout

    tcp_established = False
    text = send_file.read(utils.CONTENT_SIZE)

    while not tcp_established:
        try:
            packet = utils.make_packet(local_port, remote_port, seqnum, acknum, False, False, text)

            send_sock.sendto(packet, (remote_ip, remote_port))
            sent += 1
            send_time = time.time()

            signal.signal(signal.SIGALRM, utils.timeout)
            signal.alarm(utils.TIMEOUT)

            recv_sock, addr = ack_sock.accept()

            signal.alarm(0)
            tcp_established = True
            recv_sock.settimeout(utils.TIMEOUT)
        except socket.timeout:
            retransmitted += 1
            continue

    while True:
        try:
            ack = recv_sock.recv(utils.HEADER_SIZE)
            recv_time = time.time()

            ack_source_port, ack_dest_port, ack_seqnum, \
            ack_acknum, ack_valid, ack_final, ack_contents = utils.unpack(ack)

            log = str(datetime.datetime.now()) + " " + \
                  str(ack_source_port) + " " + \
                  str(ack_dest_port) + " " + \
                  str(ack_seqnum) + " " + \
                  str(ack_acknum) + "\n"

            if ack_valid:
                log = log.strip("\n") + " ACK\n"
            if ack_final:
                log = log.strip("\n") + " FIN\n"

            if ack_acknum == acknum and ack_valid:

                rtt = recv_time - send_time

                log = log.strip() + " " + str(rtt) + "\n"

                log_file.write(log)

                if ack_final:
                    break

                text = send_file.read(utils.CONTENT_SIZE)

                if text == "":
                    final = True

                seqnum += 1
                acknum += 1

                packet = utils.make_packet(local_port, remote_port, seqnum, acknum, False, final, text)

                send_sock.sendto(packet, (remote_ip, remote_port))
                sent += 1
                send_time = time.time()

            else:
                log_file.write(log)
                raise socket.timeout

        except socket.timeout:
            packet = utils.make_packet(local_port, remote_port, seqnum, acknum, False, final, text)
            send_sock.sendto(packet, (remote_ip, remote_port))
            send_time = time.time()
            sent += 1
            retransmitted += 1

    print("\nTRANSMISSION SUCCESSFUL")
    print("Segments sent:\t\t" + str(sent))
    print("Segments retransmitted:\t" + str(retransmitted))
