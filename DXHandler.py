from datetime import datetime
import dxfeed as dx
from dxfeed.core.utils.data_class import DequeWithLock

class DXHandler(dx.EventHandler):
  def __init__(self, n_events):
    self.spx_data = {
      'Open': DequeWithLock(maxlen=n_events),
      'High': DequeWithLock(maxlen=n_events),
      'Low': DequeWithLock(maxlen=n_events),
      'Close': DequeWithLock(maxlen=n_events),
      'Time': DequeWithLock(maxlen=n_events)
    }
    self.spx_buffer = None
  
  def update(self, events):
    for event in events:
      if event.symbol.startswith('SPX'):
        if self.spx_buffer and event.time != self.spx_buffer.time:
          print(f'DXFeed: {self.spx_buffer}')
          #self.spx_data['Open'].append(self.spx_buffer.open)
          #self.spx_data['High'].append(self.spx_buffer.high)
          #self.spx_data['Low'].append(self.spx_buffer.low)
          #self.spx_data['Close'].append(self.spx_buffer.close)
          #self.spx_data['Time'].append(datetime.fromtimestamp(self.spx_buffer.time // 1000))
        self.spx_buffer = event
