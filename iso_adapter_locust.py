import gevent
import gevent.monkey
gevent.monkey.patch_all()
from gevent import queue
from locust import SequentialTaskSet,HttpUser,HttpLocust, task, between,events
import json
import auth

url = 'http://localhost:9001'
headers = {'Authorization': "Bearer "+auth.jwt};

def reader(data_file:str, queue:queue.Queue):
  with open('./data/'+data_file, 'rb') as f:
    data = f.readline()
    while data:
      data = f.readline()
      #print(data)
      queue.put(data,block=True)
      gevent.sleep(0.01)


tx_queue = queue.Queue()

def spawn_greenlets():
  #gevent.signal(signal.SIGQUIT, gevent.kill)
  greenlets = [gevent.spawn(reader,'transactions.txt',tx_queue)]
  # try:
  #     gevent.joinall(greenlets)
  # except KeyboardInterrupt:
  #     print("Exiting...")



def tx_factory(locust):
    txhash,blockhash = json.loads(tx_queue.get())
    print(txhash)
    locust.client.get(url=url+'/transactions/'+txhash+'?block_hash='+blockhash,
            headers=headers,
            name="/transactions/")

class TxLocust(HttpUser):
  weight = 1
  tasks = [tx_factory]
  min_wait = 1
  max_wait = 5
 

spawn_greenlets()