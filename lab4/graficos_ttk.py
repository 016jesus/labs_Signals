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


def trazar_2x2_canvas(canvas, senal_original, senal_filtrada, espectro_original, espectro_filtrada, fs, fc1, fc2):
    """
    Dibuja 4 subgráficas en un único Canvas (2x2):
      - [0,0] Señal Original (Tiempo)
      - [0,1] Espectro Original (lineal)
      - [1,0] Señal Filtrada (Tiempo)
      - [1,1] Espectro Filtrado (lineal) con sombreado de bandas entre [fc1, fc2]

    Notas:
      - Las entradas de espectro deben ser listas de tuplas (f, |X|).
      - Se aplica reduccion de puntos para rendimiento en Canvas.
    """

    canvas.delete("all")

    if not senal_original or not senal_filtrada or not espectro_original or not espectro_filtrada:
        canvas.create_text(20, 20, text="No hay datos para mostrar", fill="#b3b9c5", anchor="w")
        return

    # Copias seguras
    xo = list(senal_original)
    xf = list(senal_filtrada)
    esp_o = list(espectro_original)
    esp_f = list(espectro_filtrada)

    # Parámetros de dibujo
    canvas.update_idletasks()
    W = max(int(canvas.winfo_width()), 400)
    H = max(int(canvas.winfo_height()), 300)

    margin = 42
    inner_W = W - 2 * margin
    inner_H = H - 2 * margin
    mid_x = margin + inner_W // 2
    mid_y = margin + inner_H // 2

    grid_color = "#2e3440"
    axis_color = "#444c56"

    # Reducción de puntos
    def reduce_line(vs, max_pts=1200):
        n = len(vs)
        if n <= max_pts:
            return vs
        paso = (n + max_pts - 1) // max_pts
        out = []
        i = 0
        while i < n:
            bloque = vs[i:i+paso]
            out.append(sum(bloque)/len(bloque))
            i += paso
        return out

    def reduce_xy(xs, ys, max_pts=1200):
        n = min(len(xs), len(ys))
        if n <= max_pts:
            return xs[:n], ys[:n]
        paso = (n + max_pts - 1) // max_pts
        rx, ry = [], []
        i = 0
        while i < n:
            bx = xs[i:i+paso]
            by = ys[i:i+paso]
            # tomar el punto de mayor magnitud del bloque para preservar picos
            j = max(range(len(by)), key=lambda k: by[k])
            rx.append(bx[j])
            ry.append(by[j])
            i += paso
        return rx, ry

    xo_r = reduce_line(xo)
    xf_r = reduce_line(xf)
    fmax = max(esp_o[-1][0], esp_f[-1][0]) if esp_o and esp_f else fs/2.0
    fo_all = [p[0] for p in esp_o]
    mo_all = [p[1] for p in esp_o]
    ff_all = [p[0] for p in esp_f]
    mf_all = [p[1] for p in esp_f]
    fo, mo = reduce_xy(fo_all, mo_all)
    ff, mf = reduce_xy(ff_all, mf_all)

    # Utilidades de escalado
    def scale_x_series(idx, n, x0, x1):
        return x0 + (idx/(n-1))*(x1-x0) if n>1 else x0

    def scale_y(v, vmin, vmax, y0, y1):
        if vmax == vmin:
            return (y0+y1)/2
        return y1 - ((v - vmin)/(vmax - vmin))*(y1 - y0)

    def scale_x_freq(f, x0, x1):
        fm = max(fmax, 1e-9)
        fclamped = 0.0 if f < 0 else (fm if f > fm else f)
        return x0 + (fclamped/fm)*(x1-x0)

    # Rectángulos de subplots
    pads = 18
    rects = {
        'tl': (margin, margin, mid_x - pads, mid_y - pads),
        'tr': (mid_x + pads, margin, W - margin, mid_y - pads),
        'bl': (margin, mid_y + pads, mid_x - pads, H - margin),
        'br': (mid_x + pads, mid_y + pads, W - margin, H - margin),
    }

    # Helpers para dibujar rejilla y ejes
    def draw_grid(x0,y0,x1,y1):
        for frac in (0.25,0.5,0.75):
            y = y0 + frac*(y1-y0)
            canvas.create_line(x0, y, x1, y, fill=grid_color, dash=(2,3))
            x = x0 + frac*(x1-x0)
            canvas.create_line(x, y0, x, y1, fill=grid_color, dash=(2,3))
        canvas.create_rectangle(x0, y0, x1, y1, outline=axis_color)

    # Títulos
    canvas.create_text(rects['tl'][0], rects['tl'][1]-14, text="Senal Original (Tiempo)", fill="#e6edf3", anchor="w", font=("Segoe UI", 10, "bold"))
    canvas.create_text(rects['tr'][0], rects['tr'][1]-14, text="Espectro Original", fill="#e6edf3", anchor="w", font=("Segoe UI", 10, "bold"))
    canvas.create_text(rects['bl'][0], rects['bl'][1]-14, text="Senal Filtrada (Tiempo)", fill="#e6edf3", anchor="w", font=("Segoe UI", 10, "bold"))
    canvas.create_text(rects['br'][0], rects['br'][1]-14, text="Espectro Filtrado", fill="#e6edf3", anchor="w", font=("Segoe UI", 10, "bold"))

    # Dibujo tiempo original
    x0,y0,x1,y1 = rects['tl']
    draw_grid(x0,y0,x1,y1)
    n = len(xo_r)
    if n>0:
        vmin, vmax = min(xo_r), max(xo_r)
        pts=[]
        for i,v in enumerate(xo_r):
            px = scale_x_series(i, n, x0, x1)
            py = scale_y(v, vmin, vmax, y0, y1)
            pts += [px, py]
        canvas.create_line(pts, fill="#1f77b4", width=2, smooth=True)

    # Dibujo espectro original (lineal)
    x0,y0,x1,y1 = rects['tr']
    draw_grid(x0,y0,x1,y1)
    if mo:
        vmin, vmax = 0.0, max(mo)
        pts=[]
        for f, m in zip(fo, mo):
            px = scale_x_freq(f, x0, x1)
            py = scale_y(m, vmin, vmax, y0, y1)
            pts += [px, py]
        canvas.create_line(pts, fill="#1f77b4", width=2, smooth=True)

    # Dibujo tiempo filtrada
    x0,y0,x1,y1 = rects['bl']
    draw_grid(x0,y0,x1,y1)
    n = len(xf_r)
    if n>0:
        vmin, vmax = min(xf_r), max(xf_r)
        pts=[]
        for i,v in enumerate(xf_r):
            px = scale_x_series(i, n, x0, x1)
            py = scale_y(v, vmin, vmax, y0, y1)
            pts += [px, py]
        canvas.create_line(pts, fill="#ff7f0e", width=2, smooth=True)

    # Dibujo espectro filtrado + sombreado
    x0,y0,x1,y1 = rects['br']
    draw_grid(x0,y0,x1,y1)
    if mf:
        # sombreado bandas
        px1 = scale_x_freq(fc1, x0, x1)
        px2 = scale_x_freq(fc2, x0, x1)
        canvas.create_rectangle(x0, y0, px1, y1, fill="#ffb3b3", outline="", stipple="gray25")
        canvas.create_rectangle(px2, y0, x1, y1, fill="#ffb3b3", outline="", stipple="gray25")
        canvas.create_rectangle(px1, y0, px2, y1, fill="#7fdb7f", outline="", stipple="gray25")

        vmin, vmax = 0.0, max(mf)
        pts=[]
        for f, m in zip(ff, mf):
            px = scale_x_freq(f, x0, x1)
            py = scale_y(m, vmin, vmax, y0, y1)
            pts += [px, py]
        canvas.create_line(pts, fill="#ff7f0e", width=2, smooth=True)

    # Marco general
    canvas.create_rectangle(3, 3, W-3, H-3, outline="#343b46", width=2)


