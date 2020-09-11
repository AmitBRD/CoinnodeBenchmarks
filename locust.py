import requests
import time
import auth
from locust import SequentialTaskSet,HttpUser,HttpLocust, task, between,events
import threading,queue


user = auth.user
password= auth.password
url = auth.url

def tx_factory(locust): 
    tx = tx_hashes.get()
    print("Create Tx TxLocust:"+tx)
    locust.client.post(url=url,
            data='{"jsonrpc": "1.0", "id":"load_tester", "method": "getrawtransaction", "params": ["'+ tx+'"] }',
            auth=(user,password),
            #headers={"authorization": "bearer " + 'token'},
            name="/tx/"+str(tx))
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
            name="/block/"+str(block_num))
      json_response_dict = resp.json()
      self.blockhash = json_response_dict['result']
      pass

    @task
    def get_block(self):
        resp = self.client.post(
            url=url,
            data='{"jsonrpc": "1.0", "id":"curltest", "method": "getblock", "params": ["'+self.blockhash+'",1] }',
            auth=(user,password),
            #headers={"authorization": "bearer " + 'token'},
            name="/getblock/"+self.blockhash,
        )
        json_response_dict = resp.json()
        global tx_hashes
        print("BEFORE:"+str(tx_hashes.qsize()))
        for tx in json_response_dict['result']['tx']:
          tx_hashes.put(tx)
        print("AFTER:"+str(tx_hashes.qsize()))
        pass
        #TODO: get transaction hashs and set tx_hash = []


    #tasks = [tx_factory(tx_hashes)]

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
  weight = 1
  tasks = [tx_factory]
  min_wait = 10
  max_wait = 20

class MyLocust(HttpUser):
  weight=1
  tasks = [SequenceOfTasksSpec1]
  min_wait = 10
  max_wait = 50


# def tx_factory(path):
# 	def _locust(locust):
# 		locust.client.post(
#             url="http://167.172.193.236:8889",
#             data='{"jsonrpc": "1.0", "id":"curltest", "method": "getrawtransaction", "params": ["000000000000009a753dd0a038673fa672d9170d62a794244f9647550e37b701"] }',
#             auth=('michael','jEFnnKPhO93yBYx3C0tGUsUfqz_G3_BKBdM6-CGf1lY='),
#             #headers={"authorization": "bearer " + 'token'},
#             name="/getblock",
#         )

# class SequenceOfTasksSpec2(SequentialTaskSet):

#     @task
#     def get_blockhash(self):
#     	resp = self.client.post(
#             url="http://167.172.193.236:8889",
#             data='{"jsonrpc": "1.0", "id":"load_tester", "method": "getblockhash", "params": ["000000000000009a753dd0a038673fa672d9170d62a794244f9647550e37b701"] }',
#             auth=('michael','jEFnnKPhO93yBYx3C0tGUsUfqz_G3_BKBdM6-CGf1lY='),
#             #headers={"authorization": "bearer " + 'token'},
#             name="/getblockhash",
#         )
#         pass
#  	@task
#     def get_block(self):
#         resp = self.client.post(
#             url="http://167.172.193.236:8889",
#             data='{"jsonrpc": "1.0", "id":"curltest", "method": "getblock", "params": ["000000000000009a753dd0a038673fa672d9170d62a794244f9647550e37b701"] }',
#             auth=('michael','jEFnnKPhO93yBYx3C0tGUsUfqz_G3_BKBdM6-CGf1lY='),
#             #headers={"authorization": "bearer " + 'token'},
#             name="/getblock",
#         )

#     @task
#     def get_transaction(self):
#         pass


# class QuickstartUser(HttpUser):
#     wait_time = between(1, 2)

   

#     @task
#     def get_blockhash(self):
#         resp = self.client.post(
#             url="http://167.172.193.236:8889",
#             data='{"jsonrpc": "1.0", "id":"curltest", "method": "getblock", "params": ["000000000000009a753dd0a038673fa672d9170d62a794244f9647550e37b701"] }',
#             auth=('michael','jEFnnKPhO93yBYx3C0tGUsUfqz_G3_BKBdM6-CGf1lY='),
#             #headers={"authorization": "bearer " + 'token'},
#             name="/getblock",
#         )


    # @task
    # def index_page(self):
    #     self.client.get("/hello")
    #     self.client.get("/world")

    # @task(3)
    # def view_item(self):
    #     for item_id in range(10):
    #         self.client.get(f"/item?id={item_id}", name="/item")
    #         time.sleep(1)

    # def on_start(self):
    #     self.client.post("/login", json={"username":"foo", "password":"bar"})
	#flag = False

