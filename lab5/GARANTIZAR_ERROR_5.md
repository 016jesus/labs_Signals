# Garantizar Error ≤ 5% Según Enunciado del Laboratorio

## 📋 Requisitos del Enunciado

1. **3 subbandas** (no 10)
2. **Mínimo 100 grabaciones por comando** (no 50)
3. **Diversidad**: Grabaciones de diferentes personas
4. **Duración fija**: Todas las grabaciones con la misma duración
5. **Comparación**: Usar energía promedio Y desviación estándar

---

## ✅ Estrategias para Garantizar Error ≤ 5%

### 1. 📊 Cantidad Suficiente de Datos (CRÍTICO)

**Según enunciado: Mínimo 100 grabaciones por comando**

```python
# main.py - Ya ajustado
K = 3   # 3 subbandas (según enunciado)
M = 100 # 100 grabaciones mínimo (según enunciado)
```

**Por qué es importante:**
- Más datos → Mejor representación de la variabilidad
- Promedios y desviaciones más robustos
- Reduce sobreajuste (overfitting)

**Recomendación:**
```
Mínimo absoluto: 100 grabaciones/comando
Recomendado: 120-150 grabaciones/comando
Óptimo: 200+ grabaciones/comando
```

### 2. 🎤 Diversidad de Grabaciones (MUY IMPORTANTE)

**Según enunciado: "Fuentes muy diversas (diferentes personas)"**

**Estrategia:**

```
Por comando, grabar con:
- Mínimo 5 personas diferentes
- Diferentes géneros (hombres, mujeres)
- Diferentes edades
- Diferentes acentos/entonaciones
- Diferentes entornos acústicos
```

**Distribución sugerida (100 grabaciones):**

```
Comando "segmentar":
  - Persona 1: 20 grabaciones
  - Persona 2: 20 grabaciones
  - Persona 3: 20 grabaciones
  - Persona 4: 20 grabaciones
  - Persona 5: 20 grabaciones
  Total: 100 grabaciones

Comando "cifrar": (idem)
Comando "comprimir": (idem)
```

**Por qué es crítico:**
- Si solo grabas TÚ → El modelo solo reconoce TU voz
- Si graban varias personas → El modelo generaliza mejor
- Reduce el error cuando pruebas con voces nuevas

### 3. ⏱️ Duración Fija y Consistente

**Según enunciado: "Misma duración de tiempo"**

```python
# Recomendado
DURACION_FIJA = N / FS  # ~93ms con N=4096, fs=44100

# Ejemplo: 1 segundo exacto
N = 44100  # 1 segundo
```

**Cómo garantizar duración fija:**

```python
# En audio_utils.py
def record_fixed_length(filename: str, duration_s: float, fs: int, device=None):
    """
    Graba EXACTAMENTE duration_s segundos.
    """
    data = sd.rec(int(duration_s * fs), samplerate=fs, channels=1, dtype='float32', device=device)
    sd.wait()
    x = data.flatten()
    
    # Asegurar longitud exacta
    target_samples = int(duration_s * fs)
    if len(x) > target_samples:
        x = x[:target_samples]
    elif len(x) < target_samples:
        x = np.pad(x, (0, target_samples - len(x)))
    
    sf.write(filename, x, fs)
```

**Duración recomendada por palabra:**
- Muy corta (<0.5s): Puede perder información
- **Óptima: 1-1.5 segundos** ✅
- Muy larga (>2s): Desperdicia recursos

### 4. 📈 Uso de Desviación Estándar (SEGÚN ENUNCIADO)

**El enunciado especifica: "energía promedio Y desviación promedio"**

Ya implementado en el código:

```python
# model_utils.py - decide_label_by_min_dist()
mean = info["mean"]  # Energía promedio
std = info["std"]    # Desviación estándar

# Distancia normalizada (considera variabilidad)
d = √(Σ((E_i - mean_i) / (std_i + ε))²)
```

**Ventaja:**
- Subbandas estables (baja std) → Mayor peso
- Subbandas variables (alta std) → Menor peso
- Mejor discriminación entre comandos

### 5. 🎯 Validación Cruzada (Recomendado)

**No usar todos los datos para entrenar**

**Método Hold-out:**
```
Total: 100 grabaciones/comando
- Entrenamiento: 80 (80%)
- Validación: 20 (20%)
```

**Método K-Fold (Mejor):**
```
K=5 folds:
- 5 iteraciones
- Cada iteración: 80 entrenar, 20 validar
- Error final = promedio de 5 errores
- Más robusto
```

**Implementación:**
```python
# Entrenar con primeras 80
M_train = 80
python entrenar.py  # Usar solo primeras 80 de cada carpeta

# Validar con últimas 20
python validar.py --test-only  # Usar solo últimas 20
```

### 6. 🔧 Control de Calidad de Grabaciones

**Rechazar grabaciones que:**
- Tienen ruido excesivo
- Están cortadas
- No contienen la palabra completa
- Tienen volumen muy bajo/alto

