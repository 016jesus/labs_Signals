import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from typing import Tuple
import numpy as np

from señales import (
    señal_entrada,
    respuesta_impulso,
    salida_por_convolucion,
    salida_teorica,
)
from ventanas import VentanaXH, VentanaSalida


class VentanaPrincipal(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")  # tema moderno oscuro
        self.title("Sistema Discreto por Convolución")
        self.geometry("540x430")

        marco = ttk.Frame(self, padding=14)
        marco.pack(fill="both", expand=True)

        ttk.Label(
            marco,
            text="Simulación de sistema discreto:\n x(n)=a e^{bn} u(n), y(n)=c e^{dn} cosh(kn) u(n)",
            wraplength=500,
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, columnspan=2, pady=(0, 10))

        self.var_a = ttk.StringVar(value="1.0")
        self.var_b = ttk.StringVar(value="-0.05")
        self.var_c = ttk.StringVar(value="1.0")
        self.var_d = ttk.StringVar(value="-0.02")
        self.var_k = ttk.StringVar(value="0.10")
        self.var_N = ttk.StringVar(value="200")

        fila = 1
        for texto, var in [
            ("a (escala entrada)", self.var_a),
            ("b (exponente entrada)", self.var_b),
            ("c (escala salida)", self.var_c),
            ("d (exponente salida)", self.var_d),
            ("k (cosh en salida)", self.var_k),
            ("N (nº puntos, ≥100)", self.var_N),
        ]:
            ttk.Label(marco, text=texto).grid(row=fila, column=0, sticky="e", pady=6)
            ttk.Entry(marco, textvariable=var, width=20).grid(row=fila, column=1, sticky="w")
            fila += 1

        ttk.Button(
            marco, text="Simular y Graficar", bootstyle=SUCCESS, command=self.simular
        ).grid(row=fila, column=0, columnspan=2, pady=15)

        ttk.Label(
            marco,
            text="Sugerencia: usar b<0 y d±k<0 (|e^{·}|<1) para estabilidad.",
            wraplength=500,
            foreground="#aaa",
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
            raise ValueError("N debe ser mayor o igual a 100.")
        if a == 0:
            raise ValueError("El parámetro 'a' no puede ser cero.")
        return a, b, c, d, k, N

    def simular(self):
        try:
            a, b, c, d, k, N = self.leer_parametros()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        n, x = señal_entrada(a, b, N)
        nh, h = respuesta_impulso(a, b, c, d, k, N)
        y_conv = salida_por_convolucion(x, h, N)
        ny, y_teo = salida_teorica(c, d, k, N)

        VentanaXH(self, n, x, nh, h)
        VentanaSalida(self, ny, y_conv, y_teo)


if __name__ == "__main__":
    app = VentanaPrincipal()
    app.mainloop()
