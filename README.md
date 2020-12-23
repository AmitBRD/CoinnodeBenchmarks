pip3 install locust

add auth.py in base directory set coinnode basic auth properties:

user= 'username'
password= 'password'

locust -f locust.py

go to: http://localhost:8089

spawn user: 1
spawn rate : 1
set url: http://167.172.193.236:8889





in headless mode





Running prefetch

python3.9 prefetch.py ADAPTER_URI 'JWT_TOKEN' START_BLOCK END_BLOCK --concurrency 10

e.g. 

python3.9 prefetch.py http://127.0.0.1:9001 '...JWT...' 9313041 9313941 --concurrency 10

generates 2 files:
data/blocks.txt
data/transactions.txt




