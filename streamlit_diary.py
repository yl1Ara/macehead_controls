import streamlit as st
import pandas as pd
import os
import datetime
import matplotlib.pyplot as plt

# --- Setup ---
st.set_page_config(layout="wide")
st.title("📓 Diary Logger with Criticality Plot")

# Create directory
os.makedirs("diaries", exist_ok=True)
plot_path = "diaries/plot.csv"
crit_levels = [str(i) for i in range(11)]

# --- Note Input ---
note = st.text_input("Enter your note")
criticality = st.slider("Criticality level", 0, 10, 1)
now = datetime.datetime.utcnow()
time_str = now.strftime("%H:%M:%S")
date_str = now.strftime("%d-%m-%Y")

# --- Save Note ---
if st.button("Save Note"):
    # Save daily diary
    diary_file = f"diaries/diary_{date_str}.csv"
    if os.path.exists(diary_file):
        df = pd.read_csv(diary_file)
    else:
        df = pd.DataFrame(columns=["Time", "Note", "Criticality"])

    df.loc[len(df)] = [time_str, note, criticality]
    df.to_csv(diary_file, index=False)

    # Update plot.csv
    if os.path.exists(plot_path):
        pdf = pd.read_csv(plot_path, index_col=0)
    else:
        pdf = pd.DataFrame(columns=crit_levels)

    if date_str not in pdf.index:
        pdf.loc[date_str] = [0]*11

    for col in crit_levels:
        if col not in pdf.columns:
            pdf[col] = 0

    pdf.loc[date_str, str(criticality)] += 1
    pdf = pdf.sort_index()
    pdf.to_csv(plot_path)

    st.success(f"Saved note with criticality {criticality} for {date_str} at {time_str}!")

# --- Plot Bar Chart ---
st.subheader("📊 Daily Criticality Stacked Bar Chart")

if os.path.exists(plot_path):
    df = pd.read_csv(plot_path, index_col=0).fillna(0)
    for col in crit_levels:
        if col not in df.columns:
            df[col] = 0
    df = df[crit_levels].astype(int)
    df = df[df.sum(axis=1) > 0]

    fig, ax = plt.subplots(figsize=(max(10, len(df) * 0.5), 5))
    bottom = [0] * len(df)
    colors = [
        "#b0b0b0", "#9090a0", "#7080b0", "#5080c0", "#3080d0",
        "#1080e0", "#e070b0", "#e05080", "#e03060", "#e01030", "#d00000"
    ]
    for i, level in enumerate(crit_levels):
        ax.bar(df.index, df[level], bottom=bottom, label=f"Level {level}", color=colors[i])
        bottom = [b + h for b, h in zip(bottom, df[level])]
    ax.set_title("Daily Criticality Distribution")
    ax.set_xlabel("Date")
    ax.set_ylabel("Count (log)")
    ax.set_yscale("log")
    ax.legend(title="Criticality", bbox_to_anchor=(1.02, 1), loc='upper left')
    ax.tick_params(axis='x', rotation=45)
    fig.tight_layout()
    st.pyplot(fig)
else:
    st.info("No entries yet to plot.")
