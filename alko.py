import requests
from time import sleep
from random import uniform

#print(requests.get('http://localhost:5000/add_employee/1/John/Doe'))

for _ in range(8):
    print(requests.get(f'http://localhost:5000/api/add_reading/AAAAAAAA/{uniform(0.0, 0.3):.2f}'))
    #sleep(0.25)