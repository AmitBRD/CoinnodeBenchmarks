pip3 install locust

add auth.py in base directory set coinnode basic auth properties:

user= 'username'
password= 'password'

locust -f locust.py

go to: http://localhost:8089

spawn user: 1
spawn rate : 1
set url: http://167.172.193.236:8889

