import http.client as htc

class Connection(object):
    def __init__(self, cid: str, http_con: htc.HTTPConnection):
        self.cid = cid
        self.http_con = http_con
