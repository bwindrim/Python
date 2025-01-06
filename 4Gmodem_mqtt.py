import serial
import time

def sendATcommand(modem, command, timeout=2):
    """
    Sends an AT command to a modem and parses the response.

    Args:
        port (str): Serial port (e.g., '/dev/ttyUSB0' or 'COM3').
        baudrate (int): Baud rate for the connection (e.g., 9600).
        command (str): AT command to send (e.g., 'AT' or 'AT+CSQ').
        timeout (int): Timeout in seconds for waiting for a response.

    Returns:
        str: The modem's response to the command.
    """
    try:
        # Ensure the modem is ready
        if not modem.is_open:
            modem.open()
        
        # Send the AT command
        command = "AT" + command.strip() + '\r\n'
        modem.write(command.encode('utf-8'))
        
        # Wait briefly to ensure data is transmitted
        time.sleep(0.1)
        
        # Read the response
        response = modem.read_all().decode('utf-8', errors='ignore').strip()
        
        return response.splitlines()
    
    except serial.SerialException as e:
        return f"Serial exception: {e}"
    except Exception as e:
        return f"General exception: {e}"

# Example usage
if __name__ == "__main__":
    port = "/dev/ttyAMA0"
    baudrate = 115200
    command = "+CIPOPEN=?"

    # Open the serial port
    with serial.Serial(port, baudrate, timeout=2) as modem:
        response = sendATcommand(modem, command)
        print(f"Response:\n{response}")

