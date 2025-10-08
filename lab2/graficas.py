from typing import Optional

def _set_stemlines_style(stemlines, color: str, lw: float):
    if stemlines is None:
        return
    try:
        stemlines.set_color(color)
        stemlines.set_linewidth(lw)
        return
    except Exception:
        pass
    try:
        for ln in stemlines:
            ln.set_color(color)
            ln.set_linewidth(lw)
    except TypeError:
        pass


def stem_coloreado(ax, n, y, color: str, basecolor: str, marker: str = "o", lw: float = 1.8):
    cont = ax.stem(n, y)  
    if hasattr(cont, "markerline") and cont.markerline is not None:
        cont.markerline.set_marker(marker)
        cont.markerline.set_markersize(5.0)
        cont.markerline.set_color(color)
    _set_stemlines_style(getattr(cont, "stemlines", None), color, lw)
    baseline = getattr(cont, "baseline", None)
    if baseline is not None:
        try:
            baseline.set_color(basecolor)
            baseline.set_linewidth(1.0)
        except Exception:
            pass

    return cont
