from .consts import SUCCESS


class Response():
    """
    Reponse of ping
    """
    def __init__(self):
        self.packet_transmitted = None
        self.packet_received = None
        self.packet_loss = None
        self.packet_loss_percent = None

        self.max_rtt = None
        self.min_rtt = None
        self.avg_rtt = None
        self.ret_code = None
        self.messages = []

        self.packet_data_size = None
        self.ttl = None
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
            "packet_transmitted": self.packet_transmitted,
            "packet_received": self.packet_received,
            "packet_loss": self.packet_loss,
            "packet_loss_percent": self.packet_loss_percent,
            "ret_code": self.ret_code,
            "packet_data_size": self.packet_data_size,
            "ttl": self.ttl,
            "timeout": self.timeout,
            "dest": self.dest,
            "dest_ip": self.dest_ip,
        }

    def is_reached(self):
        return self.ret_code == SUCCESS

    def print_messages(self):
        for msg in self.messages:
            print(msg)
