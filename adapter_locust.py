import requests
import time
import bsv_auth as auth
from locust import SequentialTaskSet,HttpUser,HttpLocust, task, between,events
import threading
import queue
import asyncio

jwt = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZGFwdGVyLWV0aGVyZXVtIiwiYnJkOmN0IjoiaW50IiwiZXhwIjo5MjIzMzcyMDM2ODU0Nzc1LCJpYXQiOjE2MDQwMDMxNjd9.AOM1mhLekIbKOdbU5Q2PBlLxVzypmkGeS5z1Vt7ENQY'
url = 'http://localhost:9001'
headers = {'Authorization': "Bearer "+jwt};


TX_BLOCK_WORKER_RATIO = 120


block_num = 9200834
#this shared object is a bottleneck, we are better off getting a list of transactions (millions) loading the and processing them in a single locust rather then coordinate 2 locusts
tx_hashes =queue.Queue()
block_hashes = queue.Queue()

def tx_factory(locust):
    global tx_hashes 
    (txhash,blockhash) = tx_hashes.get()
    
    locust.client.get(url=url+'/transactions/'+txhash+'?block_hash='+blockhash,
            headers=headers,
            name="/transactions/")
    tx_hashes.task_done()

def block_factory(locust): 
    global block_hashes
    blockhash = block_hashes.get()
    print(blockhash)
    locust.client.get(url=url+'/blocks/'+blockhash+'?txidsonly=false',
            headers=headers,
            name="/blocks/txidsonly=false")
    block_hashes.task_done()

class GetBlockAndTxids(SequentialTaskSet):

    blockhash = ''

    @task
    def get_blockhash(self):
      global block_num
      block_num = block_num+1
      resp = self.client.get(
            url=url+'/heights/'+str(block_num),
            headers=headers,
            name="/heights")
      json_response_dict = resp.json()
      #{"header":{"eventId":"ethereum-fakenet-blockchain-height-9300834-133","producerNodeId":"3","producerTimestamp":1608523607690,"blockchainId":"ethereum-fakenet"},"height":9300834,"blockHash":"0x308c4c0d49f052e8587a07079ba3035b104fdb091bac7155d74bbbb849ee3719"}
      self.blockhash = json_response_dict['blockHash']
      global block_hashes
      block_hashes.put(json_response_dict['blockHash'])
      pass

    @task
    def get_block_with_txids(self):
        print("blockhash"+self.blockhash)
        resp = self.client.get(
            url=url+'/blocks/'+self.blockhash+'?txidsonly=true',
            headers=headers,
            name="/blocks/txidsonly=true",
        )
        json_response_dict = resp.json()
        print(json_response_dict)
        global tx_hashes
        print("BEFORE:"+str(tx_hashes.qsize()))
        for tx in json_response_dict['transactions']:
          #we need a tuple of tx_hash + block_hash for indexer endpoint
          tx_hashes.put((tx['transactionId'], json_response_dict['hash']))
        print("AFTER:"+str(tx_hashes.qsize()))

       
        pass
        
from locust import events

@events.test_start.add_listener
def on_test_start(**kwargs):
    print("A new test is starting")



class Producer(HttpUser):
  weight = 1 
  tasks  = [GetBlockAndTxids]
  min_wait = 10
  max_wait = 15
  

class TxLocust(HttpUser):
  weight = 1
  tasks = [tx_factory]
  min_wait = 10
  max_wait = 15

class BlockLocust(HttpUser):
  weight=1
  tasks = [block_factory] 
  min_wait = 10
  max_wait = 50






