# Laboratorio 5 - Reconocimiento de 3 Comandos de Voz

## Descripción
Sistema de reconocimiento de voz para **3 comandos** utilizando banco de filtros FFT y clasificación por distancia euclidiana mínima.

## Características
- **3 comandos de voz** (A, B, C)
- Banco de filtros basado en FFT con K subbandas
- Entrenamiento con M grabaciones por comando
- Reconocimiento desde micrófono o archivo WAV
- Reconocimiento en tiempo real con detección de silencio
- Visualización de espectro y energías por subbanda

## Requisitos
```bash
pip install numpy scipy sounddevice soundfile matplotlib
```

## Parámetros por defecto
- **FS**: 32768 Hz (frecuencia de muestreo)
- **N**: 4096 (tamaño de ventana/FFT - potencia de 2)
- **K**: 3 (número de subbandas - según enunciado)
- **M**: 100 (grabaciones por comando para entrenamiento - mínimo según enunciado)
- **Ventana**: Hamming
- **Margen de error objetivo**: Máximo 5%

## Uso

### 1. Ejecutar la aplicación
```bash
python main.py
```

### 2. Configurar parámetros
- Ajustar FS, N, K, M según necesidad
- **IMPORTANTE**: K=3 y M=100 según enunciado del laboratorio
- Definir etiquetas para los 3 comandos (A, B, C)
- Seleccionar directorio de grabaciones

### 3. Entrenar modelo

#### ⭐ **OPCIÓN A: Herramienta de Grabación Masiva (RECOMENDADO)**
```bash
python grabador_masivo.py
```

**Características:**
- ✅ Graba automáticamente 100+ muestras por comando
- ✅ Cuenta regresiva antes de cada grabación
- ✅ Beeps de confirmación
- ✅ Pausar/reanudar en cualquier momento
- ✅ Barra de progreso en tiempo real
- ✅ Nombres automáticos secuenciales
- ✅ Control total del flujo de grabación

**Flujo:**
1. Seleccionar micrófono
2. Configurar nombres de comandos
3. Definir cantidad de grabaciones (default: 100)
4. Grabar cada comando secuencialmente
5. Archivos guardados automáticamente en `recordings/`

#### **OPCIÓN B: Grabar desde la interfaz gráfica**
1. Configurar las 3 etiquetas (ej: "hola", "adiós", "parar")
2. **Importante**: Cambiar M a 100 en la GUI
3. Clic en "Grabar M por etiqueta"
4. Seguir instrucciones para cada grabación
5. **Advertencia**: Requiere 300 grabaciones manuales (muy tedioso)

#### **OPCIÓN C: Usar grabaciones existentes**
1. Organizar carpetas con al menos 100 archivos WAV por comando:
   ```
   recordings/
   ├── A/
   │   ├── A_001.wav
   │   ├── A_002.wav
   │   ├── ...
   │   └── A_100.wav
   ├── B/
   │   └── ... (100 archivos)
   └── C/
       └── ... (100 archivos)
   ```
2. **Requisitos**:
   - Misma duración: 0.125s (4096 puntos @ 32768 Hz)
   - Misma frecuencia de muestreo: 32768 Hz
   - Formato: WAV mono
   - **Diversidad**: Grabar con diferentes personas, tonos, volúmenes
3. Clic en "Entrenar desde carpetas"

#### **OPCIÓN D: Herramientas Externas**
Si prefieres usar otras herramientas:

**Audacity:**
1. Configurar proyecto a 32768 Hz
2. Generar > Tono de clic (para marcar intervalos)
3. Grabar múltiples palabras con pausas
4. Analizar > Etiquetas de sonido (detectar)
5. Archivo > Exportar múltiples (por etiquetas)

**Python script simple:**
```python
import sounddevice as sd
import soundfile as sf
fs, duracion = 32768, 0.125
for i in range(100):
    input(f"Presiona ENTER para grabar {i+1}/100...")
    audio = sd.rec(int(duracion*fs), fs, channels=1, dtype='float32')
    sd.wait()
    sf.write(f'hola_{i+1:03d}.wav', audio, fs)
```

