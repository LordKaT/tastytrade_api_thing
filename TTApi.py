import json, requests
from TTOrder import *
#import dxfeed as dx
#from datetime import datetime
#from DXHandler import DXHandler

CERT_URI = 'https://api.cert.tastyworks.com'
PROD_URI = 'https://api.tastyworks.com'

CERT_WSS = 'wss://streamer.cert.tastyworks.com'
PROD_WSS = 'wss://streamer.tastyworks.com'

class TTApi:
  username: str = None
  password: str = None
  session_token: str = None
  remember_token: str = None
  streamer_token: str = None
  streamer_uri: str = None
  streamer_websocket_uri: str = None
  streamer_level: str = None
  tt_uri: str = None
  wss_uri: str = None
  headers: dict = {}
  user_data: dict = {}
  
  dxstreamer: any = None

  def __init__(self, username, password) -> None:
    self.headers['Content-Type'] = 'application/json'
    self.username = username
    self.password = password
  
  def __post(self, endpoint, body, headers):
    response = requests.post(self.tt_uri + endpoint, data=json.dumps(body), headers=headers)
    if response.status_code == 201:
      return response.json()
    print(f'Error {response.status_code}')
    print(f'Endpoint: {endpoint}')
    print(f'Body: {body}')
    print(f'Headers: {headers}')
    print(f'Response: {response.text}')
    return None
  
  def __get(self, endpoint, body, headers):
    response = requests.get(self.tt_uri + endpoint, data=json.dumps(body), headers=headers)
    if response.status_code == 200:
      return response.json()
    print(f'Error {response.status_code}')
    print(f'Endpoint: {endpoint}')
    print(f'Body: {body}')
    print(f'Headers: {headers}')
    print(f'Response: {response.text}')
    return None
  
  def __delete(self, endpoint, body, headers):
    response = requests.delete(self.tt_uri + endpoint, data=json.dumps(body), headers=headers)
    if response.status_code == 204:
      return response
    print(f'Error {response.status_code}')
    print(f'Endpoint: {endpoint}')
    print(f'Body: {body}')
    print(f'Headers: {headers}')
    print(f'Response: {response.text}')
    return None

  def login(self, mfa: str = '') -> bool:
    body = {
      'login': self.username,
      'password': self.password,
      'remember-me': True
    }
    
    if mfa != '':
      self.headers['X-Tastyworks-OTP'] = mfa
      self.tt_uri = PROD_URI
      self.wss_uri = PROD_WSS
    else:
      self.tt_uri = CERT_URI
      self.wss_uri = CERT_WSS
    
    response = self.__post('/sessions', body=body, headers=self.headers)
    if response is None:
      return False
    
    self.user_data = response['data']['user']
    self.session_token = response['data']['session-token']
    self.headers['Authorization'] = self.session_token
    
    if mfa != '':
      del self.headers['X-Tastyworks-OTP']

    response = self.__get('/quote-streamer-tokens', body={}, headers=self.headers)
    if response is None:
      return False
    self.streamer_token = response['data']['token']
    self.streamer_uri = response['data']['streamer-url']
    self.streamer_websocket_uri = f'{response["data"]["websocket-url"]}/cometd'
    self.streamer_level = response['data']['level']

    #self.dxstreamer = dx.Endpoint(self.streamer_uri)
    #print(f'Streamer endpoint: {self.dxstreamer.address}')
    #print(f'Streamer status: {self.dxstreamer.connection_status}')
    #trade_sub = self.dxstreamer.create_subscription('Trade')
    #trade_handler = self.dxstreamer.DefaultHandler()
    #trade_sub = trade_sub.set_event_handler(trade_handler)
    #trade_sub.set_event_handler(DXHandler(5))
    #trade_sub.add_symbols(['SPX'])

    return True
  
  def logout(self) -> bool:
    response = self.__delete('/sessions', body={}, headers=self.headers)
    return True

  def validate(self) -> bool:
    response = self.__post('/sessions/validate', body={}, headers=self.headers)
    if response is None:
      return False
    self.user_data['external-id'] = response['data']['external-id']
    self.user_data['id'] = response['data']['id']
    return True
  
  def fetch_accounts(self) -> bool:
    response = self.__get('/customers/me/accounts', {}, self.headers)
    if response is None:
      return False
    self.user_data['accounts'] = []
    for account in response['data']['items']:
      self.user_data['accounts'].append(account)
    return True

  def get_equity_options(self, symbol) -> any:
    response = self.__get(f'/option-chains/{symbol}/nested', body={}, headers=self.headers)

  def simple_order(self, order: TTOrder = None) -> bool:
    if order is None:
      print(f'You need to supply an order.')
      return False
    
    response = self.__post(f'/accounts/{self.user_data["accounts"][0]["account"]["account-number"]}/orders/dry-run', body=order.build_order(), headers=self.headers)

    if response is None:
      return False
    
    print(json.dumps(response))
    return True
