"""
Herramienta para grabación masiva de comandos de voz
Facilita la captura de 100+ grabaciones por comando de forma eficiente.

Características:
- Grabación con cuenta regresiva
- Reproduce beep antes de cada grabación
- Permite pausar y continuar
- Muestra progreso en tiempo real
- Guarda automáticamente con nombres secuenciales
"""

import os
import time
import numpy as np
import sounddevice as sd
import soundfile as sf
from audio_utils import ensure_dir, parse_device_index, enumerate_input_devices

# Parámetros de grabación
FS = 32768
DURACION = 0.125  # N/fs = 4096/32768 = 0.125 segundos por grabación
N = 4096

# Configuración visual
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"


def beep(freq=1000, duration=0.1, volume=0.3):
    """Genera un beep de confirmación"""
    t = np.linspace(0, duration, int(FS * duration))
    wave = volume * np.sin(2 * np.pi * freq * t)
    sd.play(wave, FS)
    sd.wait()


def cuenta_regresiva(segundos=3):
    """Cuenta regresiva visual antes de grabar"""
    for i in range(segundos, 0, -1):
        print(f"\r{YELLOW}   Preparado en {i}...{RESET}", end="", flush=True)
        time.sleep(1)
    print(f"\r{RED}   🔴 GRABANDO...{RESET}         ", flush=True)


def grabar_una(fs=FS, duracion=DURACION):
    """Graba una sola toma"""
    data = sd.rec(int(duracion * fs), samplerate=fs, channels=1, dtype='float32')
    sd.wait()
    return data.flatten()


def seleccionar_microfono():
    """Permite al usuario seleccionar el micrófono"""
    devices, hostapis = enumerate_input_devices()
    device_list = [d for d in devices if d.get('max_input_channels', 0) > 0]
    
    if not device_list:
        print(f"{RED}❌ No se encontraron dispositivos de entrada.{RESET}")
        return None
    
    print(f"\n{BOLD}{CYAN}═══════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}📱 DISPOSITIVOS DE ENTRADA DISPONIBLES:{RESET}")
    print(f"{CYAN}═══════════════════════════════════════════════════════{RESET}")
    
    for i, d in enumerate(device_list):
        api = hostapis.get(d['hostapi'], '?')
        default = " (predeterminado)" if i == 0 else ""
        print(f"  {BOLD}[{i}]{RESET} {d['name']} [{api}]{default}")
    
    print(f"{CYAN}═══════════════════════════════════════════════════════{RESET}")
    
    try:
        choice = input(f"\n{BOLD}Selecciona dispositivo [0-{len(device_list)-1}] (Enter = 0): {RESET}").strip()
        idx = int(choice) if choice else 0
        if 0 <= idx < len(device_list):
            selected = device_list[idx]
            print(f"{GREEN}✓ Usando: {selected['name']}{RESET}\n")
            return idx
        else:
            print(f"{RED}❌ Índice inválido. Usando predeterminado.{RESET}")
            return 0
    except ValueError:
        print(f"{RED}❌ Entrada inválida. Usando predeterminado.{RESET}")
        return 0


