import serial

class ArduinoComs:    
    def __init__(self, port) -> None:
        self.arduino = serial.Serial(port)
        self.ref_val = 100
        print('Coms established')

    def read_and_respond(self):
        print('Reading lines')
        rfid = self.arduino.readline()
        print('Line read - rfid is {}'.format(rfid))
        reading = int(self.arduino.readline())
        print('Line read - value is {}'.format(reading))
        # reading value is integer representing per mille, e.g. 1 = 1 per mille
        if reading < 2:
            self.arduino.write(bytes('r', 'ascii'))
        else:
            self.arduino.write(bytes('g', 'ascii'))
        print('Info sent to Arduino')
        
        

if __name__ == '__main__':
    ard = ArduinoComs('COM3')
    while True:
        ard.read_and_respond()