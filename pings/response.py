from .consts import SUCCESS


class Response():
    """
    Reponse of ping
    """
    def __init__(self):

        self.max_rtt = None
        self.min_rtt = None
        self.avg_rtt = None
        self.packet_lost = None
        self.ret_code = None
        self.messages = []

        self.packet_size = None
        self.timeout = None
        self.dest = None
        self.dest_ip = None

    def __str__(self):
        return str(self.to_dict())

    def to_dict(self):
        return {
            "max_rtt": self.max_rtt,
            "min_rtt": self.min_rtt,
            "avg_rtt": self.avg_rtt,
            "packet_lost": self.packet_lost,
            "ret_code": self.ret_code,
            "packet_size": self.packet_size,
            "timeout": self.timeout,
            "dest": self.dest,
            "dest_ip": self.dest_ip,
        }

    def is_reached(self):
        return self.ret_code == SUCCESS

    def print_messages(self):
        for msg in self.messages:
            print(msg)
