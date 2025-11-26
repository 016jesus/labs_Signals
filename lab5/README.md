# Laboratorio 5 - Reconocimiento de Comandos de Voz por Bandas de Frecuencia

Sistema de reconocimiento de voz que identifica 3 comandos ("segmentar", "cifrar", "comprimir") mediante **análisis de energías en bandas de frecuencia**.

## 🎯 ¿Cómo Funciona?

### Concepto Principal

El sistema reconoce palabras dividiendo el audio en **K segmentos de frecuencia** y calculando la **energía de cada segmento**. Cada palabra tiene un patrón único de energías que permite distinguirlas.

**Ejemplo visual con K=10 bandas:**

```
       Energía por banda de frecuencia
       
"segmentar"  ████░░████████░░░░█████░░░░░░
"cifrar"     ████████░░░░███░░░░░░░░░█████
"comprimir"  ░░░░████████░░░░█████░░░░░░░░

Banda:       1  2  3  4  5  6  7  8  9  10
             ↓                           ↓
           Graves                     Agudas
```

### Proceso Completo

#### 1️⃣ **ENTRENAMIENTO**
```
Grabar M muestras → Calcular FFT → Dividir en K bandas → 
Calcular energías → Promediar → Guardar patrones
```

- Se graban 50 muestras de cada comando
- Se divide cada audio en 10 bandas de frecuencia
- Se calcula: **Energía = Σ|X(f)|²** para cada banda
- Se promedian todas las muestras del mismo comando
- Resultado: Cada comando tiene un "patrón de energías" único

#### 2️⃣ **RECONOCIMIENTO**
```
Audio nuevo → FFT → K bandas → Calcular energías → 
Comparar con patrones → Menor distancia = Palabra reconocida
```

- Se procesan las energías del audio desconocido
- Se compara con los patrones guardados (distancia euclidiana)
- El comando con el patrón más similar gana

**Ejemplo numérico:**
```
Audio desconocido: [0.11, 0.29, 0.20, 0.16, 0.23, ...]

Comparación:
  "segmentar": [0.12, 0.28, 0.19, 0.17, 0.24, ...] → dist = 0.03 ✓
  "cifrar":    [0.25, 0.15, 0.35, 0.10, 0.15, ...] → dist = 0.35
  "comprimir": [0.08, 0.40, 0.18, 0.12, 0.22, ...] → dist = 0.18

Resultado: "segmentar" (menor distancia)
```

📖 **Ver explicación detallada en:** [`METODO_RECONOCIMIENTO.md`](METODO_RECONOCIMIENTO.md)

## 📋 Requisitos

```bash
pip install numpy scipy sounddevice soundfile matplotlib
```

## 🚀 Uso

### 1. Entrenamiento

Entrena el modelo con las grabaciones existentes:

```bash
python entrenar.py
```

Esto genera `lab5_model.json` con las características de cada comando.

### 2. Interfaz Gráfica

Lanza la GUI completa para reconocimiento y visualización:

```bash
python main.py
```

**Funciones disponibles:**
- ✅ Entrenar modelo desde carpetas de grabaciones
- 🎤 Reconocer desde micrófono
- 📂 Reconocer desde archivo WAV
- 📊 Visualizar espectro de frecuencias
- 📈 Graficar energías por subbanda
- ⏱️ Reconocimiento en tiempo real con detección de voz

### 3. Validación del Modelo

Verifica que el modelo cumple con el requisito de **máximo 5% de error**:

```bash
python validar.py
```

Este script:
- ✅ Prueba el modelo con todos los archivos disponibles
- 📊 Calcula la **tasa de error** y **precisión**
- 🎯 Verifica si cumple el umbral del 5% de error
- 📋 Genera una **matriz de confusión**
- 📈 Muestra precisión por comando

**Salida esperada:**
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

**Opciones adicionales:**
```bash
python validar.py --quick    # Validación rápida (10 muestras/comando)
python validar.py --help     # Mostrar ayuda
```

### 4. Prueba Rápida

Verifica el funcionamiento con archivos específicos:

```bash
python probar.py
```

## 📁 Estructura de Archivos

```
lab5/
├── main.py              # Interfaz gráfica principal
├── entrenar.py          # Script de entrenamiento simple
├── probar.py            # Script de pruebas rápidas
├── validar.py           # Script de validación (verifica error ≤ 5%)
├── model_utils.py       # Funciones de entrenamiento y clasificación
├── dsp_utils.py         # Procesamiento de señales (FFT, subbandas)
├── audio_utils.py       # Grabación y carga de audio
├── lab5_model.json      # Modelo entrenado (generado)
└── recordings/          # Grabaciones de entrenamiento
    ├── segmentar/
    ├── cifrar/
    └── comprimir/
```

## ✅ Validación y Requisitos de Calidad

