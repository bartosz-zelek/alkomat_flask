import sys
import codecs
import serial
import requests

class ArduinoComs:    
    def __init__(self, port) -> None:
        self.arduino = serial.Serial(port)
        self.ref_val = 100
        print('Coms established')

    def read_and_respond(self):
        print('Face recognition')
        user_id = input("Face ID: ")
        print('Writing to Arduino: {}'.format(user_id))
        self.arduino.write(bytes(user_id, 'ascii'))
        print('Line read - user_id is {}'.format(user_id))
        meas_val = int(self.arduino.readline())
        print('Line read - meas_val is {}'.format(meas_val))
        # is_drunk = meas_val / ref_val > 0.2 and ref_val - meas_val > 5 and meas_val < 70
        # TODO: maybe rewrite using ?user_id=user_id etc. if possible
        # 'g' if all good, 'r' if drunk, 'b' if already blocked in DB, 'n' if user_id not recognized
        # not tested, server not ready to respond just yet
        response = requests.get('http://localhost:5000/api/add_reading/{}/{}'.format(user_id, meas_val))
        response_msg = response.json()['message']
        print("Response: {}".format(response_msg))
        response_char = ''
        if response_msg == "USER DOESN'T EXIST":
            response_char = 'n'
        elif response_msg == "USER BLOCKED":
            response_char = 'b'
        elif response_msg == "ENTRY BLOCKED":
            response_char = 'r'
        elif response_msg == "ACCEPTED":
            response_char = 'g'
        else:
            response_char = 'n'
        print('Writing to Arduino: {}'.format(response_char))
        self.arduino.write(bytes(response_char, 'ascii'))
        print('Info sent to Arduino')
        
        

if __name__ == '__main__':
    # change arg in terminal
    ard = ArduinoComs('/dev/ttyUSB0')
    while True:
        ard.read_and_respond()