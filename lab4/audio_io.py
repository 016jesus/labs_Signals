import struct, wave
try:
    import pyaudio
except Exception:
    pyaudio = None
def _float_a_pcm16(x):
    if x>1.0: x=1.0
    if x<-1.0: x=-1.0
    return int(x*32767.0)
def _pcm16_a_float(i): return float(i)/32768.0
def _bytes_a_floats(b):
    N=len(b)//2; vals=struct.unpack("<"+"h"*N, b)
    return [_pcm16_a_float(v) for v in vals]
def _floats_a_bytes(vs):
    ints=[_float_a_pcm16(v) for v in vs]
    return struct.pack("<"+"h"*len(ints), *ints)
def grabar_voz(segundos, fs, canales=1, frames_por_buffer=1024):
    if pyaudio is None: raise RuntimeError("PyAudio no está disponible. pip install pyaudio")
    pa=pyaudio.PyAudio()
    st=pa.open(format=pyaudio.paInt16, channels=canales, rate=fs, input=True, frames_per_buffer=frames_por_buffer)
    frames=[]; total=int((fs*segundos)/frames_por_buffer)
    for _ in range(total):
        frames.append(st.read(frames_por_buffer))
    st.stop_stream(); st.close(); pa.terminate()
    return _bytes_a_floats(b"".join(frames))
def reproducir_audio(senal, fs, canales=1, frames_por_buffer=1024):
    if pyaudio is None: raise RuntimeError("PyAudio no está disponible. pip install pyaudio")
    pa=pyaudio.PyAudio()
    st=pa.open(format=pyaudio.paInt16, channels=canales, rate=fs, output=True, frames_per_buffer=frames_por_buffer)
    i=0; N=len(senal)
    while i<N:
        st.write(_floats_a_bytes(senal[i:i+frames_por_buffer])); i+=frames_por_buffer
    st.stop_stream(); st.close(); pa.terminate()
def guardar_wav(ruta, senal, fs, canales=1):
    with wave.open(ruta, "wb") as w:
        w.setnchannels(canales); w.setsampwidth(2); w.setframerate(fs)
        w.writeframes(_floats_a_bytes(senal))
