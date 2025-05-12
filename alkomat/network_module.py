import time

import requests
import serial


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
    ip = "150.254.45.26:5000"
    client = ArduinoSerialClient(port="COM9")
    try:
        breathalyzer_id = input("Enter Brethalyzer ID: ")
        client.send_brethalyzer_id(breathalyzer_id)
        while True:
            print("Waiting for breathalyzer response...")
            uuid = client.read_uuid()
            print(f"Received UUID: {uuid}")
            user_id = None
            max_adc = None
            while user_id is None:
                response = requests.get(f"http://{ip}/api/uuid/{uuid}")
                print(f"Server response: {response}\n")
                user_id = response.json().get("user_id")
                time.sleep(1)
            print(f"User ID: {user_id}")
            client.send_response("#" + user_id)
            print("Waiting for max ADC...")
            while max_adc is None or max_adc == 0:
                max_adc = client.read_max_adc()
                print(f"Max ADC: {max_adc}")
                time.sleep(1)
            response = requests.get(
                f"http://{ip}/api/add_reading_uuid/{uuid}/{max_adc}/{breathalyzer_id}",
            )
            print(f"Server response after reading: {response}\n")
            response_msg = response.json()["message"]
            print("Response: {}".format(response_msg))
            response_char = ""
            if response_msg == "USER DOESN'T EXIST":
                response_char = "USER DOESN'T EXIST"
            elif response_msg == "USER BLOCKED":
                response_char = "USER BLOCKED"
            elif response_msg == "ENTRY BLOCKED":
                response_char = "ENTRY BLOCKED"
            elif response_msg == "ACCEPTED":
                response_char = "ACCEPTED"
            elif response_msg == "CONNECTION ERROR":
                response_char = "CONNECTION ERROR"
            else:
                response_char = "UNKNOWN"
            client.send_response(response_char)
            print(f"Response sent: {response_char}")

    finally:
        client.close()
