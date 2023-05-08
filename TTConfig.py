import configparser


class TTConfig:
    config: configparser.ConfigParser = configparser.ConfigParser()
    use_prod: bool = False
    use_mfa: bool = False
    username: str = None
    password: str = None
    cert_uri: str = None
    prod_uri: str = None
    cert_wss: str = None
    prod_wss: str = None

    def __init__(self, path: str = ".", filename: str = "tt.config") -> None:
        self.config.read(f"{path}/{filename}")
        self.use_prod = self.config.get("Config", "use_prod")
        self.use_mfa = self.config.get("Config", "use_mfa")
        self.username = self.config.get("Credentials", "username")
        self.password = self.config.get("Credentials", "password")
        self.cert_uri = self.config.get("URI", "cert")
        self.prod_uri = self.config.get("URI", "prod")
        self.cert_wss = self.config.get("WSS", "cert")
        self.prod_wss = self.config.get("WSS", "prod")
