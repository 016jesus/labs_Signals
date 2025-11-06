
class FiltroBiquadOrden2:
    def __init__(self, coeficiente_b0, coeficiente_b1, coeficiente_b2, coeficiente_a1, coeficiente_a2):
        self.b0 = float(coeficiente_b0); self.b1 = float(coeficiente_b1); self.b2 = float(coeficiente_b2)
        self.a1 = float(coeficiente_a1); self.a2 = float(coeficiente_a2)
        self.x1 = 0.0; self.x2 = 0.0; self.y1 = 0.0; self.y2 = 0.0
    def filtrar_muestra(self, x):
        y = self.b0*x + self.b1*self.x1 + self.b2*self.x2 - self.a1*self.y1 - self.a2*self.y2
        self.x2, self.x1 = self.x1, x
        self.y2, self.y1 = self.y1, y
        return y
    def filtrar_bloque(self, senal):
        return [self.filtrar_muestra(v) for v in senal]
    def clonar_reseteado(self):
        return FiltroBiquadOrden2(self.b0, self.b1, self.b2, self.a1, self.a2)
