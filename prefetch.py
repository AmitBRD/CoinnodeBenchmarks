import argparse
import auth
import asyncio, random
import aiohttp
from aiofile import async_open,AIOFile, LineReader, Writer
import json 
from progress import print_progress_bar



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
                #print("blockhash:",block_hash, "...")
                await queue.put(block_hash)
        if(block_hash):
          #print('retrieving data')
          async with aiohttp.ClientSession() as session:
            async with session.get(host+'/blocks/'+block_hash+'?txidsonly=true',headers=headers) as response:
                if(response.status == 200):
                  data = await response.json()
                  [await tx_queue.put((tx['transactionId'],block_hash)) for tx in data['transactions']]
        await rnd_sleep(.001) 
        #TODO: this is not optimal , should only render at 60fps 
        print_progress_bar(current_block-start_block,end_block-start_block, prefix = 'Progress:', suffix = 'Complete')
        block_hash = None    
        current_block= current_block+incrementer
 


async def store(queue,file):
  async with async_open("./data/"+file, 'w+') as afp:
    while True:
        token = await queue.get()
        await afp.write(json.dumps(token)+'\n')
        #await afp.fsync()
        queue.task_done()
        #print(f'consumed {token}')
 
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
    await tx_queue.join()
    # cancel the consumers, which are now idle
    for c in consumers:
        c.cancel()

parser = argparse.ArgumentParser(description='Prefetch block and transaction hashes across a block range from host and store to file')
parser.add_argument('host', metavar='host',type=str,
                    help='the host ip and port to that supports getHeight and getBlock requests')
parser.add_argument('jwt', metavar='jwt',type=str,
                    help='the jwt token for host requests')
parser.add_argument('--filepath', metavar='filepath',type=str,default="./",
                    help='the file location the blocks.txt and transactions.txt will be stored to ')
parser.add_argument('--concurrency', metavar='concurrency',type=int,default=10,
                    help='the number of workers to asynchronously fetch url')
parser.add_argument('start_block', metavar='start_block',type=int,
                    help='the start block to feth from inclusive')
parser.add_argument('end_block', metavar='end_block',type=int,
                    help='block to fetch until exclusive')


args = parser.parse_args()
parsed_args = vars(args)
headers = {'Authorization': "Bearer "+parsed_args['jwt']}; 
asyncio.run(main(**vars(args)))