import threading
import queue
import sounddevice as sd
import numpy as np
# ----------- Output player with level + scope -----------
class OutputPlayer:
    def __init__(self):
        self.stream = None
        self.buf = None
        self.fs = 44100
        self.pos = 0  # sample index
        self.lock = threading.Lock()
        self.level_q = queue.Queue(maxsize=8)
        self.scope_q = queue.Queue(maxsize=8)
        self._paused = True
        self.blocksize = 1024

    def load(self, x: np.ndarray, fs: int):
        with self.lock:
            self.buf = x.astype(np.float32)
            self.fs = int(fs)
            self.pos = 0
            self._paused = True

    def _callback(self, outdata, frames, time_info, status):
        if status:
            pass
        with self.lock:
            if self.buf is None or self._paused:
                outdata[:] = 0
                return
            end = min(self.pos + frames, len(self.buf))
            chunk = self.buf[self.pos:end]
            out = np.zeros(frames, dtype=np.float32)
            out[:len(chunk)] = chunk
            outdata[:, 0] = out
            self.pos = end
            # nivel y scope
            if len(chunk) > 0:
                rms = float(np.sqrt(np.mean(chunk ** 2)))
                try:
                    self.level_q.put_nowait(rms)
                except queue.Full:
                    pass
                # enviar pequeña ventana para dibujar
                scope_win = chunk[-min(2000, len(chunk)):]  # ~45ms a 44.1k
                try:
                    self.scope_q.put_nowait(scope_win.copy())
                except queue.Full:
                    pass

    def start(self):
        if self.stream is None:
            self.stream = sd.OutputStream(
                samplerate=self.fs,
                channels=1,
                dtype="float32",
                blocksize=self.blocksize,
                callback=self._callback,
            )
            self.stream.start()

    def play(self):
        self.start()
        with self.lock:
            self._paused = False

    def pause(self):
        with self.lock:
            self._paused = True

    def stop(self):
        with self.lock:
            self._paused = True
            self.pos = 0

    def is_playing(self):
        with self.lock:
            return (self.buf is not None) and (not self._paused) and (self.pos < len(self.buf))

    def progress(self):
        with self.lock:
            if self.buf is None:
                return 0.0
            return self.pos / max(1, len(self.buf))

    def seek_frac(self, frac):
        with self.lock:
            if self.buf is None:
                return
            frac = float(np.clip(frac, 0.0, 1.0))
            self.pos = int(frac * len(self.buf))
