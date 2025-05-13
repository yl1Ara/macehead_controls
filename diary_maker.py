import pandas as pd
import time
import datetime
import pytz
import tkinter as tk
import os
import ttkbootstrap as ttk
from ttkbootstrap import Style
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import Combobox, Button, Label, Entry, Checkbutton
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

dropbox = r'C:/Users/Thermo/Dropbox/logfiles'

canvas = None
root = tk.Tk()
root.columnconfigure(0, weight=1)
root.rowconfigure(7, weight=1)
root.title("Diary Maker")
style = Style(theme='darkly')

# Widgets
note_label = Label(root, text="Enter your note:")
note_label.grid(row=2, column=0, padx=10, pady=10)

Note = Entry(root, width=50)
Note.grid(row=3, column=0, padx=10, pady=10)

time_label = Label(root, text="Time:")
time_label.grid(row=4, column=0, padx=10, pady=10)

real_time = tk.BooleanVar()
real_time.set(True)

real_time_checkbutton = Checkbutton(root, text="Real Time", bootstyle=INFO, variable=real_time)
real_time_checkbutton.grid(row=4, column=1, padx=10, pady=10)

time_entry = Entry(root, width=20)
time_entry.grid(row=5, column=0, padx=10, pady=10)
timestamp = datetime.datetime.now(pytz.timezone('Etc/GMT-0')).strftime("%H:%M:%S %d-%m-%Y")
time_entry.insert(0, timestamp)

machine_label = Label(root, text="machine").grid(row=0, column=0, padx=5)
machine = Combobox(root, width=20)
machine.grid(row=1, column=0, padx=5)
machine.insert(0, 'Maintenance')

machine['values'] = ['ORBI','Inlet','CPC','DMA','Maintenance','Other']


Button(root, text="Save Note", command=lambda: save_note()).grid(row=6, column=0, padx=10, pady=10)



def update_time():
    if not root.winfo_exists():
        return  

    if real_time.get():
        current_time = datetime.datetime.now(pytz.timezone('Etc/GMT-0')).strftime("%Y-%m-%d %H:%M:%S")
        time_entry.delete(0, tk.END)
        time_entry.insert(0, current_time)

    root.after(1000, update_time)


def save_note():
    note = Note.get().strip()
    if not note:
        print("No note to save.")
        return

    full_timestamp = time_entry.get()

    filename = f"diaries/diary.csv"

    dropbox = r'C:/Users/Thermo/Dropbox/logfiles/diary.csv'

    os.makedirs("diaries", exist_ok=True)


    if os.path.exists(filename):
        df = pd.read_csv(filename)
    else:
        df = pd.DataFrame(columns=["Time", "Note"])

    

    note = f'[{machine.get()}] {note}'

    df.loc[len(df)] = [full_timestamp, note]

    df = df.sort_values(by="Time")

    df.to_csv(filename, index=False)
    print(f"Note saved to {filename}")

    if os.path.exists(dropbox):
        df_dropbox = pd.read_csv(dropbox)
        df = pd.concat([df, df_dropbox], ignore_index=True)
    else:
        df.to_csv(dropbox, index=False)
    df = df.sort_values(by="Time")
    df.to_csv(dropbox, index=False)
    print(f"Note saved to {dropbox}")




    

    


heatmap_frame = ttk.Frame(root)
heatmap_frame.grid(row=7, column=0, columnspan=10, padx=10, pady=10)

heatmap_frame.columnconfigure(0, weight=1)
heatmap_frame.rowconfigure(0, weight=1)


update_time()
root.mainloop()
