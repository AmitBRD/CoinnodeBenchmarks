# import asyncio
# import aiohttp


# CONCURRENT = 2

# async def fetch(sem, session, url):
#     async with sem, session.get(url) as response:
#         with open("some_file_name.json", "wb") as out:
#             async for chunk in response.content.iter_chunked(4096)
#                 out.write(chunk)


# async def fetch_all(urls, loop):
#     sem = asyncio.Semaphore(CONCURRENT) 
#     async with aiohttp.ClientSession(loop=loop) as session:
#         results = await asyncio.gather(
#             *[fetch(sem, session, url) for url in urls]
#         )
#         return results


# if __name__ == '__main__':

#     urls = (
#         "https://public.api.openprocurement.org/api/2.5/tenders/6a0585fcfb05471796bb2b6a1d379f9b",
#         "https://public.api.openprocurement.org/api/2.5/tenders/d1c74ec8bb9143d5b49e7ef32202f51c",
#         "https://public.api.openprocurement.org/api/2.5/tenders/a3ec49c5b3e847fca2a1c215a2b69f8d",
#         "https://public.api.openprocurement.org/api/2.5/tenders/52d8a15c55dd4f2ca9232f40c89bfa82",
#         "https://public.api.openprocurement.org/api/2.5/tenders/b3af1cc6554440acbfe1d29103fe0c6a",
#         "https://public.api.openprocurement.org/api/2.5/tenders/1d1c6560baac4a968f2c82c004a35c90",
#     ) 

#     loop = asyncio.get_event_loop()
#     data = loop.run_until_complete(fetch_all(urls, loop))
#     print(data)

import argparse

import asyncio, random
import aiohttp
from aiofile import async_open,AIOFile, LineReader, Writer


jwt = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZGFwdGVyLWV0aGVyZXVtIiwiYnJkOmN0IjoiaW50IiwiZXhwIjo5MjIzMzcyMDM2ODU0Nzc1LCJpYXQiOjE2MDQwMDMxNjd9.AOM1mhLekIbKOdbU5Q2PBlLxVzypmkGeS5z1Vt7ENQY'
headers = {'Authorization': "Bearer "+jwt};
 
async def rnd_sleep(t):
    # sleep for T seconds on average
    await asyncio.sleep(t * random.random() * 2)
 
async def fetch(queue,tx_queue,host,start_block,end_block,incrementer,partition):
    current_block = start_block
    block_hash = None
    while current_block< end_block:
        async with aiohttp.ClientSession() as session:
          async with session.get(host+'/heights/'+str(current_block+partition),headers=headers) as response:
              if(response.status == 200):
                result = await response.json()
                block_hash = result['blockHash']
                print("blockhash:",block_hash, "...")
                await queue.put(block_hash)
        if(block_hash):
          print('retrieving data')
          async with aiohttp.ClientSession() as session:
            async with session.get(host+'/blocks/'+block_hash+'?txidsonly=true',headers=headers) as response:
                if(response.status == 200):
                  data = await response.json()
                  [await tx_queue.put((tx['transactionId'],block_hash)) for tx in data['transactions']]
        await rnd_sleep(.001)  
        block_hash = None    
        current_block= current_block+incrementer
 
import json 

async def store(queue,file):
  async with async_open("./data/"+file, 'w+') as afp:
    while True:
        token = await queue.get()
        await afp.write(json.dumps(token)+'\n')
        #await afp.fsync()
        queue.task_done()
        print(f'consumed {token}')
 
async def main(host='',start_block=0,end_block=0,concurrency=0,**kwargs):
    queue = asyncio.Queue()
    tx_queue = asyncio.Queue()
    
    # fire up the both producers and consumers
    producers = [asyncio.create_task(fetch(queue,tx_queue,host,start_block,end_block,concurrency,p))
                 for p in range(concurrency)]
    consumers = [asyncio.create_task(store(queue,'blocks.txt')),asyncio.create_task(store(tx_queue,'transactions.txt')) ]
 
    # with both producers and consumers running, wait for
    # the producers to finish
    await asyncio.gather(*producers)
    print('---- done producing')
 
    # wait for the remaining tasks to be processed
    await queue.join()
 
    # cancel the consumers, which are now idle
    for c in consumers:
        c.cancel()

parser = argparse.ArgumentParser(description='Prefetch block and transaction hashes across a block range from host and store to file')
parser.add_argument('host', metavar='host',type=str,
                    help='the host ip and port to that supports getHeight and getBlock requests')
parser.add_argument('--filepath', metavar='filepath',type=str,default="./",
                    help='the file location the blocks.txt and transactions.txt will be stored to ')
parser.add_argument('--concurrency', metavar='concurrency',type=int,default=10,
                    help='the number of workers to asynchronously fetch url')
parser.add_argument('start_block', metavar='start_block',type=int,
                    help='the start block to feth from inclusive')
parser.add_argument('end_block', metavar='end_block',type=int,
                    help='block to fetch until exclusive')

args = parser.parse_args()

print(vars(args))

asyncio.run(main(**vars(args)))