def grabar_comando_masivo(etiqueta, num_grabaciones, directorio_base="recordings", device=None):
    """
    Graba múltiples muestras de un comando con pausas opcionales.
    
    Args:
        etiqueta: Nombre del comando (ej: "hola")
        num_grabaciones: Cantidad de grabaciones a realizar
        directorio_base: Carpeta base donde guardar
        device: Dispositivo de entrada (None = predeterminado)
    """
    carpeta = os.path.join(directorio_base, etiqueta)
    ensure_dir(carpeta)
    
    # Contar archivos existentes
    existentes = [f for f in os.listdir(carpeta) if f.endswith('.wav')]
    inicio = len(existentes) + 1
    
    print(f"\n{BOLD}{BLUE}{'═' * 60}{RESET}")
    print(f"{BOLD}{BLUE}  GRABACIÓN MASIVA: '{etiqueta.upper()}'{RESET}")
    print(f"{BOLD}{BLUE}{'═' * 60}{RESET}")
    print(f"  📁 Carpeta: {carpeta}")
    print(f"  📊 Archivos existentes: {len(existentes)}")
    print(f"  🎯 A grabar: {num_grabaciones}")
    print(f"  ⏱️  Duración por muestra: {DURACION:.3f}s ({N} puntos @ {FS} Hz)")
    print(f"{BOLD}{BLUE}{'═' * 60}{RESET}\n")
    
    print(f"{YELLOW}💡 INSTRUCCIONES:{RESET}")
    print(f"   • Di la palabra '{BOLD}{etiqueta}{RESET}' claramente cuando veas {RED}🔴 GRABANDO{RESET}")
    print(f"   • Presiona {BOLD}ENTER{RESET} después de cada grabación para continuar")
    print(f"   • Escribe {BOLD}'p'{RESET} para pausar, {BOLD}'s'{RESET} para saltar, {BOLD}'q'{RESET} para salir")
    print(f"   • Varía tu tono, volumen y velocidad para diversidad\n")
    
    input(f"{BOLD}{GREEN}Presiona ENTER para comenzar...{RESET}")
    
    grabadas = 0
    i = inicio
    
    while grabadas < num_grabaciones:
        # Progreso
        porcentaje = (grabadas / num_grabaciones) * 100
        barra = "█" * int(porcentaje / 2) + "░" * (50 - int(porcentaje / 2))
        print(f"\n{CYAN}[{barra}] {porcentaje:.1f}%{RESET}")
        print(f"{BOLD}Grabación {grabadas + 1}/{num_grabaciones} (archivo #{i}){RESET}")
        
        # Beep de preparación
        beep(freq=800, duration=0.05, volume=0.2)
        time.sleep(0.3)
        
        # Cuenta regresiva
        cuenta_regresiva(segundos=2)
        
        # GRABAR
        audio = grabar_una(fs=FS, duracion=DURACION)
        
        # Guardar
        filename = os.path.join(carpeta, f"{etiqueta}_{i:03d}.wav")
        sf.write(filename, audio, FS)
        
        # Beep de confirmación
        beep(freq=1200, duration=0.08, volume=0.25)
        
        print(f"{GREEN}   ✓ Guardado: {os.path.basename(filename)}{RESET}")
        
        grabadas += 1
        i += 1
        
        # Control de flujo
        if grabadas < num_grabaciones:
            respuesta = input(f"\n{BOLD}[ENTER] Continuar | [p] Pausar | [s] Saltar | [q] Salir: {RESET}").strip().lower()
            
            if respuesta == 'q':
                print(f"\n{YELLOW}⏸️  Grabación interrumpida. Progreso guardado: {grabadas}/{num_grabaciones}{RESET}")
                break
            elif respuesta == 'p':
                print(f"\n{YELLOW}⏸️  PAUSA - Presiona ENTER para reanudar...{RESET}")
                input()
                print(f"{GREEN}▶️  Reanudando...{RESET}\n")
            elif respuesta == 's':
                print(f"{YELLOW}⏭️  Saltando esta grabación...{RESET}")
                continue
    
    # Resumen final
    print(f"\n{BOLD}{GREEN}{'═' * 60}{RESET}")
    print(f"{BOLD}{GREEN}  ✅ COMPLETADO: '{etiqueta.upper()}'{RESET}")
    print(f"{BOLD}{GREEN}{'═' * 60}{RESET}")
    print(f"  📊 Total grabado: {grabadas}/{num_grabaciones}")
    print(f"  📁 Ubicación: {carpeta}")
    print(f"{BOLD}{GREEN}{'═' * 60}{RESET}\n")


