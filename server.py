import signal
import socket
import sys
import utils
import datetime


def shutdown():
    sys.stdout.write("\nTRANSMISSION INCOMPLETE\n")
    sys.stdout.close()

    if recv_file:
        recv_file.close()

    if recv_sock:
        recv_sock.close()

    if ack_sock:
        ack_sock.close()

    exit(1)


def log_packet(source_port, dest_port, seqnum, acknum, final):
    log = str(datetime.datetime.now()) + " " + \
          str(source_port) + " " + \
          str(dest_port) + " " + \
          str(seqnum) + " " + \
          str(acknum)

    if final:
        log += " FIN"

    sys.stdout.write(log + "\n")


def send_ack_packet(ack_sock, sender_port, seqnum, acknum, packet_valid, final):
    ack_packet = utils.make_packet(ack_sock.getsockname()[1], sender_port, seqnum, acknum, packet_valid, final, "")
    ack_sock.send(ack_packet)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, shutdown)

    try:
        filename = sys.argv[1]
        listen_port = int(sys.argv[2])
        ack_packets = int(sys.argv[3])

    except IndexError, TypeError:
        exit("usage: ./server.py <filename> <listening_port> <ack_packets>")

    try:
        recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        recv_sock.bind(("", listen_port))

        ack_sock = socket.socket()
        ack_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except socket.error:
        exit("Error creating socket.")

    try:
        recv_file = open(filename, 'w')
    except IOError:
        exit("Unable to open " + filename + ".")

    if ack_packets:
        next_acknum = 0

        packet, addr = recv_sock.recvfrom(utils.PACKET_SIZE)

        source_port, dest_port, seqnum, acknum, ack, final, contents = utils.unpack(packet)


        sender_ip = addr[0]
        sender_port = addr[1]
        ack_sock.connect((sender_ip, sender_port))

        packet_valid = next_acknum == acknum

        if packet_valid:
            recv_file.write(contents)
            next_acknum += 1

        send_ack_packet(ack_sock, sender_port, seqnum, acknum, packet_valid, False)

        log_packet(source_port, dest_port, seqnum, acknum, False)

    while True:

        packet, addr = recv_sock.recvfrom(utils.PACKET_SIZE)
        source_port, dest_port, seqnum, acknum, ack, final, contents = utils.unpack(packet)

        if ack_packets:
            packet_valid = next_acknum == acknum

            if packet_valid:
                recv_file.write(contents)
                next_acknum += 1

            send_ack_packet(ack_sock, sender_port, seqnum, acknum, packet_valid, final)
        else:
            recv_file.write(contents)

        log_packet(source_port, dest_port, seqnum, acknum, final)

        if final:
            break

    print("File successfully received.")
