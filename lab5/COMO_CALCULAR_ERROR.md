# Cómo se Calcula el Error del Modelo (≤ 5%)

## 🎯 Objetivo
Verificar que el modelo de reconocimiento tenga una **tasa de error máxima del 5%**.

---

## 📊 Cálculo del Error Real

### Fórmula
```
Tasa de Error = (Predicciones Incorrectas / Total de Predicciones) × 100%

Precisión = (Predicciones Correctas / Total de Predicciones) × 100%

Relación: Tasa de Error = 100% - Precisión
```

### Ejemplo Práctico

**Conjunto de prueba: 100 audios**
- Comando "segmentar": 35 audios
- Comando "cifrar": 32 audios  
- Comando "comprimir": 33 audios

**Resultados de predicción:**
- ✅ Correctas: 96
- ❌ Incorrectas: 4

**Cálculo:**
```
Tasa de Error = 4 / 100 × 100% = 4.0%
Precisión = 96 / 100 × 100% = 96.0%

Verificación: 4% ≤ 5% ✅ CUMPLE
```

---

## 🔍 Diferencia: Confianza vs Error

### ⚠️ IMPORTANTE: NO son lo mismo

| Concepto | Qué Mide | Cuándo se Calcula | Rango |
|----------|----------|-------------------|-------|
| **Confianza** | Separación entre predicciones de UNA muestra | En tiempo real, por cada predicción | 0-100% |
| **Error Real** | Proporción de fallos en MUCHAS muestras | Después de validación con conjunto de prueba | 0-100% |

### Confianza (en la GUI)
```python
# Para UNA predicción individual
sorted_dists = [("segmentar", 0.05), ("cifrar", 0.25), ("comprimir", 0.30)]

min_dist = 0.05      # Mejor predicción
second_dist = 0.25   # Segunda mejor

# Separación relativa
separacion = (0.25 - 0.05) / 0.25 = 0.80 = 80%

# Confianza: qué tan clara es la decisión
Confianza = 80% → "La predicción 'segmentar' está mucho más cerca que las demás"
```

**Interpretación:**
- **Alta (>90%)**: Las distancias están muy separadas → decisión clara
- **Media (70-90%)**: Hay cierta ambigüedad → decisión razonable  
- **Baja (<70%)**: Las distancias son similares → decisión dudosa

### Error Real (validación)
```python
# Para MUCHAS predicciones (100 muestras)
resultados = {
    "segmentar": {"correctas": 33, "incorrectas": 2},  # 33/35 = 94.3%
    "cifrar": {"correctas": 31, "incorrectas": 1},     # 31/32 = 96.9%
    "comprimir": {"correctas": 32, "incorrectas": 1},  # 32/33 = 97.0%
}

total_incorrectas = 2 + 1 + 1 = 4
total = 100

Error Real = 4/100 × 100% = 4.0% ✅ CUMPLE
```

---

## 🧪 Métodos de Validación

### 1. Hold-out (Conjunto de Prueba Separado)

**Proceso:**
```
1. Dividir datos:
   - 80% Entrenamiento (ej: 80 audios por comando)
   - 20% Prueba (ej: 20 audios por comando)

2. Entrenar modelo con 80%

3. Probar con 20% (NUNCA vistos en entrenamiento)

4. Calcular error:
   Error = incorrectas / total_prueba × 100%
```

**Ejemplo:**
```bash
# Entrenar con primeros 40 archivos de cada comando
python entrenar.py

# Probar con últimos 10 archivos de cada comando
python validar.py --test-only

# Resultado:
# Total: 30 (10×3 comandos)
# Correctas: 29
# Incorrectas: 1
# Error = 1/30 × 100% = 3.33% ✅
```

### 2. Validación Cruzada (K-Fold)

**Proceso:**
```
1. Dividir datos en K particiones (ej: K=5)

2. Para cada partición:
   - Entrenar con K-1 particiones
   - Probar con 1 partición
   - Calcular error

3. Error final = promedio de los K errores
```

**Ventaja:** Más robusto, usa todos los datos para entrenar Y probar.

**Ejemplo con K=5:**
```
Fold 1: Entrenar[2,3,4,5] → Probar[1] → Error = 4%
Fold 2: Entrenar[1,3,4,5] → Probar[2] → Error = 3%
Fold 3: Entrenar[1,2,4,5] → Probar[3] → Error = 5%
Fold 4: Entrenar[1,2,3,5] → Probar[4] → Error = 4%
Fold 5: Entrenar[1,2,3,4] → Probar[5] → Error = 3%

Error Promedio = (4+3+5+4+3)/5 = 3.8% ✅
```

---

## 💻 Cómo Validar en Este Proyecto

### Opción 1: Validación Completa
```bash
python validar.py
```

**Qué hace:**
- Prueba TODOS los archivos de `recordings/`
- Calcula tasa de error global
- Genera matriz de confusión
- Verifica si error ≤ 5%

**Salida:**
```
📊 Resumen:
  Total de muestras:    150
  Correctas:            145
  Incorrectas:          5

📈 Métricas:
  Precisión (Accuracy): 96.67%
  Tasa de Error:        3.33%

🎯 Verificación de requisito:
  ✅ CUMPLE: La tasa de error (3.33%) es menor o igual al 5%
```

### Opción 2: Validación Rápida
```bash
python validar_rapido.py
```

**Qué hace:**
- Prueba 5 archivos por comando (15 total)
- Muestra confianza de cada predicción
- Calcula error rápido

### Opción 3: GUI
```bash
python main.py
```

**En la interfaz:**
- "Confianza": Separación de predicción individual (0-100%)
- "Info": Distancias detalladas
- **NO muestra el error real del modelo**

---

## 📋 Ejemplo Completo Paso a Paso

### Situación
- 50 grabaciones de "segmentar"
- 50 grabaciones de "cifrar"
- 50 grabaciones de "comprimir"
- **Total: 150 audios**

### Paso 1: Entrenar
```bash
python entrenar.py
```
Usa los 150 audios para crear el modelo.

### Paso 2: Validar
```bash
python validar.py
```

### Paso 3: Analizar Resultados
```
Matriz de Confusión:

                 | segmentar   | cifrar      | comprimir
-----------------+-------------+-------------+-------------
segmentar        | 48          | 1           | 1          
cifrar           | 0           | 49          | 1          
comprimir        | 1           | 1           | 48         

Análisis:
- segmentar: 48/50 correctas = 96%
- cifrar: 49/50 correctas = 98%
- comprimir: 48/50 correctas = 96%

Total:
- Correctas: 145
- Incorrectas: 5
- Error = 5/150 × 100% = 3.33% ✅
```

### Interpretación
- ✅ El modelo cumple el requisito (3.33% < 5%)
- ⚠️ "segmentar" se confunde ocasionalmente con otros comandos
- 💡 "cifrar" tiene la mejor precisión (98%)

---

## 🎓 Resumen

### ✅ Error Real (lo que importa para el requisito)
```python
error = predicciones_incorrectas / total × 100%
# Debe ser ≤ 5%
```

### 📊 Confianza (información adicional útil)
```python
confianza = (dist_segunda - dist_primera) / dist_segunda × 100%
# Indica qué tan clara es cada predicción individual
```

### 🔑 Conclusión
- **Error Real**: Se calcula con validación usando `validar.py`
- **Confianza**: Se muestra en tiempo real en la GUI
- **Requisito**: Error Real ≤ 5%
- **Método**: Validar con conjunto de prueba o validación cruzada