def menu_principal():
    """Menú interactivo para grabar múltiples comandos"""
    print(f"\n{BOLD}{CYAN}{'█' * 60}{RESET}")
    print(f"{BOLD}{CYAN}{'█' * 60}{RESET}")
    print(f"{BOLD}{CYAN}   🎙️  GRABADOR MASIVO DE COMANDOS DE VOZ - LAB 5{RESET}")
    print(f"{BOLD}{CYAN}{'█' * 60}{RESET}")
    print(f"{BOLD}{CYAN}{'█' * 60}{RESET}\n")
    
    # Seleccionar micrófono
    device = seleccionar_microfono()
    
    # Configurar comandos
    print(f"\n{BOLD}📝 CONFIGURACIÓN DE COMANDOS:{RESET}")
    print(f"   (Presiona ENTER para usar valores por defecto)")
    
    etiqueta_a = input(f"\n{BOLD}Comando A [{CYAN}hola{RESET}]: {RESET}").strip() or "hola"
    etiqueta_b = input(f"{BOLD}Comando B [{CYAN}adios{RESET}]: {RESET}").strip() or "adios"
    etiqueta_c = input(f"{BOLD}Comando C [{CYAN}parar{RESET}]: {RESET}").strip() or "parar"
    
    num_str = input(f"\n{BOLD}Grabaciones por comando [{CYAN}100{RESET}]: {RESET}").strip()
    num_grabaciones = int(num_str) if num_str else 100
    
    dir_base = input(f"{BOLD}Directorio base [{CYAN}recordings{RESET}]: {RESET}").strip() or "recordings"
    
    # Confirmación
    print(f"\n{BOLD}{YELLOW}📋 RESUMEN:{RESET}")
    print(f"   • Comandos: {BOLD}{etiqueta_a}, {etiqueta_b}, {etiqueta_c}{RESET}")
    print(f"   • Grabaciones por comando: {BOLD}{num_grabaciones}{RESET}")
    print(f"   • Total: {BOLD}{num_grabaciones * 3}{RESET} archivos")
    print(f"   • Tiempo estimado: ~{BOLD}{(num_grabaciones * 3 * 4)//60}{RESET} minutos")
    print(f"   • Directorio: {dir_base}/\n")
    
    confirmar = input(f"{BOLD}¿Continuar? (s/n): {RESET}").strip().lower()
    if confirmar != 's':
        print(f"{YELLOW}Operación cancelada.{RESET}")
        return
    
    # Grabar cada comando
    comandos = [etiqueta_a, etiqueta_b, etiqueta_c]
    
    for idx, cmd in enumerate(comandos, 1):
        print(f"\n{BOLD}{BLUE}╔═══════════════════════════════════════════════════════╗{RESET}")
        print(f"{BOLD}{BLUE}║  COMANDO {idx}/3: {cmd.upper():^40} ║{RESET}")
        print(f"{BOLD}{BLUE}╚═══════════════════════════════════════════════════════╝{RESET}")
        
        grabar_comando_masivo(cmd, num_grabaciones, dir_base, device)
        
        if idx < len(comandos):
            continuar = input(f"\n{BOLD}Continuar con siguiente comando? (s/n): {RESET}").strip().lower()
            if continuar != 's':
                print(f"{YELLOW}Grabación detenida. Progreso guardado.{RESET}")
                break
    
    print(f"\n{BOLD}{GREEN}{'█' * 60}{RESET}")
    print(f"{BOLD}{GREEN}   ✅ ¡PROCESO COMPLETADO!{RESET}")
    print(f"{BOLD}{GREEN}{'█' * 60}{RESET}")
    print(f"\n{BOLD}Siguiente paso:{RESET}")
    print(f"   1. Ejecuta: {CYAN}python main.py{RESET}")
    print(f"   2. Clic en '{BOLD}Entrenar desde carpetas{RESET}'")
    print(f"   3. Prueba el reconocimiento en tiempo real\n")


if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}⏸️  Grabación interrumpida por el usuario.{RESET}")
    except Exception as e:
        print(f"\n{RED}❌ Error: {e}{RESET}")
