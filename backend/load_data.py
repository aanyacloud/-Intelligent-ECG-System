import wfdb

def load_mitbih(record_name="100"):
    record = wfdb.rdrecord(f"data/{record_name}")
    signal = record.p_signal[:, 0]
    fs = record.fs
    return signal, fs