### 4. Guardar/Cargar modelo
- **Guardar**: Almacena el modelo entrenado en formato JSON
- **Cargar**: Restaura un modelo previamente guardado

### 5. Reconocimiento

#### Una sola toma
- Clic en "Reconocer 1 toma (N/fs)"
- Hablar cuando se indique

#### Desde archivo
1. Clic en "Seleccionar WAV"
2. Clic en "Predecir archivo"

#### Tiempo real
1. Clic en "Iniciar RT (5s buffer)"
2. Hablar normalmente
3. La predicción se actualiza automáticamente
4. Clic en "Detener RT" para finalizar

## Fundamento Matemático

### 1. Banco de Filtros por FFT (Técnica del Laboratorio)
El método implementado sigue **exactamente** la técnica descrita en el documento:

1. **Aplicar ventana** (Hamming) a la señal de N puntos
2. **Calcular FFT completa**: X(k) con k = 0, 1, ..., N/2
3. **Particionar bins de FFT** en K=3 subbandas iguales
   - Ejemplo con 8 bins y K=3:
     - X₁(k) = {X(0), X(1), X(2)}
     - X₂(k) = {X(3), X(4), X(5)}
     - X₃(k) = {X(6), X(7)}

### 2. Energía por Subbanda
Fórmula exacta del documento:
```
E = (1/N) Σ|X(k)|²
```
donde la suma es sobre los bins de cada subbanda.

### 3. Entrenamiento
Para cada comando (A, B, C) con M=100 grabaciones:

**Energía promedio por subbanda:**
```
Ec1 = (ΣEc1) / M
Ec2 = (ΣEc2) / M  
Ec3 = (ΣEc3) / M
```

**Vector de umbrales del comando C:**
```
C → [Ec1, Ec2, Ec3]
```

Se repite para comandos B y C.

### 4. Reconocimiento en Tiempo Real
1. Capturar señal de N/fs segundos
2. Calcular vector de energías: [E1, E2, E3]
3. Comparar con vectores de umbrales de cada comando
4. **Decisión**: Comando con menor distancia euclidiana

**Fórmula de distancia:**
```
d(E, Ec) = ||E - Ec|| = √[(E1-Ec1)² + (E2-Ec2)² + (E3-Ec3)²]
```

**Predicción:**
```
comando_reconocido = argmin{d(E, Ea), d(E, Eb), d(E, Ec)}
```

## Estructura del Modelo (JSON)
```json
{
  "fs": 32768,
  "N": 4096,
  "K": 4,
  "window": "hamming",
  "commands": {
    "A": {
      "mean": [E₀, E₁, E₂, E₃],
      "std": [σ₀, σ₁, σ₂, σ₃],
      "count": 8
    },
    "B": { ... },
    "C": { ... }
  }
}
```

## Archivos del Proyecto
- `main.py`: Interfaz gráfica principal
- `audio_utils.py`: Grabación, carga de WAV, dispositivos
- `dsp_utils.py`: Banco de filtros, FFT, energías
- `model_utils.py`: Entrenamiento y clasificación
- `lab5_model.json`: Modelo guardado (generado)
- `recordings/`: Grabaciones de entrenamiento

## Notas
- Todos los archivos WAV deben tener la misma frecuencia de muestreo que el modelo
- El reconocimiento en tiempo real requiere un micrófono configurado
- La detección de silencio usa umbral de -50 dBFS por defecto
- El buffer circular es de 5 segundos en modo RT

## Diferencias con Lab3
- **Lab3**: 2 comandos de voz
- **Lab5**: 3 comandos de voz
- Interfaz actualizada para manejar 3 etiquetas simultáneamente
- Mismo fundamento matemático (banco de filtros + distancia euclidiana)
