import requests
import time
import auth
from locust import SequentialTaskSet,HttpUser,HttpLocust, task, between,events
import threading,queue


user = auth.user
password= auth.password
url = auth.url

TX_BLOCK_WORKER_RATIO = 4

def tx_factory(locust): 
    tx = tx_hashes.get()
    print("Create Tx TxLocust:"+tx)
    locust.client.post(url=url,
            data='{"jsonrpc": "1.0", "id":"load_tester", "method": "getrawtransaction", "params": ["'+ tx+'"] }',
            auth=(user,password),
            #headers={"authorization": "bearer " + 'token'},
            name="/tx")
    tx_hashes.task_done()

block_num = 464000
#this shared object is a bottleneck, we are better off getting a list of transactions (millions) loading the and processing them in a single locust rather then coordinate 2 locusts
tx_hashes = queue.LifoQueue()

class SequenceOfTasksSpec1(SequentialTaskSet):

    blockhash = ''

    @task
    def get_blockhash(self):
      global block_num
      block_num = block_num+1
      resp = self.client.post(
            url=url,
            data='{"jsonrpc": "1.0", "id":"load_tester", "method": "getblockhash", "params": ['+ str(block_num)+'] }',
            auth=(user,password),
            #headers={"authorization": "bearer " + 'token'},
            name="/block")
      json_response_dict = resp.json()
      self.blockhash = json_response_dict['result']
      pass

    @task
    def get_block(self):
        resp = self.client.post(
            url=url,
            data='{"jsonrpc": "1.0", "id":"curltest", "method": "getblock", "params": ["'+self.blockhash+'",2] }',
            auth=(user,password),
            #headers={"authorization": "bearer " + 'token'},
            name="/getblock",
        )
        json_response_dict = resp.json()
        pass

    @events.test_start.add_listener
    def on_test_start(**kwargs):
      print("A new test is starting")
      pass

    @events.test_stop.add_listener
    def on_test_stop(**kwargs):
      print("A new test is ending")
      pass

class SequenceOfTasksSpec2(SequenceOfTasksSpec1):

    @task
    def get_block(self):
        resp = self.client.post(
            url=url,
            data='{"jsonrpc": "1.0", "id":"curltest", "method": "getblock", "params": ["'+self.blockhash+'",1] }',
            auth=(user,password),
            #headers={"authorization": "bearer " + 'token'},
            name="/getblock",
        )
        json_response_dict = resp.json()
        global tx_hashes
        print("BEFORE:"+str(tx_hashes.qsize()))
        for tx in json_response_dict['result']['tx']:
          tx_hashes.put(tx)
        print("AFTER:"+str(tx_hashes.qsize()))
        pass
       

    @events.test_start.add_listener
    def on_test_start(**kwargs):
      print("A new test is starting")
      pass

    @events.test_stop.add_listener
    def on_test_stop(**kwargs):
      print("A new test is ending")
      pass

#TXLocust 20 times larger workpool then block

class TxLocust(HttpUser):
  weight = TX_BLOCK_WORKER_RATIO
  tasks = [tx_factory]
  min_wait = 10
  max_wait = 15

class BlockLocust(HttpUser):
  weight=1
  tasks = [SequenceOfTasksSpec2] 
  min_wait = 10
  max_wait = 50


#If you want to run on old spec benchmark then comment above 2 and enable below

# class BlockLocust(HttpUser)
#   weight = 1
#   tasks = [SequenceOfTasksSpec1]
#   min_wait = 10
#   max_wait = 20



