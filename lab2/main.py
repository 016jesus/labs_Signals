import tkinter as tk
from tkinter import ttk, messagebox
from typing import Tuple
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


def generar_u(n: np.ndarray) -> np.ndarray:
    return (n >= 0).astype(float)

def senal_entrada(a: float, b: float, N: int) -> Tuple[np.ndarray, np.ndarray]:
    n = np.arange(N, dtype=float)
    x = a * np.exp(b * n) * generar_u(n)
    return n, x


def respuesta_impulso(a: float, b: float, c: float, d: float, k: float, N: int) -> Tuple[np.ndarray, np.ndarray]:
    n = np.arange(N, dtype=float)
    h = np.zeros(N, dtype=float)
    A = np.exp(d + k)
    B = np.exp(d - k)
    r0 = np.exp(b)
    h[0] = c / a
    if N > 1:
        n1 = np.arange(1, N, dtype=float)
        term_A = (A - r0) * np.exp((d + k) * (n1 - 1))
        term_B = (B - r0) * np.exp((d - k) * (n1 - 1))
        h[1:] = (c / (2 * a)) * (term_A + term_B)
    return n, h


def salida_por_convolucion(x: np.ndarray, h: np.ndarray, N: int) -> np.ndarray:
    return np.convolve(x, h)[:N]


def salida_teorica(c: float, d: float, k: float, N: int) -> Tuple[np.ndarray, np.ndarray]:
    n = np.arange(N, dtype=float)
    y = c * np.exp(d * n) * np.cosh(k * n) * generar_u(n)
    return n, y


def stem_seguro(ax, n, y, **kwargs):
    try:
        return ax.stem(n, y, use_line_collection=True, **kwargs)  
    except TypeError:
        return ax.stem(n, y, **kwargs)  


class VentanaXH(tk.Toplevel):
    def __init__(self, master, n: np.ndarray, x: np.ndarray, nh: np.ndarray, h: np.ndarray):
        super().__init__(master)
        self.title("Señales x(n) y h(n)")
        self.geometry("1000x750")

        fig = Figure(figsize=(10, 8), dpi=100)
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212)

        # --- x(n) ---
        stem_seguro(ax1, n, x)
        ax1.set_title("Entrada x(n) = a e^{bn} u(n)")
        ax1.set_xlabel("n")
        ax1.set_ylabel("x(n)")
        ax1.grid(True)

        # --- h(n) ---
        stem_seguro(ax2, nh, h)
        ax2.set_title("Respuesta al impulso h(n)")
        ax2.set_xlabel("n")
        ax2.set_ylabel("h(n)")
        ax2.grid(True)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas, self)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)


class VentanaSalida(tk.Toplevel):
    def __init__(self, master, n: np.ndarray, y_conv: np.ndarray, y_teo: np.ndarray):
        super().__init__(master)
        self.title("Salida del sistema (teórica vs convolución)")
        self.geometry("1000x750")

        fig = Figure(figsize=(10, 8), dpi=100)
        ax1 = fig.add_subplot(211)  
        ax2 = fig.add_subplot(212)  

        # --- y_teórica
        ax1.plot(n, y_teo, linestyle="--", linewidth=1.5)
        ax1.set_title("Salida teórica  y_teo(n) = c e^{dn} cosh(k n) u(n)")
        ax1.set_xlabel("n")
        ax1.set_ylabel("y_teo(n)")
        ax1.grid(True)

        # --- y por convolución (discreta) ---
        stem_seguro(ax2, n, y_conv)
        ax2.set_title("Salida por convolución  y_conv(n) = (h*x)(n)")
        ax2.set_xlabel("n")
        ax2.set_ylabel("y_conv(n)")
        ax2.grid(True)

        # Opcional: mismo rango horizontal en ambas
        ax1.set_xlim(0, n[-1])
        ax2.set_xlim(0, n[-1])

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas, self)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)



class VentanaParametros(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Laboratorio: Sistema Discreto por Convolución")
        self.geometry("520x420")
        cont = ttk.Frame(self, padding=14)
        cont.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            cont,
            text="Parámetros (x(n)=a e^{bn} u(n), y(n)=c e^{dn} cosh(kn) u(n))",
            wraplength=480,
            font=("Segoe UI", 10, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

        self.var_a = tk.StringVar(value="1.0")
        self.var_b = tk.StringVar(value="-0.05")
        self.var_c = tk.StringVar(value="1.0")
        self.var_d = tk.StringVar(value="-0.02")
        self.var_k = tk.StringVar(value="0.10")
        self.var_N = tk.StringVar(value="200")

        fila = 1
        for etiqueta, var in [
            ("a (escala entrada)", self.var_a),
            ("b (exponente entrada)", self.var_b),
            ("c (escala salida)", self.var_c),
            ("d (exponente salida)", self.var_d),
            ("k (cosh en salida)", self.var_k),
            ("N (nº puntos, mínimo 100)", self.var_N),
        ]:
            ttk.Label(cont, text=etiqueta).grid(row=fila, column=0, sticky="e", pady=6, padx=(0, 10))
            ttk.Entry(cont, textvariable=var, width=20).grid(row=fila, column=1, sticky="w")
            fila += 1

        ttk.Button(cont, text="Simular y graficar", command=self.simular).grid(
            row=fila, column=0, columnspan=2, pady=18
        )

        ttk.Label(
            cont,
            text="Sugerencia de estabilidad: usar b<0 y d±k<0 (|e^{·}|<1).",
            foreground="#555",
            wraplength=480
        ).grid(row=fila + 1, column=0, columnspan=2, sticky="w")

    def leer_parametros(self) -> Tuple[float, float, float, float, float, int]:
        try:
            a = float(self.var_a.get())
            b = float(self.var_b.get())
            c = float(self.var_c.get())
            d = float(self.var_d.get())
            k = float(self.var_k.get())
            N = int(float(self.var_N.get()))
        except ValueError:
            raise ValueError("Todos los parámetros deben ser numéricos.")

        if N < 100:
            raise ValueError("N debe ser un entero mayor o igual a 100.")
        if a == 0.0:
            raise ValueError("El parámetro 'a' no puede ser cero (aparece en el denominador de h(n)).")
        return a, b, c, d, k, N

    def simular(self):
        try:
            a, b, c, d, k, N = self.leer_parametros()
        except ValueError as e:
            messagebox.showerror("Parámetros inválidos", str(e))
            return

        # Señales
        n, x = senal_entrada(a, b, N)
        nh, h = respuesta_impulso(a, b, c, d, k, N)
        y_conv = salida_por_convolucion(x, h, N)
        ny, y_teo = salida_teorica(c, d, k, N)
        # Ventanas de gráficos
        VentanaXH(self, n, x, nh, h)
        VentanaSalida(self, ny, y_conv, y_teo)


if __name__ == "__main__":
    app = VentanaParametros()
    app.mainloop()
