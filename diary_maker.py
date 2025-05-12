import pandas as pd
import time
import datetime
import pytz
import tkinter as tk
import os
import ttkbootstrap as ttk
from ttkbootstrap import Style
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import Button, Label, Entry, Checkbutton
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

canvas = None
root = tk.Tk()
root.columnconfigure(0, weight=1)
root.rowconfigure(7, weight=1)
root.title("Diary Maker")
style = Style(theme='darkly')

# Widgets
note_label = Label(root, text="Enter your note:")
note_label.grid(row=0, column=0, padx=10, pady=10)

Note = Entry(root, width=50)
Note.grid(row=1, column=0, padx=10, pady=10)

time_label = Label(root, text="Time:")
time_label.grid(row=2, column=0, padx=10, pady=10)

real_time = tk.BooleanVar()
real_time.set(True)

real_time_checkbutton = Checkbutton(root, text="Real Time", bootstyle=INFO, variable=real_time)
real_time_checkbutton.grid(row=2, column=1, padx=10, pady=10)

time_entry = Entry(root, width=20)
time_entry.grid(row=3, column=0, padx=10, pady=10)
timestamp = datetime.datetime.now(pytz.timezone('Etc/GMT-0')).strftime("%H:%M:%S %d-%m-%Y")
time_entry.insert(0, timestamp)

criticality_label = Label(root, text="Criticality:")
criticality_label.grid(row=4, column=0, padx=10, pady=10)
criticality = Entry(root, width=20)
criticality.grid(row=5, column=0, padx=10, pady=10)
criticality.insert(0, 1)


Button(root, text="Save Note", command=lambda: save_note()).grid(row=6, column=0, padx=10, pady=10)



def update_time():
    if not root.winfo_exists():
        return  

    if real_time.get():
        current_time = datetime.datetime.now(pytz.timezone('Etc/GMT-0')).strftime("%H:%M:%S %d-%m-%Y")
        time_entry.delete(0, tk.END)
        time_entry.insert(0, current_time)

    root.after(1000, update_time)


def save_note():
    note = Note.get().strip()
    if not note:
        print("No note to save.")
        return

    full_timestamp = time_entry.get()
    try:
        time_str, date_str = full_timestamp.split(' ')
    except ValueError:
        print("Invalid timestamp format.")
        return

    filename = f"diaries/diary_{date_str}.csv"

    os.makedirs("diaries", exist_ok=True)

    if os.path.exists(filename):
        df = pd.read_csv(filename)
    else:
        df = pd.DataFrame(columns=["Time", "Note", "Criticality"])

    df.loc[len(df)] = [time_str, note, criticality.get()]

    df = df.sort_values(by="Time")

    df.to_csv(filename, index=False)
    print(f"Note saved to {filename}")

    plot_path = "diaries/plot.csv"
    crit_value = int(criticality.get())

    if not 0 <= crit_value <= 10:
        print("Criticality must be between 0 and 10.")
        return

    crit_cols = [str(i) for i in range(11)]

    if os.path.exists(plot_path):
        pdf = pd.read_csv(plot_path, index_col=0)
    else:
        pdf = pd.DataFrame(columns=crit_cols)

    if date_str not in pdf.index:
        pdf.loc[date_str] = [0] * 11

    for col in crit_cols:
        if col not in pdf.columns:
            pdf[col] = 0

    pdf.loc[date_str, str(crit_value)] += 1
    pdf = pdf.sort_index()
    pdf.to_csv(plot_path)

    plot_bar_chart(heatmap_frame)

def plot_bar_chart(frame):
    global canvas

    if canvas:
        canvas.get_tk_widget().destroy()
        canvas = None

    plot_path = "diaries/plot.csv"
    if not os.path.exists(plot_path):
        print("plot.csv not found.")
        return

    df = pd.read_csv(plot_path, index_col=0).fillna(0)
    crit_levels = [str(i) for i in range(11)]

    for level in crit_levels:
        if level not in df.columns:
            df[level] = 0

    df = df[crit_levels].astype(int)

    df = df[df.sum(axis=1) > 0]

    fig_width = max(8, len(df) * 0.5) 
    fig, ax = plt.subplots(figsize=(fig_width, 4))

    bottom = [0] * len(df)
    colors = [
        "#b0b0b0", "#9090a0", "#7080b0", "#5080c0", "#3080d0",
        "#1080e0", "#e070b0", "#e05080", "#e03060", "#e01030", "#d00000"
    ]

    for i, level in enumerate(crit_levels):
        heights = df[level].values
        ax.bar(df.index, heights, bottom=bottom, label=f"Level {level}", color=colors[i])
        bottom = [b + h for b, h in zip(bottom, heights)]

    ax.set_title("Daily Criticality Distribution")
    ax.set_xlabel("Date")
    ax.set_ylabel("Count (log)")
    ax.set_yscale("log")
    ax.legend(title="Criticality", bbox_to_anchor=(1.02, 1), loc='upper left')
    ax.tick_params(axis='x', rotation=45)
    fig.tight_layout()

    outer_canvas = tk.Canvas(frame)
    outer_canvas.grid(row=0, column=0, sticky="nsew")

    h_scroll = tk.Scrollbar(frame, orient="horizontal", command=outer_canvas.xview)
    h_scroll.grid(row=1, column=0, sticky="ew")

    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    h_scroll = tk.Scrollbar(frame, orient="horizontal", command=outer_canvas.xview)
    h_scroll.grid(row=1, column=0, sticky="ew")

    outer_canvas.configure(xscrollcommand=h_scroll.set)

    canvas = FigureCanvasTkAgg(fig, master=outer_canvas)
    plot_widget = canvas.get_tk_widget()
    canvas.draw()

    plot_id = outer_canvas.create_window((0, 0), window=plot_widget, anchor="nw")
    plot_widget.update_idletasks()
    outer_canvas.configure(scrollregion=outer_canvas.bbox("all"))

    outer_canvas.config(width=800)

    fig.savefig("diaries/criticality_plot.png", bbox_inches="tight")
    




heatmap_frame = ttk.Frame(root)
heatmap_frame.grid(row=7, column=0, columnspan=10, padx=10, pady=10)

heatmap_frame.columnconfigure(0, weight=1)
heatmap_frame.rowconfigure(0, weight=1)

plot_bar_chart(heatmap_frame)

update_time()
root.mainloop()