def mostrar_2x2_matplotlib(parent, senal_original, senal_filtrada, fs, fc1, fc2, on_close=None):
    """
    Abre una ventana secundaria con una figura Matplotlib 2x2:
      [0,0] Señal Original (Tiempo)
      [0,1] Espectro Original (lineal)
      [1,0] Señal Filtrada (Tiempo)
      [1,1] Espectro Filtrado (lineal) con sombreado de bandas

    Los espectros se calculan usando `calcular_dft_real`.
    """
    # Importar aquí para no cargar Matplotlib si no se usa este modo
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from dft_manual import calcular_dft_real

    # Validaciones
    if not senal_original or not senal_filtrada:
        top = tk.Toplevel(parent)
        top.title("Visualización 2x2")
        tk.Label(top, text="No hay datos para mostrar").pack(padx=16, pady=16)
        return top

    # Tiempos (sin dependencia obligatoria de NumPy)
    N_o = len(senal_original)
    N_f = len(senal_filtrada)
    fs_f = float(fs)
    t_o = [n / fs_f for n in range(N_o)]
    t_f = [n / fs_f for n in range(N_f)]

    # Espectros (frecuencia y magnitud lineal)
    esp_o = calcular_dft_real(senal_original, fs)
    esp_f = calcular_dft_real(senal_filtrada, fs)
    if not esp_o or not esp_f:
        top = tk.Toplevel(parent)
        top.title("Visualización 2x2")
        tk.Label(top, text="No fue posible calcular los espectros").pack(padx=16, pady=16)
        return top

    f_o = [float(p[0]) for p in esp_o]
    m_o = [float(p[1]) for p in esp_o]
    f_f = [float(p[0]) for p in esp_f]
    m_f = [float(p[1]) for p in esp_f]

    fmax = float(fs) / 2.0

    # Crear ventana y figura
    top = tk.Toplevel(parent)
    top.title("Visualización 2x2 - Tiempo y Frecuencia")

    fig, axs = plt.subplots(2, 2, figsize=(10, 6), dpi=100)
    plt.subplots_adjust(hspace=0.35, wspace=0.25)

    # Señal original (tiempo)
    axs[0, 0].plot(t_o, senal_original, color="#1f77b4")
    axs[0, 0].set_title("Señal Original (Tiempo)")
    axs[0, 0].set_xlabel("Tiempo (s)")
    axs[0, 0].set_ylabel("Amplitud")
    axs[0, 0].grid(True, alpha=0.3)

    # Espectro original (lineal)
    axs[0, 1].plot(f_o, m_o, color="#1f77b4")
    axs[0, 1].set_title("Espectro Original")
    axs[0, 1].set_xlabel("Frecuencia (Hz)")
    axs[0, 1].set_ylabel("|X(f)|")
    axs[0, 1].set_xlim(0, fmax)
    axs[0, 1].grid(True, alpha=0.3)

    # Señal filtrada (tiempo)
    axs[1, 0].plot(t_f, senal_filtrada, color="#ff7f0e")
    axs[1, 0].set_title("Señal Filtrada (Tiempo)")
    axs[1, 0].set_xlabel("Tiempo (s)")
    axs[1, 0].set_ylabel("Amplitud")
    axs[1, 0].grid(True, alpha=0.3)

    # Espectro filtrado (lineal) + bandas
    axs[1, 1].plot(f_f, m_f, color="#ff7f0e")
    axs[1, 1].set_title("Espectro Filtrado")
    axs[1, 1].set_xlabel("Frecuencia (Hz)")
    axs[1, 1].set_ylabel("|Y(f)|")
    axs[1, 1].set_xlim(0, fmax)
    axs[1, 1].grid(True, alpha=0.3)

    # Sombreado de bandas: Rechazo (dos zonas) y Paso (entre fc1 y fc2)
    paso = axs[1, 1].axvspan(fc1, fc2, color="#7fdb7f", alpha=0.25, label="Banda de Paso")
    rej1 = axs[1, 1].axvspan(0, max(0.0, fc1), color="#ffb3b3", alpha=0.25, label="Banda de Rechazo")
    rej2 = axs[1, 1].axvspan(min(fmax, fc2), fmax, color="#ffb3b3", alpha=0.25)
    axs[1, 1].legend(loc="upper right")

    # Embebido en Tk
    canvas = FigureCanvasTkAgg(fig, master=top)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    # Ajuste de cierre correcto
    def _on_close():
        try:
            plt.close(fig)
        finally:
            try:
                if callable(on_close):
                    on_close()
            finally:
                top.destroy()

    top.protocol("WM_DELETE_WINDOW", _on_close)
    return top


