from matplotlib import rcParams

def _attr(colors, name, default):
    try:
        return getattr(colors, name)
    except Exception:
        return default

def paleta(style):
    c = style.colors
    return {
        "bg":       _attr(c, "bg", "#111418"),        # fondo raíz ventana
        "surface":  _attr(c, "selectbg", "#0f1b2a"),  # panel/gráfica
        "fg":       _attr(c, "fg", "#e9ecef"),        # texto principal
        "muted":    _attr(c, "muted", "#9aa4af"),     # texto secundario
        "grid":     _attr(c, "secondary", "#2b3a4b"), # grilla/sutil
        "primary":  _attr(c, "primary", "#2d9bf0"),   # color principal
        "accent":   _attr(c, "info", "#66d9ef"),      # acento/curva teórica
        "danger":   _attr(c, "danger", "#ff6b6b"),    # opcional
        "success":  _attr(c, "success", "#51cf66"),   # opcional
        "warning":  _attr(c, "warning", "#fcc419"),   # opcional
    }

def configurar_mpl_con_tema(style):
    p = paleta(style)
    rcParams.update({
        # Fondos
        "figure.facecolor": p["bg"],
        "axes.facecolor": p["surface"],
        "savefig.facecolor": p["bg"],

        # Texto y ejes
        "text.color": p["fg"],
        "axes.edgecolor": p["grid"],
        "axes.labelcolor": p["fg"],
        "axes.titlecolor": p["fg"],

        # Ticks
        "xtick.color": p["muted"],
        "ytick.color": p["muted"],

        # Grid
        "axes.grid": True,
        "grid.color": p["grid"],
        "grid.alpha": 0.35,
        "grid.linestyle": "-",

        # Líneas/estética
        "lines.linewidth": 2.0,
        "lines.markersize": 4.5,

        # Fuente
        "font.size": 10,
    })
    return p 
