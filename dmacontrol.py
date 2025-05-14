import serial
import serial.tools.list_ports
import time
import datetime
import pytz
import threading
import tkinter as tk
import json
import pandas as pd
import os
import csv
import shutil
from ttkbootstrap import Style
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import Combobox, Button, Label, Frame, Entry
from tkinter import filedialog


def copy_to_dropbox_periodically(sync_info, interval=3600):
    """Continuously copies current log file to Dropbox every `interval` seconds."""
    while running:
        try:
            if sync_info["local"] and os.path.exists(sync_info["local"]):
                shutil.copy(sync_info["local"], sync_info["dropbox"])
                terminal.insert(tk.END, f"[Dropbox Sync] Copied to {sync_info['dropbox']}\n")
        except Exception as e:
            terminal.insert(tk.END, f"[Dropbox Sync Error] {e}\n")
        time.sleep(interval)

try:
    import nidaqmx
    from nidaqmx.constants import AcquisitionType
    HAS_DAQ = True
except ImportError:
    HAS_DAQ = False

CONFIG_FILE = "orbi_inlet_config.json"
sheath_flow = 14
save_interval = 10
switch_interval = 600
settle_delay = 5
valve_state = "A"

loc_tz = pytz.timezone('Etc/GMT-0')
utc_tz = pytz.timezone('UTC')
fmt = '%Y %m %d %H %M %S %z'
new_line = '\n'.encode('UTF-8')

filename = None
dropfile = None
dropbox_sync_info = {"local": None, "dropbox": None}
running = False
ser = None
ser_mbed = None
ser_valve = None
saved_config = {}
particle_sizes = []

def load_config():
    global saved_config, valve_state, particle_sizes, sheath_flow, save_interval, switch_interval, settle_delay, corona_voltage, corona_enabled
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            saved_config = json.load(f)
            valve_state = saved_config.get("valve_state", "A")
            particle_sizes = saved_config.get("particle_sizes", [30, 50, 100])
            sheath_flow = saved_config.get("sheath_flow", 14)
            corona_voltage = saved_config.get("corona_voltage", 4500)
            corona_enabled = saved_config.get("corona_enabled", False)
            save_interval = saved_config.get("save_interval", 10)
            switch_interval = saved_config.get("switch_interval", 600)
            settle_delay = saved_config.get("settle_delay", 5)
    else:
        saved_config = {}
        particle_sizes = [30, 50, 100]
        sheath_flow = 14

def save_config(cpc_port, mbed_port, daq_device, valve_port, state):
    global save_interval, switch_interval, settle_delay
    save_interval = int(record_time_entry.get())
    switch_interval = int(switch_interval_entry.get())
    settle_delay = int(settle_delay_entry.get())
    corona_voltage = float(corona_voltage_entry.get())
    corona_enabled = corona_toggle_var.get()
    with open(CONFIG_FILE, 'w') as f:
        json.dump({
            "cpc_port": cpc_port,
            "mbed_port": mbed_port,
            "daq_device": daq_device,
            "valve_port": valve_port,
            "alicat_port": alicat_box.get(),
            "valve_state": state,
            "particle_sizes": particle_sizes,
            "sheath_flow": sheath_flow,
            "save_interval": save_interval,
            "switch_interval": switch_interval,
            "settle_delay": settle_delay,
            "corona_voltage": corona_voltage,
            "corona_enabled": corona_enabled
        }, f)

