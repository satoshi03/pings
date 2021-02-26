import select
import socket
import struct
import sys
import os
import time

from .response import Response
from .consts import SUCCESS, FAILED

__updated__ = "2021-02-25 11:09:56"

# source code URL: https://github.com/satoshi03/pings/blob/master/pings/ping.py

if (sys.version_info < (3, 3)) and sys.platform.startswith("win32"):
    timer = time.clock
else:
    timer = time.time


class Ping():

    def __init__(self, timeout=1000, packet_data_size=55, own_id=None, udp=False, bind=None, quiet=True):
        self.timeout = timeout
        self.packet_data_size = packet_data_size
        self.own_id = own_id
        self.udp = udp
        self.bind = bind
        self.quiet = quiet

        if own_id is None:
            self.own_id = os.getpid() & 0xFFFF

        self.max_wait = 1000 # ms
        self.seq_number = 0

        # self.icmp_echo_reply = 0
        self.icmp_echo = 8
        self.icmp_max_recv = 2048

    def _to_ip(self, addr):
        """
        If destination is not ip address, resolve it by using hostname
        """
        if self._is_valid_ip(addr):
            return addr
        return socket.gethostbyname(addr)

    def _is_valid_ip(self, addr):
        try:
            socket.inet_aton(addr)
        except socket.error:
            return False
        return True

    def _checksum(self, source_string):
        """
        A port of the functionality of in_cksum() from ping.c
        Ideally this would act on the string as a series of 16-bit ints (host
        packed), but this works.
        Network data is big-endian, hosts are typically little-endian
        """
        count_to = (int(len(source_string)/2))*2
        sum = 0
        count = 0

        # Handle bytes in pairs (decoding as short ints)
        lo_byte = 0
        hi_byte = 0
        while count < count_to:
            if (sys.byteorder == "little"):
                lo_byte = source_string[count]
                hi_byte = source_string[count + 1]
            else:
                lo_byte = source_string[count + 1]
                hi_byte = source_string[count]
            try:     # For Python3
                sum = sum + (hi_byte * 256 + lo_byte)
            except:  # For Python2
                sum = sum + (ord(hi_byte) * 256 + ord(lo_byte))
            count += 2

        # Handle last byte if applicable (odd-number of bytes)
        # Endianness should be irrelevant in this case
        if count_to < len(source_string): # Check for odd length
            lo_byte = source_string[len(source_string)-1]
            try:      # For Python3
                sum += lo_byte
            except:   # For Python2
                sum += ord(lo_byte)

        sum &= 0xffffffff # Truncate sum to 32 bits (a variance from ping.c, which
                          # uses signed ints, but overflow is unlikely in ping)

        sum = (sum >> 16) + (sum & 0xffff)    # Add high 16 bits to low 16 bits
        sum += (sum >> 16)                    # Add carry from above (if any)
        answer = ~sum & 0xffff                # Invert and truncate to 16 bits
        answer = socket.htons(answer)
        return answer

    def _parse_icmp_header(self, packet):
        """
        Parse icmp packet header to dict
        """
        p = struct.unpack("!BBHHH", packet[20:28])

        icmp_header = {}
        icmp_header["type"] = p[0]
        icmp_header["code"] = p[1]
        icmp_header["checksum"] = p[2]
        icmp_header["packet_id"] = p [3]
        icmp_header["sequence"] = p[4]
        return icmp_header

    def _parse_ip_header(self, packet):
        """
        Parse ip packet header to dict
        """
        p = struct.unpack("!BBHHHBBHII", packet[:20])

        ip_header = {}
        ip_header["version"] = p[0]
        ip_header["type"] = p[1]
        ip_header["length"] = p[2]
        ip_header["id"] = p[3]
        ip_header["flags"] = p[4]
        ip_header["ttl"] = p[5]
        ip_header["protocol"] = p[6]
        ip_header["checksum"] = p[7]
        ip_header["src_ip"] = p[8]
        return ip_header

    def _calc_delay(self, send_time, receive_time):
        """
        Calculate spending time between receveed time and sent time.
        If either sent time or received time is null value, returns -1
        """
        if not send_time or not receive_time:
            return -1
        return (receive_time - send_time)*1000

    def _echo_message(self, message):
        """
        If quiet option is not enable, print message.
        """
        if self.quiet:
            return
        print(message)

    def _wait_until_next(self, delay):
        if self.max_wait > delay:
            time.sleep((self.max_wait - delay)/1000)

    def ping(self, dest, times=1):
        """
        Ping to destination host (IP/Hostname)
        `dest` arg is indicate destination (both IP and hostname can be used) to ping.
        `times` args is indicate number of times that pings to destination

        Returns ping response that can be used for checking messages, some paramaeter
        and status such as success or failed.
        """
        response = Response()
        response.timeout = self.timeout
        response.dest = dest

        try:
            dest_ip = self._to_ip(dest)
        except socket.gaierror:
            msg = "ping: cannnot resolve {}: Unknown host".format(dest)
            response.messages.append(msg)
            self._echo_message(msg)
            return response

        if not dest_ip:
            response.ret_code = FAILED
            return response

        response.dest_ip = dest_ip

        # initialize sequence number
        self.seq_number = 0
        delays = []

        msg = "PING {} ({}): {} data bytes".format(dest, dest_ip, self.packet_data_size)
        response.messages.append(msg)
        self._echo_message(msg)

        for i in range(0, times):
            # create socket to send it
            try:
                my_socket = self.make_socket()
            except socket.error as e:
                etype, evalue, etb = sys.exc_info()
                if e.errno == 1:
                    # Operation not permitted - Add more information to traceback
                    msg = "{} - Note that ICMP messages can only be send from processes running as root.".format(evalue)
                else:
                    msg = str(evalue)
                self._echo_message(msg)
                response.messages.append(msg)
                response.ret_code = FAILED
                return response

            try:
                send_time = self.send(my_socket, dest_ip)
            except socket.error as e:
                msg = "General failure ({})".format(e.args[1])
                self._echo_message(msg)
                response.messages.append(msg)
                my_socket.close()
                return response

            if not send_time:
                response.ret_code = Ping.FAILED
                return response

            receive_time, packet_data_size, ip, ip_header, icmp_header = self.receive(my_socket)
            my_socket.close()
            delay = self._calc_delay(send_time, receive_time)

            # if receive_time value is 0, it means packet could not received
            if receive_time == 0:
                msg = "Request timeout for icmp_seq {}".format(self.seq_number)
                response.messages.append(msg)
                self._echo_message(msg)
                response.ret_code = FAILED
            else:
                msg = "{} bytes from {}: icmp_seq={} ttl={} time={:.3f} ms".format(
                    packet_data_size,
                    ip,
                    self.seq_number,
                    ip_header['ttl'],
                    delay
                )
                response.messages.append(msg)
                self._echo_message(msg)
                response.ret_code = SUCCESS
                response.ttl = ip_header['ttl']
                delays.append(delay)

            response.packet_data_size = packet_data_size
            self.seq_number += 1

            self._wait_until_next(delay)

        response.max_rtt = max(delays) if delays else 0.0
        response.min_rtt = min(delays) if delays else 0.0
        response.avg_rtt = sum(delays)/len(delays) if delays else 0.0

        msg = "--- {} ping statistics ---".format(dest)
        response.messages.append(msg)
        self._echo_message(msg)

        response.packet_transmitted = self.seq_number
        response.packet_received = len(delays)
        response.packet_loss = self.seq_number - response.packet_received
        response.packet_loss_percent = response.packet_loss / response.packet_transmitted *100

        msg = "{} packets transmitted, {} packets received, {:.1f}% packet loss".format(
            response.packet_transmitted,
            response.packet_received,
            response.packet_loss_percent
        )
        response.messages.append(msg)
        self._echo_message(msg)

        msg = "round-trip min/avg/max = {:.3f}/{:.3f}/{:.3f} ms".format(
            response.min_rtt, response.avg_rtt, response.max_rtt
        )
        response.messages.append(msg)
        self._echo_message(msg)

        return response

    def make_socket(self):
        """
        Make socket
        """
        if self.udp:
            my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_ICMP)
        else:
            my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        if self.bind:
            my_socket.bind((self.bind, 0))
        return my_socket

    def make_packet(self):
        # Header is type (8), code (8), checksum (16), id (16), sequence (16)
        # Header size in total is (8+8+16+16+16)/8 = 8 bytes
        checksum = 0

        # Make a dummy header with a 0 checksum.
        header = struct.pack(
            "!BBHHH", self.icmp_echo, 0, checksum, self.own_id, self.seq_number
        )

        pad_bytes = []
        # start_val = 0x41 # the order of character 'A' in ASCII is 65, and 66 in hex is 0x41
        for i in range(0, (self.packet_data_size)):
            pad_bytes += [ 0xa0 + (i & 0xf)]  # Keep chars in the 'a'-'o' range
        data = bytearray(pad_bytes)

        checksum = self._checksum(header + data)

        header = struct.pack(
            "!BBHHH", self.icmp_echo, 0, checksum, self.own_id, self.seq_number
        )
        return header + data

    def send(self, my_socket, dest):
        """
        Creates packet and send it to a destination
        Returns `send_time` that is packet send time represented in unix time.
        """
        packet = self.make_packet()
        send_time = timer()
        my_socket.sendto(packet, (dest, 1))
        return send_time


    def receive(self, my_socket):
        """
        receive icmp packet from a host where packet was sent.
        Returns receive time that is time of packet received, packet size, ip address,
        ip header and icmp header both are formatted in dict.
        If falied to receive packet, returns 0 and None

        According to RFC 791 - Internet Protocol Version 4
        The struct of IPv4 packet:
        Internet Header Length (4bits),
        Type of Service (8bits),
        Total Length (16bits),
        Identification (16bits),
        Flags (3bits),
        Fragment Offset (13bits),
        Time To Live (8bits), 
        Protocol (8bits),
        Header checksum (16bits),
        Source Address (32bits),
        Destination Address (32bits),
        Options (Variable) Padding (0-24bits)
        So.The IPv4 packet header length is (4+8+16+16+3+13+8+8+16+32+32)/8 = 20 bytes
        According to RFC 792 - Internet Control Message Protocol 
        The struct of ICMP packet:
        Type (8bits), Code (8bits), Checksum (16bits), ...anything else... (32bits),
                        Internet Header + 64 bits of Original Data Datagram
        So.The ICMP packet header length is (8+8+16+32)/8 = 8 bytes
        Generally,a ICMP over IPv4 packet's data length = len(packet) - (20+8)
        """
        timeout = self.timeout / 1000
        while True:
            select_start = timer()
            inputready, outputready, exceptready = select.select([my_socket], [], [], timeout)
            select_duration = (timer() - select_start)
            if inputready == []:
                return 0, 0, 0, None, None

            packet, address = my_socket.recvfrom(self.icmp_max_recv)
            icmp_header = self._parse_icmp_header(packet)

            receive_time = timer()

            if icmp_header["packet_id"] == self.own_id: # my packet
                ip_header = self._parse_ip_header(packet)
                ip = socket.inet_ntoa(struct.pack("!I", ip_header["src_ip"]))
                packet_data_size = len(packet) - 28
                return receive_time, packet_data_size, ip, ip_header, icmp_header

            timeout = timeout - select_duration

            if timeout <= 0:
                return 0, 0, 0, None, None