**Script de validación de grabaciones:**
```python
def validar_grabacion(filepath, duracion_esperada, umbral_rms_min=0.01):
    """
    Verifica si una grabación es válida.
    """
    x, fs = sf.read(filepath)
    
    # Verificar duración
    duracion_real = len(x) / fs
    if abs(duracion_real - duracion_esperada) > 0.1:
        return False, "Duración incorrecta"
    
    # Verificar que no esté en silencio
    rms_val = np.sqrt(np.mean(x**2))
    if rms_val < umbral_rms_min:
        return False, "Volumen muy bajo"
    
    # Verificar que no esté saturada
    if np.max(np.abs(x)) > 0.99:
        return False, "Señal saturada"
    
    return True, "OK"
```

### 7. 📊 Configuración Óptima de Parámetros

**Según pruebas y enunciado:**

```python
# Parámetros óptimos
FS = 44100           # Frecuencia muestreo estándar
N = 44100            # 1 segundo de audio
K = 3                # 3 subbandas (enunciado)
M = 100              # Mínimo 100 grabaciones (enunciado)
WINDOW = "hamming"   # Ventana suave
```

**Probar variaciones si error > 5%:**
```python
# Aumentar datos
M = 150  # Más grabaciones

# Aumentar duración
N = 88200  # 2 segundos

# Probar otras ventanas
WINDOW = "hann"  # o "blackman"
```

### 8. 🎤 Condiciones de Grabación

**Para minimizar error:**

1. **Entorno controlado:**
   - Habitación silenciosa
   - Sin eco excesivo
   - Micrófono consistente

2. **Instrucciones claras:**
   - Pronunciar claramente
   - Volumen normal (no gritar, no susurrar)
   - Decir solo la palabra (no frases)
   - Mantener distancia consistente al micrófono

3. **Variabilidad intencional:**
   - Diferentes entonaciones
   - Diferentes velocidades (rápido, normal, lento)
   - Diferentes énfasis

### 9. 📈 Monitoreo del Error Durante Entrenamiento

**Calcular error en cada etapa:**

```python
# 1. Entrenar con 50 muestras
M = 50
entrenar() → validar() → error_50 = 8%

# 2. Entrenar con 80 muestras
M = 80
entrenar() → validar() → error_80 = 6%

# 3. Entrenar con 100 muestras
M = 100
entrenar() → validar() → error_100 = 4% ✅

# 4. Entrenar con 120 muestras
M = 120
entrenar() → validar() → error_120 = 3.5% ✅
```

**Curva de aprendizaje:**
```
Error vs Número de muestras:
|
10%|     *
 8%|       *
 6%|         *
 4%|           * * *  ← Estable aquí
 2%|
 0%|_________________
   0  50 100 150 200
```

### 10. 🎯 Checklist Final

Antes de afirmar que cumples con error ≤ 5%:

- [ ] Mínimo 100 grabaciones por comando
- [ ] Al menos 5 personas diferentes grabaron
- [ ] Todas las grabaciones tienen duración fija
- [ ] Modelo usa 3 subbandas (K=3)
- [ ] Modelo usa energía promedio Y desviación
- [ ] Validaste con conjunto de prueba separado
- [ ] Error calculado correctamente: (incorrectas/total × 100%)
- [ ] Probaste con voces NO incluidas en entrenamiento
- [ ] Matriz de confusión muestra buenos resultados
- [ ] Error por comando ≤ 5% individual

---

## 🧮 Ejemplo Completo

### Configuración
```python
K = 3      # 3 subbandas
M = 120    # 120 grabaciones/comando
N = 44100  # 1 segundo
```

### Grabaciones
```
Total: 360 grabaciones (120 × 3 comandos)

Por comando:
- 6 personas × 20 grabaciones = 120 total

División:
- Entrenamiento: 100 grabaciones/comando (300 total)
- Validación: 20 grabaciones/comando (60 total)
```

### Entrenamiento
```bash
python entrenar.py  # Usa primeras 100 de cada carpeta
```

### Validación
```bash
python validar.py --test-set  # Usa últimas 20 de cada carpeta

Resultados:
Total: 60 audios de validación
Correctas: 58
Incorrectas: 2
Error = 2/60 × 100% = 3.33% ✅
```

### Verificación por Comando
```
"segmentar": 19/20 correctas = 95% ✅
"cifrar": 20/20 correctas = 100% ✅
"comprimir": 19/20 correctas = 95% ✅
```

---

## 🎓 Conclusión

**Para GARANTIZAR error ≤ 5%:**

1. **Cantidad**: Mínimo 100 grabaciones/comando
2. **Diversidad**: Múltiples personas
3. **Consistencia**: Duración fija
4. **Método**: Energía + desviación estándar
5. **Validación**: Conjunto de prueba separado
6. **Monitoreo**: Calcular error correctamente

**Si aún tienes error > 5%:**
- Aumenta a 150-200 grabaciones
- Mejora calidad de grabaciones
- Aumenta diversidad de personas
- Ajusta duración (probar 1.5-2 segundos)
- Verifica que K=3 sea óptimo para tus palabras
