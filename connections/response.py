import http.client as htc

class ManagedResponseCtx(object):
    def __init__(self, response: htc.HTTPResponse):
        self.response = response

    def __enter__(self) -> htc.HTTPResponse:
        return self.response

    def __exit__(self, exc_type, exc_value, exc_tb):
        if not self.response.isclosed():
            self.response.read()
            self.response.close()