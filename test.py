from TTApi import TTApi
from TTOrder import *

ttapi = TTApi('THIS IS SUPPOSED TO BE A USERNAME', 'THIS IS SUPPOSED TO BE A PASSWORD')

print('login')
mfa = input('MFA: ')
if not ttapi.login(mfa):
  exit()

print('validate')
if not ttapi.validate():
  exit()

print('fetch accounts')
if not ttapi.fetch_accounts():
  exit()

order = TTOrder(TTTimeInForce.GTC, 0.25, TTPriceEffect.CREDIT, TTOrderType.LIMIT)
option = TTOption('MPW', '230721', TTOptionSide.PUT, 6.00)
order.add_leg(TTInstrumentType.EQUITY_OPTION, option.symbol, 1, TTLegAction.STO)
option = TTOption('MPW', '230721', TTOptionSide.CALL, 5.00)
order.add_leg(TTInstrumentType.EQUITY_OPTION, option.symbol, 1, TTLegAction.BTO)

ttapi.simple_order(order)

'''
print('Websocket stuff')
ws_url = 'wss://streamer.cert.tastyworks.com'
#ws_url = 'wss://streamer.tastyworks.com'

body = {
  'auth-token': ttapi.session_token,
  'action': '',
  'value': ''
}

def on_message(ws, message):
  print(f'wss get {message}')

def on_error(ws, error):
  print(f'wss error: {error}')

def on_close(ws, status_code, message):
  print(f'wss close: {status_code} {message}')

def on_open(ws):
  print(f'wss open')

  body['action'] = 'heartbeat'
  body['value'] = ''
  ws.send(json.dumps(body))

  body['action'] = 'public-watchlists-subscribe'
  body['value'] = ''
  print(json.dumps(body))
  ws.send(json.dumps(body))

  body['action'] = 'connect'
  body['value'] = [f'{ttapi.user_data["accounts"][0]["account"]["account-number"]}']
  print(json.dumps(body))
  ws.send(json.dumps(body))

ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)

ws.run_forever()
'''
print('logout')
if not ttapi.logout():
  exit()
