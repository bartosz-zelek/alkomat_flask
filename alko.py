import requests
from time import sleep
from random import uniform

print(requests.get('http://localhost:5000/add_employee/1/John/Doe'))

for i in range(10):
    print(requests.get('http://localhost:5000/add_reading/1/{}'.format(round(uniform(0.0, 0.4), 2))))
    sleep(5)