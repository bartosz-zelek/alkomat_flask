import time

import requests
import serial

from helpers import ip


class ArduinoSerialClient:
    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 1.0):
        """Open serial port and give Arduino time to reset."""
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        time.sleep(2)  # wait for Arduino reset

    def close(self):
        """Close the serial port."""
        if self.ser and self.ser.is_open:
            self.ser.close()

    def _write_line(self, line: str):
        """Send a single line (with LF) to Arduino."""
        self.ser.reset_input_buffer()
        data = (line.strip() + "\n").encode("utf-8")
        self.ser.write(data)

    def _read_line(self) -> str:
        """Read a line back from Arduino (strips CR/LF)."""
        raw = self.ser.readline()
        return raw.decode("utf-8", errors="ignore").strip()

    def send_brethalyzer_id(self, device_id: str) -> None:
        """Send the Brethalyzer ID; Arduino will echo or ack."""
        self._write_line(device_id)
        # optionally read echo:
        _ = self._read_line()

    def read_max_adc(self) -> int:
        """After blowing, Arduino sends max ADC value as an integer."""
        line = self._read_line()
        return int(line) if line.isdigit() else 0

    def send_response(self, response: str) -> None:
        """Send back 'ACCEPTED' or 'REJECTED'."""
        self._write_line(response)

    def read_uuid(self) -> str:
        """Block until Arduino sends a non‐empty UUID line."""
        while True:
            line = self._read_line()
            if line:
                return line


if __name__ == "__main__":
    client = ArduinoSerialClient(port="COM9")
    try:
        breathalyzer_id = input("Enter Brethalyzer ID: ")
        client.send_brethalyzer_id(breathalyzer_id)
        uuid = client.read_uuid()
        print(f"UUID: {uuid}")
        # send response to server
        response = requests.get(f"http://{ip}/add_reading/uuid/{uuid}")
        print(f"Server response: {response} {response.content}")
    finally:
        client.close()
