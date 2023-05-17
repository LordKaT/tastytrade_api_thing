import configparser


class TBConfig:
    config: configparser.ConfigParser = configparser.ConfigParser()
    discord_token: str = None
    discord_channel: int = None
    discord_debug_channel: int = None
    watchlist: str = None

    ivr_elevated: int = 20
    ivr_tasty: int = 35
    ivr_extreme: int = 50

    symbology_unch: str = None
    symbology_down: str = None
    symbology_up: str = None

    def __init__(
        self, path: str = "./config", filename: str = "TastyBot.config"
    ) -> None:
        self.config.read(f"{path}/{filename}")
        self.discord_token = self.config.get("Discord", "token")
        self.discord_channel = int(self.config.get("Discord", "channel"))
        self.discord_debug_channel = int(self.config.get("Discord", "debug_channel"))
        self.watchlist = self.config.get("Discord", "watchlist")
        self.ivr_elevated = int(self.config.get("IVR Levels", "elevated"))
        self.ivr_tasty = int(self.config.get("IVR Levels", "tasty"))
        self.ivr_extreme = int(self.config.get("IVR Levels", "extreme"))
        self.symbology_unch = self.config.get("IVR Symbology", "unch")
        self.symbology_down = self.config.get("IVR Symbology", "down")
        self.symbology_up = self.config.get("IVR Symbology", "up")
