import requests
from time import sleep
from random import uniform

#print(requests.get('http://localhost:5000/add_employee/1/John/Doe'))

for _ in range(5):
    print(requests.get('http://localhost:5000/api/add_reading/1/{}'.format(round(uniform(0.0, 0.19), 2))))
    #sleep(0.25)