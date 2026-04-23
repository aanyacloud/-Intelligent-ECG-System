def stream_signal(signal, window, step):
    for i in range(0, len(signal) - window, step):
        yield signal[i:i+window]