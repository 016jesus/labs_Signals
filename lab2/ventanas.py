import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from graficas import stem_seguro

class VentanaXH(ttk.Toplevel):
    def __init__(self, master, n, x, nh, h):
        super().__init__(master)
        self.title("Señales x(n) y h(n)")
        self.geometry("1000x750")

        fig = Figure(figsize=(10, 8), dpi=100)
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212)

        stem_seguro(ax1, n, x)
        ax1.set_title("Entrada x(n) = a e^{bn} u(n)")
        ax1.grid(True)

        stem_seguro(ax2, nh, h)
        ax2.set_title("Respuesta al impulso h(n)")
        ax2.grid(True)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        toolbar = NavigationToolbar2Tk(canvas, self)
        toolbar.update()
        toolbar.pack(side="bottom", fill="x")


class VentanaSalida(ttk.Toplevel):
    def __init__(self, master, n, y_conv, y_teo):
        super().__init__(master)
        self.title("Salidas del sistema")
        self.geometry("1000x750")

        fig = Figure(figsize=(10, 8), dpi=100)
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212)

        ax1.plot(n, y_teo, linestyle="--", linewidth=1.5)
        ax1.set_title("Salida teórica y_teo(n) = c e^{dn} cosh(kn) u(n)")
        ax1.grid(True)

        stem_seguro(ax2, n, y_conv)
        ax2.set_title("Salida por convolución y_conv(n) = (h*x)(n)")
        ax2.grid(True)

        ax1.set_xlim(0, n[-1])
        ax2.set_xlim(0, n[-1])

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        toolbar = NavigationToolbar2Tk(canvas, self)
        toolbar.update()
        toolbar.pack(side="bottom", fill="x")
