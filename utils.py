import socket
import struct

HEADER_FORMAT = "!HHIIH"
TIMEOUT = 1
CONTENT_SIZE = 1000
HEADER_SIZE = 14
PACKET_SIZE = CONTENT_SIZE + HEADER_SIZE


def make_packet(source_port, dest_port, seqnum, acknum, ack, final, contents):
    flags = 1 if final else 0

    if ack:
        flags += 16

    header = struct.pack(HEADER_FORMAT, source_port,
                         dest_port, seqnum, acknum,
                         flags)

    return header + contents


def unpack(segment):
    header = segment[:HEADER_SIZE]
    packet_source_port, packet_dest_port, packet_seqnum, \
    packet_acknum, packet_flags = struct.unpack(HEADER_FORMAT, header)

    packet_ack = (packet_flags >> 4) == 1
    packet_final = int(packet_flags % 2 == 1)
    packet_contents = segment[HEADER_SIZE:]

    return packet_source_port, packet_dest_port, \
           packet_seqnum, packet_acknum, \
           packet_ack, packet_final, \
           packet_contents


def timeout(signum, frame):
    raise socket.timeout
