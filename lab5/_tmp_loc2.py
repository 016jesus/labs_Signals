from pathlib import Path
lines = Path("interfaz.py").read_text(encoding='utf-8').splitlines()
for idx, line in enumerate(lines, start=1):
    if "_procesar_audio" in line:
        print(idx, line.strip())
