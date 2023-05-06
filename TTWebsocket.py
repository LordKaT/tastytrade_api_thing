import json, threading, time, websocket

CERT_WSS = "wss://streamer.cert.tastyworks.com"
PROD_WSS = "wss://streamer.tastyworks.com"


class TTWebsocket:
    socket: websocket.WebSocketApp = None
    uri: str = None
    auth_token: str = None
    body: dict = {}
    thread: threading.Thread = None
    heartbeat_thread: threading.Thread = None
    active: bool = False

    def __init__(self, is_prod: bool = False, auth_token: str = None) -> None:
        if is_prod:
            self.uri = PROD_WSS
        else:
            self.uri = CERT_WSS
        self.auth_token = auth_token
        self.body["auth-token"] = self.auth_token

    def connect(self):
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
        print(f"wss get {message}")

    def on_error(self, ws, error):
        print(f"wss error {error}")
        self.active = False

    def on_close(self, ws, status_code, message):
        print(f"wss close {status_code} {message}")
        self.active = False

    def on_open(self, ws):
        print(f"wss open")
        self.active = True
        self.heartbeat_thread = threading.Thread(target=self.heartbeat)
        self.heartbeat_thread.start()

    def send(self, action: str = "", value: str = ""):
        if action == "":
            return
        self.body["action"] = action
        self.body["value"] = value
        self.socket.send(json.dumps(self.body))

    def heartbeat(self):
        while self.active:
            self.send(action="heartbeat")
            time.sleep(6)
