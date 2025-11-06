"""
Modulo: graficos_ttk.py
-------------------------------------
Funciones de trazado para los espectros en la interfaz.
"""

import tkinter as tk
from math import log10


def trazar_espectros_dobles(canvas, espectro_original, espectro_filtrada):
    """
    Dibuja dos subgraficas en un canvas:
      - Superior: magnitud del espectro original (dB)
      - Inferior: magnitud del espectro filtrado (dB)
    Ambas se escalan automaticamente al tamano del canvas.
    """

    # --- Limpieza y validaciones ---
    canvas.delete("all")
    espectro_original = list(espectro_original or [])
    espectro_filtrada = list(espectro_filtrada or [])

    if len(espectro_original) == 0 or len(espectro_filtrada) == 0:
        canvas.create_text(20, 20, text="No hay datos para mostrar",
                           fill="#b3b9c5", anchor="w")
        return

    # Emparejar longitudes
    N = min(len(espectro_original), len(espectro_filtrada))
    espectro_original = espectro_original[:N]
    espectro_filtrada = espectro_filtrada[:N]

    # Reducir puntos para dibujo (performance en Canvas)
    MAX_PTS = 1600
    if N > MAX_PTS:
        paso = (N + MAX_PTS - 1) // MAX_PTS

        def _down(vs):
            out = []
            i = 0
            while i < len(vs):
                bloque = vs[i:i + paso]
                out.append(max(bloque))  # preservar picos
                i += paso
            return out

        espectro_original = _down(espectro_original)
        espectro_filtrada = _down(espectro_filtrada)
        N = min(len(espectro_original), len(espectro_filtrada))
        espectro_original = espectro_original[:N]
        espectro_filtrada = espectro_filtrada[:N]

    # Obtener tamano del canvas
    canvas.update_idletasks()
    ancho = max(int(canvas.winfo_width()), 400)
    alto = max(int(canvas.winfo_height()), 300)

    mitad = alto // 2
    margen_x = 40
    margen_y = 25

    # Convertir magnitudes a dB (log10 evita desbordes)
    def to_db(x):
        return 20 * log10(max(x, 1e-12))

    espec_o_db = [to_db(v) for v in espectro_original]
    espec_f_db = [to_db(v) for v in espectro_filtrada]

    # Escalas verticales
    max_val = max(max(espec_o_db), max(espec_f_db))
    min_val = min(min(espec_o_db), min(espec_f_db))
    rango = max_val - min_val if max_val != min_val else 1

    def esc_x(i):
        return margen_x + (i / (N - 1)) * (ancho - 2 * margen_x)

    def esc_y(db_val, mitad_sup):
        # Escala invertida (arriba = mayor valor)
        return mitad_sup - ((db_val - min_val) / rango) * (mitad_sup - margen_y)

    # Grid suave (moderno)
    grid_color = "#2e3440"
    for frac in (0.25, 0.5, 0.75):
        y1 = int((mitad - margen_y) * frac) + margen_y
        canvas.create_line(margen_x, y1, ancho - margen_x, y1, fill=grid_color, dash=(2, 3))
        y2 = mitad + int((alto - mitad - margen_y) * frac)
        canvas.create_line(margen_x, y2, ancho - margen_x, y2, fill=grid_color, dash=(2, 3))
    for frac in (0.2, 0.4, 0.6, 0.8):
        x = int(margen_x + frac * (ancho - 2 * margen_x))
        canvas.create_line(x, margen_y, x, alto - margen_y, fill=grid_color, dash=(2, 3))

    # === Subgrafica superior (original) ===
    alto_sup = mitad
    puntos_o = []
    for i, dbv in enumerate(espec_o_db):
        puntos_o += [esc_x(i), esc_y(dbv, alto_sup)]
    canvas.create_line(puntos_o, fill="#58a6ff", width=2, smooth=True)
    canvas.create_text(margen_x, 10, text="Espectro Original (dB)",
                       fill="#e6edf3", font=("Segoe UI", 10, "bold"), anchor="w")

    # Eje horizontal superior
    canvas.create_line(margen_x, alto_sup - margen_y,
                       ancho - margen_x, alto_sup - margen_y, fill="#444c56")

    # === Subgrafica inferior (filtrada) ===
    alto_inf = alto - mitad
    base_y = mitad + margen_y
    puntos_f = []
    for i, dbv in enumerate(espec_f_db):
        y = base_y + esc_y(dbv, alto_inf)
        puntos_f += [esc_x(i), y]
    canvas.create_line(puntos_f, fill="#3fb950", width=2, smooth=True)
    canvas.create_text(margen_x, mitad + 10, text="Espectro Filtrado (dB)",
                       fill="#e6edf3", font=("Segoe UI", 10, "bold"), anchor="w")

    # Eje horizontal inferior
    canvas.create_line(margen_x, alto - margen_y,
                       ancho - margen_x, alto - margen_y, fill="#444c56")

    # === Marco decorativo ===
    canvas.create_rectangle(3, 3, ancho - 3, alto - 3, outline="#343b46", width=2)