def load_sequence_file():
    global sequence_steps, use_sequence_mode
    ini_dir = os.path.join(os.path.dirname(__file__), 'sequences')
    file_path = filedialog.askopenfilename(initialdir=ini_dir, filetypes=[("CSV Files", "*.csv")])
    if file_path:
        with open(file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            sequence_steps = [row for row in reader]
            df = pd.read_csv(file_path)
        use_sequence_mode = True
        terminal.insert(tk.END, f"[Sequence] Loaded {len(sequence_steps)} steps from {file_path}\n")
        terminal.insert(tk.END, df)
    else:
        use_sequence_mode = False

def manualmode():
    stop_measurement()
    terminal.insert(tk.END, "[Measurement] Stopped.\n")
    global use_sequence_mode
    use_sequence_mode = False
    terminal.insert(tk.END, "[Manual Mode] Sequence mode disabled.\n")
    

def update_sizes():
    global particle_sizes, sheath_flow, save_interval, switch_interval, settle_delay
    try:
        particle_sizes = list(map(float, size_entry.get().split(",")))
        sheath_flow = float(sheath_entry.get())
        save_interval = int(record_time_entry.get())
        switch_interval = int(switch_interval_entry.get())
        settle_delay = int(settle_delay_entry.get())
        save_config(cpc_box.get(), mbed_box.get(), daq_box.get(), valve_box.get(), valve_state)
    except Exception as e:
        terminal.insert(tk.END, f"[Config Error] {e}\n")

def list_available_devices():
    ports = ["None"] + [port.device for port in serial.tools.list_ports.comports()]
    daq_devices = []
    if HAS_DAQ:
        try:
            daq_devices = [device.name for device in nidaqmx.system.System.local().devices]
        except Exception:
            pass
    return ports, daq_devices

def update_com_ports_loop():
    while True:
        ports, daqs = list_available_devices()
        root.after(0, lambda: update_comboboxes(ports, daqs))
        time.sleep(2)

def update_comboboxes(ports, daqs):
    cpc_box["values"] = ports
    mbed_box["values"] = ports
    daq_box["values"] = daqs
    valve_box["values"] = ports
    alicat_box["values"] = ports
    alicat_box["values"] = ports


def toggle_corona_voltage(device_name, current_state):
    new_state = not current_state
    corona_toggle_var.set(new_state)
    try:
        voltage = float(corona_voltage_entry.get())
    except ValueError:
        voltage = 4500  # fallback default

    voltage_out = voltage / 5000 * 10 if new_state else 0.0

    if HAS_DAQ and device_name != "None":
        try:
            with nidaqmx.Task() as task:
                task.ao_channels.add_ao_voltage_chan(f"{device_name}/ao1")
                task.write(voltage_out)
            terminal.insert(tk.END, f"[Corona HV] Output set to {voltage_out:.2f} V ({'ON' if new_state else 'OFF'}) \n")
        except Exception as e:
            terminal.insert(tk.END, f"[Corona HV Error] {e}!!!!!!!!\n")
    else:
        terminal.insert(tk.END, "[Corona HV] NI DAQ not available or not selected.\n")

    save_config(cpc_box.get(), mbed_box.get(), daq_box.get(), valve_box.get(), valve_state)

def toggle_valve(port, button):
    global valve_state
    try:
        if port != "None":
            with serial.Serial(port, 9600, timeout=1) as valve_serial:
                if valve_state == "A":
                    valve_serial.write(b"B")
                    valve_state = "B"
                    button.config(text="Valve B Open", bootstyle=SUCCESS)
                else:
                    valve_serial.write(b"A")
                    valve_state = "A"
                    button.config(text="Valve A Open", bootstyle=PRIMARY)
                save_config(cpc_box.get(), mbed_box.get(), daq_box.get(), valve_box.get(), valve_state)
        else:
            terminal.insert(tk.END, "[Valve] No COM port selected.\n")
    except Exception as e:
        terminal.insert(tk.END, f"[Valve Error] {e}\n")

def voltage_from_size(dp):
    from bisect import bisect_left
    # Updated DMA calibration table: dp (nm) → HV (V)
    calibration = {
        1: 17.17,
        10: 23.37,
        100: 341.3,
        300: 5000
    }
    dps = sorted(calibration.keys())
    hvs = [calibration[d] for d in dps]

    dp = dp * 1e9 if dp < 1 else dp  # Convert m to nm if needed

    if dp <= dps[0]:
        hv = hvs[0]
    elif dp >= dps[-1]:
        hv = hvs[-1]
    else:
        i = bisect_left(dps, dp)
        x0, x1 = dps[i - 1], dps[i]
        y0, y1 = hvs[i - 1], hvs[i]
        hv = y0 + (dp - x0) * (y1 - y0) / (x1 - x0)

    analog = hv / 500  # Convert HV to 0–10V analog signal (5kV source)
    return max(0.0, min(10.0, analog))

def set_sheath_flow_mbed():
    port = mbed_box.get()
    if port != "None":
        try:
            with serial.Serial(port, 9600, timeout=1) as mbed_serial:
                cmd = f"write pid_setpoint {sheath_flow}\r\n"
                mbed_serial.write(cmd.encode('utf-8'))
                response = mbed_serial.read_until(new_line).decode('utf-8').strip()
                terminal.insert(tk.END, f"[MBED] Sent: {cmd.strip()} | Received: {response}\n")
        except Exception as e:
            terminal.insert(tk.END, f"[MBED Error] {e}\n")
    else:
        terminal.insert(tk.END, "[MBED] No COM port selected.\n")

def set_daq_voltage(device_name, voltage):
    if HAS_DAQ and device_name != "None":
        try:
            with nidaqmx.Task() as task:
                task.ao_channels.add_ao_voltage_chan(f"{device_name}/ao0")
                task.write(voltage)
        except Exception as e:
            terminal.insert(tk.END, f"[DAQ Error] {e}\n")

def start_measurement():
    threading.Thread(target=measurement_loop, daemon=True).start()

def read_alicat_data(port, device='A'):
    try:
        if port != "None":
            with serial.Serial(port, 19200, timeout=1) as alicat_serial:
                alicat_serial.write(f"{device}\r".encode("utf-8"))
                response = alicat_serial.read_until(new_line).decode('utf-8').strip()
                terminal.insert(tk.END, f"[Alicat {device} Read] Response: {response}\n")
                return response
        else:
            terminal.insert(tk.END, f"[Alicat {device}] No COM port selected.\n")
    except Exception as e:
        terminal.insert(tk.END, f"[Alicat {device} Read Error] {e}\n")
        return None

def measurement_loop():
    global running, ser, ser_mbed, filename, dropfile, dropbox_sync_info
    running = True
    log_dir = 'logfiles'
    dropbox = r'C:/Users/Thermo/Dropbox/logfiles'
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(dropbox, exist_ok=True)

    def get_log_filenames():
        timestamp = datetime.datetime.now().strftime('%Y%m%d')
        return (
            os.path.join(log_dir, f'orbi_inlet_{timestamp}.csv'),
            os.path.join(dropbox, f'orbi_inlet_{timestamp}.csv')
        )

    filename, dropfile = get_log_filenames()
    dropbox_sync_info["local"] = filename
    dropbox_sync_info["dropbox"] = dropfile

    # Start a single persistent Dropbox thread
    threading.Thread(
        target=copy_to_dropbox_periodically,
        args=(dropbox_sync_info, 3600),
        daemon=True
    ).start()

    current_date = datetime.datetime.now().date()
    print(os.path.abspath(filename))

    cpc_port = cpc_box.get()
    mbed_port = mbed_box.get()
    daq_device = daq_box.get()

    ser = None
    ser_mbed = None

    if cpc_port != "None":
        try:
            ser = serial.Serial(cpc_port, 115200, timeout=1)
        except serial.SerialException as e:
            terminal.insert(tk.END, f"[CPC Error] {e}\n")
    if mbed_port != "None":
        try:
            ser_mbed = serial.Serial(mbed_port, 9600, timeout=1)
        except serial.SerialException as e:
            terminal.insert(tk.END, f"[MBED Error] {e}\n")

    file_exists = os.path.exists(filename)
    local = open(filename, 'a', newline='', encoding='utf-8')
    drop = open(dropfile, 'a', newline='', encoding='utf-8')

    writer1 = csv.writer(local)
    writer2 = csv.writer(drop)
    header = ["Local Time", "CPC data", "Size (nm)", "Voltage (V)", "Sheath Flow", "Corona HV (V)", "CPC makeup flow response", "VIA makeup flow response"]
        
    if not file_exists:
        header = ["Local Time", "CPC data", "Size (nm)", "Voltage (V)", "Sheath Flow", "Corona HV (V)", "CPC makeup flow response", "VIA makeup flow response"]
        writer1.writerow(header)
        writer2.writerow(header)

    with local, drop:

        steps = sequence_steps if use_sequence_mode and sequence_steps else [
            {
                "Step Duration (s)": switch_interval,
                "Delay Before Measure (s)": settle_delay,
                "DMA Particle Size (nm)": dp,
                "Alicat A (sLPM)": 0,
                "Alicat B (sLPM)": sheath_flow,
                "Valve (A=0/B=1)": 0 if valve_state == "A" else 1,
                "Corona (0=Off/1=On)": int(corona_toggle_var.get())
            }
            for dp in particle_sizes
        ]

        while running:
            for step in steps:
                # Rotate logs at midnight
                new_date = datetime.datetime.now().date()
                if new_date != current_date:
                    current_date = new_date
                    header = ["Local Time", "CPC data", "Size (nm)", "Voltage (V)", "Sheath Flow", "Corona HV (V)", "CPC makeup flow response", "VIA makeup flow response"]
                    local.close()
                    drop.close()
                    filename, dropfile = get_log_filenames()
                    dropbox_sync_info["local"] = filename
                    dropbox_sync_info["dropbox"] = dropfile
                    local = open(filename, 'a', newline='', encoding='utf-8')
                    drop = open(dropfile, 'a', newline='', encoding='utf-8')
                    writer1 = csv.writer(local)
                    writer2 = csv.writer(drop)
                    writer1.writerow(header)
                    writer2.writerow(header)
                    terminal.insert(tk.END, f"[Logger] Switched to new log file: {filename}\n")

                if not running:
                    break

                try:
                    duration = float(step["Step Duration (s)"])
                    delay = float(step["Delay Before Measure (s)"])
                    dp = float(step["DMA Particle Size (nm)"])
                    alicat_a = float(step["Alicat A (sLPM)"])
                    alicat_b = float(step["Alicat B (sLPM)"])
                    valve = int(step["Valve (A=0/B=1)"])
                    corona = int(step["Corona (0=Off/1=On)"])

                    # Apply settings
                    target_valve = "A" if valve == 0 else "B"
                    if valve_state != target_valve:
                        toggle_valve(valve_box.get(), valve_toggle_btn)
                    alicat_a_response = set_alicat_flow(alicat_box.get(), alicat_a, 'A')
                    alicat_b_response = set_alicat_flow(alicat_box.get(), alicat_b, 'B')
                    corona_toggle_var.set(corona == 1)
                    toggle_corona_voltage(daq_box.get(), not corona)
                    voltage = voltage_from_size(dp)
                    set_daq_voltage(daq_device, voltage)
                    terminal.insert(tk.END, f"[Step] Set DMA {dp} nm → {voltage:.2f} V\n")
                    time.sleep(delay)

                    start_time = time.time()
                    while time.time() - start_time < duration and running:
                        sh_read = "offline"
                        if ser_mbed:
                            try:
                                ser_mbed.write(b'read sh_flow\r\n')
                                sh_read = ser_mbed.read_until(new_line).decode('utf-8').strip()
                            except Exception as e:
                                terminal.insert(tk.END, f"[MBED Error] {e}\n")

                        line1 = "offline"
                        if ser:
                            try:
                                ser.write(b':MEAS:OPC\r')
                                line1 = ser.read_until(new_line).decode('utf-8').strip().replace(',', ' ').replace(':MEAS:OPC', '')
                            except:
                                pass

                        loc_dt = utc_tz.localize(datetime.datetime.utcnow()).astimezone(loc_tz)
                        corona_log_voltage = float(corona_voltage_entry.get()) if corona_toggle_var.get() else 0.0
                        alicat_a_response = read_alicat_data(alicat_box.get(), 'A')
                        alicat_b_response = read_alicat_data(alicat_box.get(), 'B')
                        row = [loc_dt.strftime(fmt), line1, dp, voltage, sh_read, corona_log_voltage, alicat_a_response, alicat_b_response]
                        terminalrow= [loc_dt.strftime(fmt), line1, dp, voltage, sh_read, corona_log_voltage]
                        writer1.writerow(row)
                        writer2.writerow(row)
                        terminal.insert(tk.END, f"{', '.join(map(str, terminalrow))}\n")
                        terminal.see(tk.END)
                        time.sleep(save_interval)
                except Exception as e:
                    terminal.insert(tk.END, f"[Step Error] {e}\n")

def stop_measurement():
    global filename, dropfile
    global running
    running = False
    if os.path.exists(filename):
        try:
            shutil.copy(filename, dropfile)
            terminal.insert(tk.END, f"[Dropbox Sync] Final copy to Dropbox complete.\n")
        except Exception as e:
            terminal.insert(tk.END, f"[Dropbox Final Copy Error] {e}\n")
    if ser_mbed and ser_mbed.is_open:
        ser_mbed.close()
    if ser and ser.is_open:
        ser.close()
    

def on_closing():
    stop_measurement()
    root.destroy()

root = tk.Tk()
style = Style(theme='darkly')
root.title("Orbi Inlet Controller")
load_config()

canvas = tk.Canvas(root)
scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = Frame(canvas)
scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

frame = scrollable_frame
top_frame = Frame(frame)
top_frame.pack(fill='x', pady=5)
left_frame = Frame(top_frame)
left_frame.pack(side='left', anchor='nw', padx=10)
right_frame = Frame(top_frame)
right_frame.pack(side='right', anchor='ne', padx=10)

Label(left_frame, text="Orbi Inlet Data Logger", font=("Helvetica", 16, "bold")).pack(pady=10)
port_frame = Frame(left_frame)
port_frame.pack(pady=10)
Label(port_frame, text="CPC COM Port:").grid(row=0, column=0, padx=5)
cpc_box = Combobox(port_frame, width=20)
cpc_box.grid(row=0, column=1, padx=5)
cpc_box.set(saved_config.get("cpc_port", "None"))
Label(port_frame, text="MBED COM Port:").grid(row=0, column=2, padx=5)
mbed_box = Combobox(port_frame, width=20)
mbed_box.grid(row=0, column=3, padx=5)
mbed_box.set(saved_config.get("mbed_port", "None"))
Label(port_frame, text="NI DAQ Device:").grid(row=1, column=0, padx=5)
daq_box = Combobox(port_frame, width=20)
daq_box.grid(row=1, column=1, padx=5)
daq_box.set(saved_config.get("daq_device", "None"))
Label(port_frame, text="Valve COM Port:").grid(row=1, column=2, padx=5)
valve_box = Combobox(port_frame, width=20)
valve_box.grid(row=1, column=3, padx=5)
valve_box.set(saved_config.get("valve_port", "None"))
Label(port_frame, text="Alicat COM Port:").grid(row=2, column=0, padx=5)
alicat_box = Combobox(port_frame, width=20)
alicat_box.grid(row=2, column=1, padx=5)
alicat_box.set(saved_config.get("alicat_port", "None"))

Label(left_frame, text="Sheath Flow Setpoint (e.g. 14.0):").pack()
sheath_entry = Entry(left_frame, width=20)
sheath_entry.pack()
sheath_entry.insert(0, str(sheath_flow))
Label(left_frame, text="Particle Sizes (nm, comma-separated):").pack()
size_entry = Entry(left_frame, width=80)
size_entry.pack()
size_entry.insert(0, ", ".join(map(str, particle_sizes)))

Label(left_frame, text="Recording Time (s):").pack()
record_time_entry = Entry(left_frame, width=20)
record_time_entry.pack()
record_time_entry.insert(0, str(save_interval))
Label(left_frame, text="Switch Interval (s):").pack()
switch_interval_entry = Entry(left_frame, width=20)
switch_interval_entry.pack()
switch_interval_entry.insert(0, str(switch_interval))
Label(left_frame, text="Settle Delay (s):").pack()
settle_delay_entry = Entry(left_frame, width=20)
settle_delay_entry.pack()
settle_delay_entry.insert(0, str(settle_delay))

valve_toggle_btn = Button(left_frame, text=f"Valve {valve_state} Open", bootstyle=(SUCCESS if valve_state == "B" else PRIMARY))
valve_toggle_btn.config(command=lambda: toggle_valve(valve_box.get(), valve_toggle_btn))
valve_toggle_btn.pack(pady=10)

Button(left_frame, text="Save Sizes & Set Sheath", command=lambda: [update_sizes(), set_sheath_flow_mbed()], bootstyle=PRIMARY).pack(pady=5)
Button(left_frame, text="Start Measurement", command=start_measurement, bootstyle=SUCCESS).pack(pady=5)
Button(left_frame, text="Stop", command=stop_measurement, bootstyle=DANGER).pack(pady=5)
Button(left_frame, text="Save Configuration", command=lambda: save_config(cpc_box.get(), mbed_box.get(), daq_box.get(), valve_box.get(), valve_state), bootstyle=SECONDARY).pack(pady=5)
Button(left_frame, text="Load Sequence CSV", command=load_sequence_file, bootstyle=INFO).pack(pady=5)
Button(left_frame, text="manual mode", command = manualmode, bootstyle = INFO).pack(pady=5)


Label(left_frame, text="Alicat A Setpoint (sccm):").pack()
alicat_a_entry = Entry(left_frame, width=20)
alicat_a_entry.pack()
Button(left_frame, text="Set Alicat A Flow", command=lambda: set_alicat_flow(alicat_box.get(), alicat_a_entry.get(), 'A'), bootstyle=INFO).pack(pady=5)

Label(left_frame, text="Alicat B Setpoint (sccm):").pack()
alicat_b_entry = Entry(left_frame, width=20)
alicat_b_entry.pack()
Button(left_frame, text="Set Alicat B Flow", command=lambda: set_alicat_flow(alicat_box.get(), alicat_b_entry.get(), 'B'), bootstyle=INFO).pack(pady=5)

Label(left_frame, text="Corona Voltage (V):").pack()
corona_voltage_entry = Entry(left_frame, width=20)
corona_voltage_entry.pack()
corona_voltage_entry.insert(0, str(saved_config.get("corona_voltage", 4500)))
corona_toggle_var = tk.BooleanVar(value=saved_config.get("corona_enabled", False))
corona_toggle_btn = Button(left_frame, text="Toggle Corona HV", command=lambda: toggle_corona_voltage(daq_box.get(), corona_toggle_var.get()), bootstyle=WARNING)
corona_toggle_btn.pack(pady=5)

terminal = tk.Text(right_frame, height=30, width=100)
terminal.pack(pady=5)
terminal.insert(tk.END, "[Terminal Ready]")

def set_alicat_flow(port, flow, device):
    """
    Set flow for Alicat MFC with unit ID (A, B) on the same shared COM port (RS-485 daisy chain).
    """
    try:
        flow = float(flow)
        command = f"{device}s{flow:.3f}\r"  # e.g., As1.000
        if port != "None":
            with serial.Serial(port, 19200, timeout=1) as alicat_serial:
                alicat_serial.write(command.encode("utf-8"))
                response = alicat_serial.read_until(new_line).decode('utf-8').strip()
                terminal.insert(tk.END, f"[Alicat {device}] Set to {flow:.3f} sLPM | Response: {response}\n")
                return response
        else:
            terminal.insert(tk.END, f"[Alicat {device}] No COM port selected.\n")
    except Exception as e:
        terminal.insert(tk.END, f"[Alicat {device} Error] {e}\n")


threading.Thread(target=update_com_ports_loop, daemon=True).start()
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
