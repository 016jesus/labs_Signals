from pathlib import Path
lines = Path("interfaz.py").read_text(encoding='utf-8').splitlines()
for idx, line in enumerate(lines, start=1):
    if "result_notebook" in line or "_add_audio_tab" in line or "_draw_waveform_canvas" in line:
        print(idx, line.strip())
