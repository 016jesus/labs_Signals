# Laboratorio 5 - Reconocimiento de Comandos de Voz

Sistema de reconocimiento de voz basado en **banco de filtros con FFT** para clasificar 3 comandos: "segmentar", "cifrar" y "comprimir".

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

### 3. Prueba Rápida

Verifica el funcionamiento con archivos de prueba:

```bash
python probar.py
```

## 📁 Estructura de Archivos

```
lab5/
├── main.py              # Interfaz gráfica principal
├── entrenar.py          # Script de entrenamiento simple
├── probar.py            # Script de pruebas
├── model_utils.py       # Funciones de entrenamiento y clasificación
├── dsp_utils.py         # Procesamiento de señales (FFT, subbandas)
├── audio_utils.py       # Grabación y carga de audio
├── lab5_model.json      # Modelo entrenado (generado)
└── recordings/          # Grabaciones de entrenamiento
    ├── segmentar/
    ├── cifrar/
    └── comprimir/
```

## 🔧 Parámetros del Sistema

- **Frecuencia de muestreo (fs)**: 44100 Hz
- **Tamaño de ventana (N)**: 4096 muestras (~93 ms)
- **Número de subbandas (K)**: 10 bandas espectrales
- **Tipo de ventana**: Hamming
- **Muestras por comando (M)**: 50 grabaciones

## 📊 Método: Banco de Filtros FFT

El sistema utiliza el método de banco de filtros basado en FFT:

1. **Preprocesamiento**:
   - Pre-énfasis (realza altas frecuencias)
   - Eliminación de componente DC
   - Detección de actividad de voz (VAD)
   - Normalización de energía

2. **Extracción de características**:
   - Aplicar ventana de Hamming
   - Calcular FFT (N=4096 puntos)
   - Dividir espectro en K=10 subbandas
   - Calcular energía por subbanda: E = (1/N) Σ|X(k)|²

3. **Clasificación**:
   - Comparar con patrones entrenados
   - Distancia euclidiana mínima
   - Retornar comando con menor distancia

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
