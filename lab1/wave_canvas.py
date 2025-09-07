import tkinter as tk
import numpy as np

# -------- Mini osciloscopio (Canvas polyline) --------
class WaveCanvas(tk.Canvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, height=100, bg="#f8fafc", highlightthickness=0, bd=0, **kwargs)
        self.line = None
        self.margin = 8
        self.last_pts = []

    def draw_wave(self, samples: np.ndarray | None):
        self.delete("all")
        if samples is None or len(samples) == 0:
            return
        W = self.winfo_width()
        H = self.winfo_height()
        if W <= 0 or H <= 0:
            return
        # normalizar a [-1,1] y mapear a canvas
        s = samples.astype(np.float32)
        if np.max(np.abs(s)) > 0:
            s = s / np.max(np.abs(s))
        else:
            s = s.copy()
        N = len(s)
        xs = np.linspace(self.margin, W - self.margin, N)
        ys = (H/2) - (H/2 - 6) * s  # margen superior
        pts = []
        for x, y in zip(xs, ys):
            pts.extend([x, y])
        self.create_line(*pts, fill="#2563eb", width=1.5)