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


class FiltroButterworthPasabandaOrden4:
    """
    Implementa la ecuacion discreta del filtro Butterworth pasabanda derivada en el laboratorio,
    que incluye terminos x[n], x[n-2], x[n-4] y la realimentacion de hasta y[n-4].
    """

    def __init__(self, A0, A2, A4, B0, B1, B2, B3, B4):
        self.A0 = float(A0); self.A2 = float(A2); self.A4 = float(A4)
        self.B0 = float(B0); self.B1 = float(B1); self.B2 = float(B2)
        self.B3 = float(B3); self.B4 = float(B4)
        self._x_delay = [0.0, 0.0, 0.0, 0.0]  # [x(n-1), x(n-2), x(n-3), x(n-4)]
        self._y_delay = [0.0, 0.0, 0.0, 0.0]  # [y(n-1), y(n-2), y(n-3), y(n-4)]

    def filtrar_muestra(self, x):
        x_n2 = self._x_delay[1]
        x_n4 = self._x_delay[3]
        y_n1, y_n2, y_n3, y_n4 = self._y_delay

        y = (
            self.A0 * x
            - self.A2 * x_n2
            + self.A4 * x_n4
            - self.B1 * y_n1
            - self.B2 * y_n2
            - self.B3 * y_n3
            - self.B4 * y_n4
        ) / self.B0

        self._x_delay = [x, self._x_delay[0], self._x_delay[1], self._x_delay[2]]
        self._y_delay = [y, y_n1, y_n2, y_n3]
        return y

    def filtrar_bloque(self, senal):
        return [self.filtrar_muestra(v) for v in senal]

    def clonar_reseteado(self):
        return FiltroButterworthPasabandaOrden4(self.A0, self.A2, self.A4,
                                                self.B0, self.B1, self.B2,
                                                self.B3, self.B4)
