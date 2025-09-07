import tkinter as tk
import numpy as np
# ------------------ VU LED ------------------
class VuLedCanvas(tk.Canvas):
    def __init__(self, master, bars=24, **kwargs):
        super().__init__(master, height=22, **kwargs)
        self.bars = bars
        self.margin = 6
        self.spacing = 4
        self.peak = 0.0
        self.peak_decay = 0.015
        self.rects = []
        self.bind("<Configure>", lambda e: self._draw_static())

    def _color_for(self, frac):
        if frac < 0.6:
            return "#48C774"
        elif frac < 0.85:
            return "#FFDD57"
        else:
            return "#F14668"

    def _draw_static(self):
        self.delete("all")
        W = self.winfo_width()
        H = self.winfo_height()
        if W <= 0 or H <= 0:
            return
        usable_w = W - 2 * self.margin
        bar_w = max(2, int((usable_w - (self.bars - 1) * self.spacing) / self.bars))
        x = self.margin
        self.rects = []
        for i in range(self.bars):
            r = self.create_rectangle(x, 4, x + bar_w, H - 4, outline="", fill="#e5e7eb", tags=("bar",))
            self.rects.append(r)
            x += bar_w + self.spacing
        self.peak_line = self.create_line(0, 2, 0, H - 2, fill="#111827", width=2, state="hidden", tags=("peak",))

    def update_level(self, value_01: float):
        val = float(np.clip(value_01, 0.0, 1.0))
        self.peak = max(self.peak, val)
        self.peak = max(0.0, self.peak - self.peak_decay)
        lit = int(round(val * self.bars))
        for i, r in enumerate(self.rects):
            if i < lit:
                frac = (i + 1) / self.bars
                self.itemconfigure(r, fill=self._color_for(frac))
            else:
                self.itemconfigure(r, fill="#e5e7eb")
        if self.rects:
            left = self.coords(self.rects[0])[0]
            right = self.coords(self.rects[-1])[2]
            x_peak = left + (right - left) * self.peak
            self.coords(self.peak_line, x_peak, 2, x_peak, self.winfo_height() - 2)
            self.itemconfigure(self.peak_line, state="normal")
