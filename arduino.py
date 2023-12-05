import serial
import codecs
import requests

class ArduinoComs:    
    def __init__(self, port) -> None:
        self.arduino = serial.Serial(port)
        self.ref_val = 100
        print('Coms established')

    def read_and_respond(self):
        print('Reading lines')
        rfid = self.arduino.readline()
        rfid = codecs.decode(rfid, 'ascii')
        print('Line read - rfid is {}'.format(rfid))
        ref_val = int(self.arduino.readline())
        meas_val = int(self.arduino.readline())
        print('Line read - ref_val is {}, meas_val is {}'.format(ref_val, meas_val))
        is_drunk = meas_val / ref_val > 0.2 and ref_val - meas_val > 5 and meas_val < 70
        # TODO: maybe rewrite using ?rfid=rfid etc.
        # 'g' if all good, 'r' if drunk, 'b' if already blocked in DB, 'n' if RFID not recognized
        # mocked response
        response = requests.get('http://localhost:5000/add_reading/{}/{}'.format(rfid, is_drunk))
        response_char = response.text
        self.arduino.write(bytes(response_char, 'ascii'))
        print('Info sent to Arduino')
        
        

if __name__ == '__main__':
    # change COM for RPi
    ard = ArduinoComs('COM3')
    while True:
        ard.read_and_respond()