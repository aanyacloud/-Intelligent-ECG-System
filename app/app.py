import sys
import os

# Make project root visible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time

from backend.load_data import load_mitbih
from backend.adaptive_filter import adaptive_filter
from backend.sqi import compute_sqi, compute_confidence
from backend.hr_analysis import compute_rr, compute_hr, compute_hrv
from backend.realtime import stream_signal

from scipy.signal import find_peaks, welch

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="ECG System", layout="wide")
st.title("🫀 Intelligent ECG System")

# ---------------- R-PEAK DETECTION ----------------
def detect_r_peaks(signal, fs):
    norm = (signal - np.mean(signal)) / (np.std(signal) + 1e-8)
    enhanced = norm ** 2

    window = int(0.12 * fs)
    enhanced = np.convolve(enhanced, np.ones(window)/window, mode='same')

    threshold = np.mean(enhanced) + 0.5 * np.std(enhanced)
    distance = int(0.4 * fs)

    rough_peaks, _ = find_peaks(enhanced, height=threshold, distance=distance)

    refined_peaks = []
    search_window = int(0.08 * fs)

    for p in rough_peaks:
        start = max(0, p - search_window)
        end = min(len(signal), p + search_window)
        true_peak = np.argmax(signal[start:end]) + start
        refined_peaks.append(true_peak)

    return np.array(refined_peaks)

# ---------------- SNR FUNCTION ----------------
def compute_snr_local(signal, fs):
    f, Pxx = welch(signal, fs)
    signal_power = np.sum(Pxx[(f >= 0.5) & (f <= 40)])
    noise_power = np.sum(Pxx) - signal_power
    return 10 * np.log10(signal_power / (noise_power + 1e-8))

# ---------------- INPUT ----------------
mode = st.selectbox("Input Mode", ["MIT-BIH Sample", "Upload CSV"])

if mode == "MIT-BIH Sample":
    record = st.selectbox("Select Record", ["100", "101", "102"])
    signal, fs = load_mitbih(record)

else:
    file = st.file_uploader("Upload ECG CSV")
    if file:
        signal = np.loadtxt(file)
        fs = st.number_input("Sampling Rate", value=360)

# ---------------- PROCESS ----------------
if 'signal' in locals():

    realtime = st.checkbox("Enable Real-Time")

    # ================= NORMAL MODE =================
    if not realtime:

        # -------- SIGNAL PROCESSING --------
        filtered, steps = adaptive_filter(signal, fs)
        sqi, snr = compute_sqi(filtered, fs)
        conf = compute_confidence(sqi)

        peaks = detect_r_peaks(filtered, fs)

        rr = compute_rr(peaks, fs)
        hr = compute_hr(rr)
        hr = hr[(hr > 40) & (hr < 180)]

        hrv = compute_hrv(rr)

        # -------- METRICS --------
        st.subheader("📊 Metrics")
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("SNR (dB)", f"{snr:.2f}")
        col2.metric("SQI", f"{sqi:.2f}")
        col3.metric("Confidence", f"{conf:.1f}%")
        col4.metric("Avg HR", f"{np.mean(hr):.1f} BPM" if len(hr) else "0")

        st.write("HRV:")
        st.json(hrv)

        # ================= NEW SECTION =================
        # -------- QUANTITATIVE PERFORMANCE --------
        st.subheader("📊 Quantitative Performance")

        snr_before = compute_snr_local(signal, fs)
        snr_after = compute_snr_local(filtered, fs)
        improvement = snr_after - snr_before

        col1, col2, col3 = st.columns(3)
        col1.metric("SNR Before", f"{snr_before:.2f} dB")
        col2.metric("SNR After", f"{snr_after:.2f} dB")
        col3.metric("Improvement", f"+{improvement:.2f} dB")

        st.success(
            f"Filtering improved SNR by {improvement:.2f} dB, enhancing ECG signal quality."
        )

        # -------- ECG VISUALIZATION --------
        st.subheader("🔍 ECG Visualization")

        window_size = min(2000, len(filtered) - 1)
        start = st.slider("Select Signal Window", 0, len(filtered) - window_size, 0)

        segment = filtered[start:start + window_size]
        visible_peaks = peaks[(peaks >= start) & (peaks < start + window_size)]

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(segment, label="ECG Signal", linewidth=1)

        ax.plot(
            visible_peaks - start,
            filtered[visible_peaks],
            "ro",
            label="R-peaks",
            markersize=5
        )

        ax.set_title("Filtered ECG (Zoomed View)")
        ax.set_xlabel("Samples")
        ax.set_ylabel("Amplitude")
        ax.legend()

        st.pyplot(fig)

        # -------- HEART RATE TREND --------
        st.subheader("📈 Heart Rate Trend")

        if len(hr) > 5:
            hr_smooth = np.convolve(hr, np.ones(5)/5, mode='valid')

            fig_hr, ax_hr = plt.subplots(figsize=(8, 3))
            ax_hr.plot(hr_smooth)
            ax_hr.set_title("Heart Rate Over Time")
            ax_hr.set_ylabel("BPM")
            ax_hr.set_xlabel("Beat Index")

            st.pyplot(fig_hr)

        # -------- RR INTERVAL --------
        st.subheader("⏱️ RR Interval Variation")

        if len(rr) > 1:
            fig_rr, ax_rr = plt.subplots(figsize=(8, 3))
            ax_rr.plot(rr)
            ax_rr.set_title("RR Interval Variation")
            ax_rr.set_ylabel("Seconds")
            ax_rr.set_xlabel("Beat Index")

            st.pyplot(fig_rr)

        # -------- PROCESSING INFO --------
        st.subheader("⚙️ Processing Info")
        for step in steps:
            st.write(f"✔ {step}")

    # ================= REAL-TIME MODE =================
    else:
        window = int(2 * fs)
        step = int(0.5 * fs)

        chart = st.empty()
        hr_history = []

        for chunk in stream_signal(signal, window, step):

            filtered, _ = adaptive_filter(chunk, fs)
            sqi, snr = compute_sqi(filtered, fs)
            conf = compute_confidence(sqi)

            peaks = detect_r_peaks(filtered, fs)

            if len(peaks) > 1:
                rr = compute_rr(peaks, fs)
                hr = compute_hr(rr)
                hr = hr[(hr > 40) & (hr < 180)]

                if len(hr) > 0:
                    avg_hr = np.mean(hr)
                    hr_history.append(avg_hr)
                else:
                    avg_hr = 0
            else:
                avg_hr = 0

            fig, ax = plt.subplots(figsize=(8, 3))
            ax.plot(filtered, linewidth=1)
            ax.plot(peaks, filtered[peaks], "ro", markersize=4)

            ax.set_title(f"HR: {avg_hr:.1f} BPM | Conf: {conf:.1f}%")
            chart.pyplot(fig)

            time.sleep(0.2)

        if len(hr_history) > 5:
            st.subheader("📈 Real-Time HR Trend")

            fig, ax = plt.subplots(figsize=(8, 3))
            ax.plot(hr_history)
            ax.set_title("Real-Time Heart Rate")
            ax.set_ylabel("BPM")

            st.pyplot(fig)