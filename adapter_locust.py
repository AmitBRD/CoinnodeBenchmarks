import requests
import time
import bsv_auth as auth
from locust import SequentialTaskSet,HttpUser,HttpLocust, task, between,events
import threading
from gevent import queue


jwt = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZGFwdGVyLWV0aGVyZXVtIiwiYnJkOmN0IjoiaW50IiwiZXhwIjo5MjIzMzcyMDM2ODU0Nzc1LCJpYXQiOjE2MDQwMDMxNjd9.AOM1mhLekIbKOdbU5Q2PBlLxVzypmkGeS5z1Vt7ENQY'
url = 'http://localhost:9001'
headers = {'Authorization': "Bearer "+jwt};


TX_BLOCK_WORKER_RATIO = 120



block_num = 9200834
#this shared object is a bottleneck, we are better off getting a list of transactions (millions) loading the and processing them in a single locust rather then coordinate 2 locusts
tx_hashes = queue.JoinableQueue()
block_hashes = queue.JoinableQueue()

def tx_factory(locust):
    #global tx_hashes 
    (txhash,blockhash) = tx_hashes.get()
    print(txhash)
    print(blockhash)
    locust.client.get(url=url+'/transactions/'+txhash+'?block_hash='+blockhash,
            headers=headers,
            name="/transactions/")
    tx_hashes.task_done()

def block_factory(locust): 
    #global block_hashes
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
        

    # @events.test_start.add_listener
    # def on_test_start(**kwargs):
    #   print("A new test is starting")
    #   pass

    # @events.test_stop.add_listener
    # def on_test_stop(**kwargs):
    #   print("A new test is ending")
    #   pass

# class GetBlock(SequentialTaskSet):
#     blockhash = ''

   
#     @task
#     def get_block(self):

#         print("blockhash"+self.blockhash)
#         resp = self.client.get(
#             url=url+'/blocks/'+self.blockhash+'?txidsonly=false',
#             headers=headers,
#             name="/blocks/txidsonly=true",
#         )
#         json_response_dict = resp.json()
#         print(json_response_dict)
#         global tx_hashes
#         print("BEFORE:"+str(tx_hashes.qsize()))
#         for tx in json_response_dict['transactions']:
#           #we need a tuple of tx_hash + block_hash for indexer endpoint
#           tx_hashes.put((tx['transactionId'], json_response_dict['hash']))
#         print("AFTER:"+str(tx_hashes.qsize()))
#         pass

#     @task
#     def get_block(self):
#         global block_num
#         global PAUSE_BLOCK
#         if(block_num > PAUSE_BLOCK):
#           return
#         print('fetching block hash now:'+ self.blockhash)
#         resp = self.client.post(
#             url=url,
#             data='{"jsonrpc": "1.0", "id":"curltest", "method": "getblock", "params": ["'+self.blockhash+'",1] }',
#             #headers={"authorization": "bearer " + 'token'},
#             name="/getblock",
#         )
#         json_response_dict = resp.json()
#         global tx_hashes
#         #print("BEFORE:"+str(tx_hashes.qsize()))
#         for tx in json_response_dict['result']['tx']:
#           tx_hashes.put(tx)
#         print("AFTER:"+str(tx_hashes.qsize()))
#         pass
       
#     # @task
#     # def my_task(self):
#     #     from gevent.pool import Group
#     #     group = Group()
#     #     group.spawn(lambda: self.client.get("/some_url")
#     #     group.spawn(lambda: self.client.get("/some_url")
#     #     group.join() # wait for greenlets to finish

#     @events.test_start.add_listener
#     def on_test_start(**kwargs):
#       print("A new test is starting")
#       pass

#     @events.test_stop.add_listener
#     def on_test_stop(**kwargs):
#       print("A new test is ending")
#       pass

#TXLocust 20 times larger workpool then block
import asyncio
from aiofile import async_open,AIOFile, LineReader, Writer
import os
import random
import time



async def randsleep(a: int = 1, b: int = 5, caller=None) -> None:
    i = random.randint(10, 20)
    if caller:
        print(f"{caller} sleeping for {i} milliseconds.")
    await asyncio.sleep(i*0.001)

async def produce(name: int, q: asyncio.Queue) -> None:
    async with AIOFile("./test.txt", 'rb') as afp:
      reader = LineReader(afp)
      while True:
        await randsleep(caller=f"Producer {name}")
        async for line in reader:
            t = time.perf_counter()
            await q.put((line, t))
            print(f"Producer {name} added <{line}> to queue.")

async def consume(name: int, q: asyncio.Queue) -> None:
    while True:
        await randsleep(caller=f"Consumer {name}")
        i, t = await q.get()
        now = time.perf_counter()
        print(f"Consumer {name} got element <{i}>"
              f" in {now-t:0.5f} seconds.")
        q.task_done()

async def main():
    q = asyncio.Queue(maxsize=1)
    producers = [asyncio.create_task(produce(1, q)) ]
    consumers = [asyncio.create_task(consume(1, q)) ]
    await asyncio.gather(*producers)
    await q.join()  # Implicitly awaits consumers, too
    for c in consumers:
        c.cancel()

from locust import events

@events.test_start.add_listener
def on_test_start(**kwargs):
    print("A new test is starting")



class Producer(HttpUser):
  weight = 1 
  tasks  = [GetBlockAndTxids]
  min_wait = 10
  max_wait = 15
  

# class Indexer(HttpUser):
#   weight = 1
#   tasks = [GetBlock, GetTransaction]

class TxLocust(HttpUser):
  weight = 20
  tasks = [tx_factory]
  min_wait = 10
  max_wait = 15

class BlockLocust(HttpUser):
  weight=1
  tasks = [block_factory] 
  min_wait = 10
  max_wait = 50


import threading
def loop_in_thread(loop):
  asyncio.set_event_loop(loop)
  loop.run_until_complete(main())

loop = asyncio.get_event_loop()
t = threading.Thread(target=loop_in_thread, args=(loop,))
t.start()




#If you want to run on old spec benchmark then comment above 2 and enable below

# class BlockLocust(HttpUser)
#   weight = 1
#   tasks = [SequenceOfTasksSpec1]
#   min_wait = 10
#   max_wait = 20



