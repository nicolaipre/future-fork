from typing import Callable


class Response:
    def __init__(self, body: bytes = b"", status: int = 200, headers=None):
        self.body = body
        self.status = status
        #self.headers = headers or [[b"content-type", b"text/plain"]]
        self.headers = [[key.encode(), value.encode()] for key, value in headers.items()] if headers else [[b"content-type", b"text/plain"]]  # FIXME: Should this be the default..?
        self.context = {}  # for custom data we inject into the response

    async def __call__(self, send: Callable) -> None:
        assert type(self.body) == bytes, "Response body must be bytes"
        
        start_message = {
            "type": "http.response.start",
            "status": self.status,
            "headers": self.headers,
        }
        await send(start_message)
        body_message = {
            "type": "http.response.body",
            "body": self.body,
        }
        await send(body_message)


class PlainTextResponse(Response):
    pass


class JSONResponse(Response):
    pass


class EmptyResponse(Response):
    pass