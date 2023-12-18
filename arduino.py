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
        print('Reading lines')
        rfid = self.arduino.readline()
        rfid = codecs.decode(rfid, 'ascii')
        rfid = rfid[:len(rfid)-1]
        print('Line read - rfid is {}'.format(rfid))
        ref_val = int(self.arduino.readline())
        meas_val = int(self.arduino.readline())
        print('Line read - ref_val is {}, meas_val is {}'.format(ref_val, meas_val))
        # is_drunk = meas_val / ref_val > 0.2 and ref_val - meas_val > 5 and meas_val < 70
        # TODO: maybe rewrite using ?rfid=rfid etc. if possible
        # 'g' if all good, 'r' if drunk, 'b' if already blocked in DB, 'n' if RFID not recognized
        # not tested, server not ready to respond just yet
        response = requests.get('http://localhost:5000/api/add_reading/{}/{}/{}'.format(rfid, ref_val, meas_val))
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
    ard = ArduinoComs(sys.argv[1])
    while True:
        ard.read_and_respond()