import json, threading, websocket


class DXLink:
    socket: websocket.WebSocketApp = None
    uri: str = None
    auth_token: str = None
    auth_state: str = None
    user_id: str = None

    def __init__(self, uri: str = None, auth_token: str = None) -> None:
        self.uri = uri
        self.auth_token = auth_token
        self.connect()

    def connect(self) -> bool:
        print("dxlink connect")
        self.socket = websocket.WebSocketApp(
            url=self.uri,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        self.thread = threading.Thread(target=self.socket.run_forever)
        self.thread.start()

    def disconnect(self):
        self.active = False
        self.socket.close()

    def on_message(self, ws, message):
        message = json.loads(message)
        print(f"got {message}")
        match message["type"]:
            case "SETUP":
                self.send({"type": "AUTH", "token": self.auth_token})
            case "AUTH_STATE":
                if message["state"] == "AUTHORIZED":
                    self.auth_state = message["state"]
                    self.user_id = message["userId"]
                    self.send(
                        {
                            "type": "CHANNEL_REQUEST",
                            "channel": 1,
                            "service": "FEED",
                            "parameters": {"contract": "AUTO"},
                        }
                    )
            case "KEEPALIVE":
                self.send({"type": "KEEPALIVE"})
            case _:
                print(f"dxlink get {message}")

    def on_error(self, ws, error):
        print(f"dxlink error {error}")
        self.active = False

    def on_close(self, ws, status_code, message):
        print(f"dxlink close {status_code} {message}")
        self.active = False

    def on_open(self, ws):
        print(f"dxlink open")
        self.active = True

        self.send(
            {
                "type": "SETUP",
                "keepaliveTimeout": 60,
                "acceptKeepaliveTimeout": 60,
                "version": "0.1",
            }
        )

    def send(self, data: dict = {}):
        print(f"sending {data}")
        if (
            self.auth_state != "AUTHORIZED"
            and data["type"] != "SETUP"
            and data["type"] != "AUTH"
        ):
            print(
                f"dxlink Tried to send message of type {data['type']} but auth_state is {self.auth_state}!"
            )
            return
        if not "channel" in data:
            data["channel"] = 0
        if not "userId" in data and self.user_id is not None:
            data["userId"] = self.user_id
        self.socket.send(json.dumps(data))
