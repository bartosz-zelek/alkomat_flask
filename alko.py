import requests
from time import sleep
from random import uniform

#print(requests.get('http://localhost:5000/add_employee/1/John/Doe'))

for _ in range(5):
    print(requests.get(f'http://localhost:5000/api/add_reading/BBBBBBB/{uniform(0.2, 0.4):.2f}'))
    #sleep(0.25)