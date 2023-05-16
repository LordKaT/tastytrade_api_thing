from lib.TTApi import *
from lib.TTConfig import *
from lib.TastyBot.TastyBot import *
from lib.TastyBot.TBConfig import *

ttapi = TTApi()

if not ttapi.login():
    print("login failed")
    exit()

if not ttapi.validate():
    print("validate failed")
    exit()

if not ttapi.fetch_accounts():
    print("fetch accounts failed")
    exit()

tb = TastyBot(ttapi)
