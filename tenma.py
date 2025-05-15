from PyExpLabSys.drivers.tenma import Tenma722535

# Replace with the correct serial port for your Tenma device
serial_port = "COM12"  # Update this to match your setup

try:
    # Initialize the Tenma power supply
    tenma = Tenma722535(serial_port)
    print(f"Connected to Tenma power supply on {serial_port}")

    # Set the voltage to 0V
    tenma.set_voltage(9)
    print("Voltage successfully set to 0V")

    # Optionally, turn off the output
    print("Output turned off")
except Exception as e:
    print(f"Error: {e}")