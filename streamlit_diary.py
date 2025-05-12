import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("📊 Criticality Tracker")

plot_path = "diaries/plot.csv"
crit_levels = [str(i) for i in range(11)]

if not os.path.exists(plot_path):
    st.warning("No data yet in plot.csv.")
    st.stop()

df = pd.read_csv(plot_path, index_col=0).fillna(0)

# Ensure all columns 0–10 exist
for col in crit_levels:
    if col not in df.columns:
        df[col] = 0

df = df[crit_levels].astype(int)
df = df[df.sum(axis=1) > 0]  # Remove empty days

# Bar chart
fig, ax = plt.subplots(figsize=(max(10, len(df)*0.5), 5))
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
