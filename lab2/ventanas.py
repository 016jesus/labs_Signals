import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from graficas import stem_coloreado


class PanelGraficas(ttk.Frame):
    def __init__(self, master, paleta: dict):
        super().__init__(master)
        self.p = paleta  
        # Notebook (pestañas)
        self.nb = ttk.Notebook(self, bootstyle=PRIMARY)
        self.nb.pack(fill="both", expand=True, padx=(2, 0), pady=(2, 2))

        # --------- Pestaña 1: x y h ---------
        self.tab_xyh = ttk.Frame(self.nb)
        self.nb.add(self.tab_xyh, text="x y h")

        self.fig_xyh = Figure(figsize=(6, 5), dpi=100)
        self.ax_x = self.fig_xyh.add_subplot(211)
        self.ax_h = self.fig_xyh.add_subplot(212)
        self._estilizar_axes(self.ax_x)
        self._estilizar_axes(self.ax_h)
        self.fig_xyh.tight_layout(pad=1.2)

        self.canvas_xyh = FigureCanvasTkAgg(self.fig_xyh, master=self.tab_xyh)
        self.canvas_xyh.draw()
        self.canvas_xyh.get_tk_widget().pack(fill="both", expand=True)

        self.toolbar_xyh = NavigationToolbar2Tk(self.canvas_xyh, self.tab_xyh)
        self.toolbar_xyh.update()
        self.toolbar_xyh.pack(side="bottom", fill="x")

        # --------- Pestaña 2: salidas ---------
        self.tab_salidas = ttk.Frame(self.nb)
        self.nb.add(self.tab_salidas, text="salidas")

        self.fig_sal = Figure(figsize=(6, 5), dpi=100)
        self.ax_teo = self.fig_sal.add_subplot(211)
        self.ax_conv = self.fig_sal.add_subplot(212)
        self._estilizar_axes(self.ax_teo)
        self._estilizar_axes(self.ax_conv)
        self.fig_sal.tight_layout(pad=1.2)

        self.canvas_sal = FigureCanvasTkAgg(self.fig_sal, master=self.tab_salidas)
        self.canvas_sal.draw()
        self.canvas_sal.get_tk_widget().pack(fill="both", expand=True)

        self.toolbar_sal = NavigationToolbar2Tk(self.canvas_sal, self.tab_salidas)
        self.toolbar_sal.update()
        self.toolbar_sal.pack(side="bottom", fill="x")

    # ---------- Helpers de estilo ----------
    def _estilizar_axes(self, ax):
        ax.set_facecolor(self.p["surface"])
        for spine in ax.spines.values():
            spine.set_color(self.p["grid"])

    # ---------- Redibujado de Pestaña 'x y h' ----------
    def actualizar_xyh(self, n, x, nh, h):
        self.ax_x.clear();  self._estilizar_axes(self.ax_x)
        self.ax_h.clear();  self._estilizar_axes(self.ax_h)

        # x(n)
        stem_coloreado(
            self.ax_x, n, x,
            color=self.p["primary"], basecolor=self.p["grid"], marker="o", lw=1.8
        )
        self.ax_x.set_title("Entrada x(n) = a e^{bn} u(n)")
        self.ax_x.set_xlabel("n")
        self.ax_x.set_ylabel("x(n)")
        self.ax_x.grid(True)

        # h(n)
        stem_coloreado(
            self.ax_h, nh, h,
            color=self.p["success"], basecolor=self.p["grid"], marker="o", lw=1.8
        )
        self.ax_h.set_title("Respuesta al impulso h(n)")
        self.ax_h.set_xlabel("n")
        self.ax_h.set_ylabel("h(n)")
        self.ax_h.grid(True)

        self.fig_xyh.tight_layout(pad=1.2)
        self.canvas_xyh.draw()

    # ---------- Redibujado de Pestaña 'salidas' ----------
    def actualizar_salidas(self, n, y_conv, y_teo):
        self.ax_teo.clear();  self._estilizar_axes(self.ax_teo)
        self.ax_conv.clear(); self._estilizar_axes(self.ax_conv)

        # y_teórica (línea con color de acento)
        self.ax_teo.plot(n, y_teo, linestyle="--", linewidth=2.2, color=self.p["accent"])
        self.ax_teo.set_title("Salida teórica  y_teo(n) = c e^{dn} cosh(kn) u(n)")
        self.ax_teo.set_xlabel("n")
        self.ax_teo.set_ylabel("y_teo(n)")
        self.ax_teo.grid(True)

        # y por convolución (stem con color primario)
        stem_coloreado(
            self.ax_conv, n, y_conv,
            color=self.p["primary"], basecolor=self.p["grid"], marker="o", lw=1.8
        )
        self.ax_conv.set_title("Salida por convolución  y_conv(n) = (h*x)(n)")
        self.ax_conv.set_xlabel("n")
        self.ax_conv.set_ylabel("y_conv(n)")
        self.ax_conv.grid(True)

        # mismo eje x
        if len(n) > 0:
            self.ax_teo.set_xlim(0, n[-1])
            self.ax_conv.set_xlim(0, n[-1])

        self.fig_sal.tight_layout(pad=1.2)
        self.canvas_sal.draw()