def mostrar_2x2_en_frame(frame, senal_original, senal_filtrada, fs, fc1, fc2):
    """
    Renderiza la figura 2x2 dentro de un `frame` (widget Tk) existente.
    Destruye cualquier contenido previo del frame antes de dibujar.
    """
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from dft_manual import calcular_dft_real

    # Limpiar frame
    try:
        for w in list(frame.winfo_children()):
            try:
                w.destroy()
            except Exception:
                pass
    except Exception:
        pass

    # Validaciones mínimas
    if not senal_original or not senal_filtrada:
        tk.Label(frame, text="No hay datos para mostrar").pack(padx=10, pady=10)
        return None

    fs = float(fs)
    fmax = fs / 2.0

    # Tiempos
    t_o = [n / fs for n in range(len(senal_original))]
    t_f = [n / fs for n in range(len(senal_filtrada))]

    # Espectros
    esp_o = calcular_dft_real(senal_original, fs)
    esp_f = calcular_dft_real(senal_filtrada, fs)
    if not esp_o or not esp_f:
        tk.Label(frame, text="No fue posible calcular los espectros").pack(padx=10, pady=10)
        return None

    f_o = [float(p[0]) for p in esp_o]
    m_o = [float(p[1]) for p in esp_o]
    f_f = [float(p[0]) for p in esp_f]
    m_f = [float(p[1]) for p in esp_f]

    # Figura
    fig, axs = plt.subplots(2, 2, figsize=(7.5, 5.0), dpi=100)
    plt.subplots_adjust(hspace=0.35, wspace=0.25)

    # Señal original (tiempo)
    axs[0, 0].plot(t_o, senal_original, color="#1f77b4")
    axs[0, 0].set_title("Señal Original (Tiempo)")
    axs[0, 0].set_xlabel("Tiempo (s)")
    axs[0, 0].set_ylabel("Amplitud")
    axs[0, 0].grid(True, alpha=0.3)

    # Espectro original
    axs[0, 1].plot(f_o, m_o, color="#1f77b4")
    axs[0, 1].set_title("Espectro Original")
    axs[0, 1].set_xlabel("Frecuencia (Hz)")
    axs[0, 1].set_ylabel("|X(f)|")
    axs[0, 1].set_xlim(0, fmax)
    axs[0, 1].grid(True, alpha=0.3)

    # Señal filtrada (tiempo)
    axs[1, 0].plot(t_f, senal_filtrada, color="#ff7f0e")
    axs[1, 0].set_title("Señal Filtrada (Tiempo)")
    axs[1, 0].set_xlabel("Tiempo (s)")
    axs[1, 0].set_ylabel("Amplitud")
    axs[1, 0].grid(True, alpha=0.3)

    # Espectro filtrado + sombreado
    axs[1, 1].plot(f_f, m_f, color="#ff7f0e")
    axs[1, 1].set_title("Espectro Filtrado")
    axs[1, 1].set_xlabel("Frecuencia (Hz)")
    axs[1, 1].set_ylabel("|Y(f)|")
    axs[1, 1].set_xlim(0, fmax)
    axs[1, 1].grid(True, alpha=0.3)
    axs[1, 1].axvspan(fc1, fc2, color="#7fdb7f", alpha=0.25, label="Banda de Paso")
    axs[1, 1].axvspan(0, max(0.0, fc1), color="#ffb3b3", alpha=0.25, label="Banda de Rechazo")
    axs[1, 1].axvspan(min(fmax, fc2), fmax, color="#ffb3b3", alpha=0.25)
    axs[1, 1].legend(loc="upper right")

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    # Cierre ordenado cuando el frame se destruya
    def _on_destroy(_):
        try:
            plt.close(fig)
        except Exception:
            pass

    frame.bind("<Destroy>", _on_destroy)
    return canvas
