import json
from enum import Enum

class TTOrderType(Enum):
  LIMIT = 'Limit'
  MARKET = 'Market'

class TTPriceEffect(Enum):
  CREDIT = 'Credit'
  DEBIT = 'Debit'

class TTOrderStats(Enum):
  RECEIVED = 'Received'
  CANCELLED = 'Cancelled'
  FILLED = 'Filled'
  EXPIRED = 'Expired'
  LIVE = 'Live'
  REJECTED = 'Rejected'

class TTTimeInForce(Enum):
  DAY = 'Day'
  GTC = 'GTC'
  GTD = 'GTD'

class TTInstrumentType(Enum):
  EQUITY = 'Equity'
  EQUITY_OPTION = 'Equity Option'
  FUTURE = 'Future'
  FUTURE_OPTION = 'Future Option'
  NOTIONAL_MARKET = 'Notional Market'

class TTLegAction(Enum):
  STO = 'Sell to Open'
  STC = 'Sell to Close'
  BTO = 'Buy to Open'
  BTC = 'Buy to Close'

class TTOptionSide(Enum):
  PUT = 'P'
  CALL = 'C'

class TTOption:
  symbol: str = None

  def __init__(self, symbol: str = None, date: str = None,
                side: TTOptionSide = None, strike: float = None) -> None:
    symbol = symbol.ljust(6, ' ')
    strike = str(int(strike * 100)).replace('.', '').zfill(6)
    self.symbol = symbol + date + side.value + '0' + strike + '0'

class TTOrder:
  order_type: TTOrderType = TTOrderType.LIMIT
  tif: TTTimeInForce = TTTimeInForce.GTC
  price: str = "0.00"
  price_effect: TTPriceEffect = TTPriceEffect.CREDIT
  legs: list = []
  body: dict = {}

  def __init__(self, tif: TTTimeInForce = None, price: float = None,
                price_effect: TTPriceEffect = None, order_type: TTOrderType = None) -> None:
    self.tif = tif
    self.order_type = order_type
    self.price = '{:2f}'.format(price)
    self.price_effect = price_effect

  def add_leg(self, instrument_type: TTInstrumentType = None,
              symbol: str = None, quantity: int = 0,
              action: TTLegAction = None) -> list:
    if len(self.legs) >= 4:
      print(f'Error: cannot have more than 4 legs per order.')
      return
    if instrument_type is None or symbol == None or quantity == 0 or action is None:
      print(f'Invalid parameters')
      print(f'instrument_type: {instrument_type}')
      print(f'symbol: {symbol}')
      print(f'quantity')
    
    self.legs.append({
      'instrument-type': instrument_type.value,
      'symbol': symbol,
      'quantity': quantity,
      'action': action.value
    })

  def build_order(self) -> dict:
    self.body = {
      'time-in-force': self.tif.value,
      'price': self.price,
      'price-effect': self.price_effect.value,
      'order-type': self.order_type.value,
      'legs': self.legs
    }
    print(json.dumps(self.body))
    return self.body
