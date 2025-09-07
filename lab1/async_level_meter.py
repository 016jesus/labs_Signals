import queue
import platform
import sounddevice as sd
import numpy as np

# ------------- Async input meter (for capture) -------------
class AsyncLevelMeter:
    def __init__(self):
        self.stream = None
        self.q = queue.Queue(maxsize=8)
        self.rms_ema = 0.0
        self.alpha = 0.2
        self.current_params = (None, None, False)

    def start(self, device_index: int | None, fs: int, raw: bool):
        if self.current_params == (device_index, fs, raw) and self.stream is not None:
            return
        self.stop()
        if device_index is None:
            return
        try:
            extra = None
            if raw and platform.system() == "Windows":
                try:
                    extra = sd.WasapiSettings(exclusive=True)
                except Exception:
                    extra = None
            self.stream = sd.InputStream(
                samplerate=fs,
                channels=1,
                device=device_index,
                dtype="float32",
                blocksize=0,
                latency="low",
                extra_settings=extra,
                callback=self._callback,
            )
            self.stream.start()
            self.current_params = (device_index, fs, raw)
        except Exception:
            self.stop()

    def stop(self):
        try:
            if self.stream is not None:
                self.stream.stop()
                self.stream.close()
        except Exception:
            pass
        self.stream = None
        self.current_params = (None, None, False)
        while not self.q.empty():
            try:
                self.q.get_nowait()
            except queue.Empty:
                break

    def _callback(self, indata, frames, time_info, status):
        if status:
            pass
        rms = float(np.sqrt(np.mean(indata[:, 0] ** 2))) if frames > 0 else 0.0
        self.rms_ema = 0.2 * rms + 0.8 * self.rms_ema
        try:
            self.q.put_nowait(self.rms_ema)
        except queue.Full:
            pass

