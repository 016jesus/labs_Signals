def stem_seguro(ax, n, y, **kwargs):
    try:
        return ax.stem(n, y, use_line_collection=True, **kwargs)
    except TypeError:
        return ax.stem(n, y, **kwargs)