### Requisito: Error Máximo del 5%

El sistema debe reconocer correctamente al menos el **95%** de las muestras (tasa de error ≤ 5%).

### 📐 Cómo se Calcula el Error

```
Error Real = (Predicciones Incorrectas / Total de Predicciones) × 100%

Ejemplo:
- Total de muestras: 150
- Correctas: 145
- Incorrectas: 5
- Error = 5/150 × 100% = 3.33% ✅ (< 5%)
```

### ⚠️ Importante: Confianza ≠ Error

| Métrica | Qué mide | Dónde se ve |
|---------|----------|-------------|
| **Confianza** | Separación entre predicciones de UNA muestra | GUI (tiempo real) |
| **Error Real** | Proporción de fallos en MUCHAS muestras | `validar.py` |

**Confianza en GUI:**
- Indica qué tan "clara" es cada predicción individual
- Alta: La predicción está muy separada de las demás
- Baja: Hay ambigüedad entre comandos
- **NO es el error del modelo**

**Error Real:**
- Se calcula probando el modelo con muchas muestras
- Es la métrica que debe ser ≤ 5%
- Se obtiene con `python validar.py`

📖 **Ver explicación completa:** [`COMO_CALCULAR_ERROR.md`](COMO_CALCULAR_ERROR.md)

**Cómo se verifica:**

1. **Tasa de Error** = (Incorrectas / Total) × 100%
2. **Precisión** = (Correctas / Total) × 100%
3. Debe cumplirse: **Tasa de Error ≤ 5%**

**Métricas calculadas:**
- ✅ **Precisión global**: % de predicciones correctas
- 📋 **Matriz de confusión**: Confusiones entre comandos
- 📊 **Precisión por comando**: Rendimiento individual
- ⚠️ **Casos incorrectos**: Análisis de fallos

**Ejemplo de validación:**
```python
Total:      150 muestras
Correctas:  145 muestras
Incorrectas:  5 muestras

Tasa de Error = 5/150 × 100% = 3.33% ✅ (< 5%)
Precisión = 145/150 × 100% = 96.67% ✅
```

**Factores que afectan la precisión:**
- 📏 Número de muestras de entrenamiento (M)
- 🎚️ Número de segmentos/bandas (K)
- 🎤 Calidad de las grabaciones
- 🔊 Ruido de fondo
- 🗣️ Variabilidad en pronunciación

## 🔧 Parámetros del Sistema

- **Frecuencia de muestreo (fs)**: 44100 Hz
- **Tamaño de ventana (N)**: 4096 muestras (~93 ms)
- **Número de subbandas (K)**: 10 bandas espectrales
- **Tipo de ventana**: Hamming
- **Muestras por comando (M)**: 50 grabaciones

## 📊 Método: Reconocimiento por Bandas de Frecuencia (FFT)

### Proceso Técnico Detallado

1. **Preprocesamiento de Audio**:
   - Eliminar componente DC (offset)
   - Normalizar energía RMS (independiente del volumen)
   - Pre-énfasis: realza frecuencias altas (mejora consonantes)

2. **Análisis Espectral**:
   - Aplicar ventana de Hamming al audio
   - Calcular FFT (N=4096 puntos)
   - Obtener espectro de frecuencias [0 - 22050 Hz]

3. **División en K Bandas**:
   ```
   Espectro completo → Dividir en K=10 segmentos
   Banda 1: [0 - 2205 Hz]
   Banda 2: [2205 - 4410 Hz]
   ...
   Banda 10: [19845 - 22050 Hz]
   ```

4. **Cálculo de Energías**:
   ```python
   Para cada banda k:
     E_k = Σ |X(f)|²  (suma de potencias en la banda)
   ```

5. **Normalización**:
   - Escala logarítmica: E = log₁₀(E + ε)
   - Normalización relativa: E / Σ(E) = 1

6. **Clasificación**:
   - Distancia euclidiana: d = √(Σ(E_i - patrón_i)²)
   - Decisión: argmin(distancias)

### Ventajas del Método

✅ **Robusto**: Invariante al volumen de grabación  
✅ **Rápido**: Procesamiento en tiempo real  
✅ **Simple**: Solo requiere FFT y operaciones básicas  
✅ **Interpretable**: Visualización clara de qué frecuencias distinguen cada palabra

## 📈 Visualizaciones

La GUI muestra:
- **Espectro de frecuencias**: Magnitud FFT en dB
- **Energías por subbanda**: Distribución de energía espectral
- **Tabla de subbandas**: Valores numéricos y porcentajes
- **Nivel de entrada**: VU meter en tiempo real

## 🎯 Resultados

El sistema logra **100% de precisión** en las pruebas con las grabaciones de entrenamiento.

## 👨‍💻 Autor

Laboratorio desarrollado para el curso de Procesamiento de Señales e Imágenes.
