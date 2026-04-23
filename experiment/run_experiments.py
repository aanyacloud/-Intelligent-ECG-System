import sys
import os

# Fix import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from backend.load_data import load_mitbih
from backend.adaptive_filter import adaptive_filter
from backend.sqi import compute_sqi

# -------- DATA PATH --------
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

# Get all records
records = [f.split(".")[0] for f in os.listdir(DATA_PATH) if f.endswith(".dat")]
records = sorted(list(set(records)))

results = []

# -------- PROCESS ALL RECORDS --------
for record in records:
    try:
        print(f"Processing {record}...")

        signal, fs = load_mitbih(record)

        # Before filtering
        _, snr_before = compute_sqi(signal, fs)

        # After filtering
        filtered, _ = adaptive_filter(signal, fs)
        _, snr_after = compute_sqi(filtered, fs)

        improvement = snr_after - snr_before

        results.append({
            "record": record,
            "snr_before": snr_before,
            "snr_after": snr_after,
            "snr_improvement": improvement
        })

    except Exception as e:
        print(f"Skipping {record}: {e}")

# -------- SAVE CSV --------
df = pd.DataFrame(results)

os.makedirs("results", exist_ok=True)
df.to_csv("results/results.csv", index=False)

# -------- SUMMARY --------
summary = {
    "avg_snr_before": df["snr_before"].mean(),
    "avg_snr_after": df["snr_after"].mean(),
    "avg_improvement": df["snr_improvement"].mean(),
    "std_improvement": df["snr_improvement"].std()
}

pd.DataFrame([summary]).to_csv("results/summary.csv", index=False)

print("\n✅ Experiment complete!")
print(df.head())
print("\n📊 Summary:")
print(summary)

# -------- PLOTS --------
PLOT_PATH = "results/plots"
os.makedirs(PLOT_PATH, exist_ok=True)

# 1. SNR BAR CHART
plt.figure()
plt.bar(
    ["Before", "After"],
    [df["snr_before"].mean(), df["snr_after"].mean()]
)
plt.title("Average SNR Improvement")
plt.ylabel("SNR (dB)")
plt.savefig(f"{PLOT_PATH}/snr_bar.png", dpi=300)
plt.close()

# 2. SNR IMPROVEMENT BOXPLOT
plt.figure()
plt.boxplot(df["snr_improvement"])
plt.title("SNR Improvement Distribution")
plt.ylabel("ΔSNR (dB)")
plt.savefig(f"{PLOT_PATH}/snr_boxplot.png", dpi=300)
plt.close()

# 3. LINE PLOT PER RECORD
plt.figure()
plt.plot(df["record"], df["snr_before"], label="Before")
plt.plot(df["record"], df["snr_after"], label="After")
plt.legend()
plt.title("SNR per Record")
plt.xlabel("Record")
plt.ylabel("SNR (dB)")
plt.xticks(rotation=90)
plt.tight_layout()
plt.savefig(f"{PLOT_PATH}/snr_line.png", dpi=300)
plt.close()

print("\n📊 Plots saved in results/plots/")

