def guardar_csv(ruta, pares):
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("frecuencia_hz,magnitud")
        for (fr, mg) in pares:
            f.write(f"{fr},{mg}")
