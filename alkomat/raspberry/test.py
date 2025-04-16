import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)  # Adjust port if needed
time.sleep(2)  # Wait for Arduino to reset

# ser.write(b'1')  # Send '1' to Arduino
while True:
    response = ser.readline().decode().strip()
    if response:
        print(response)
    
