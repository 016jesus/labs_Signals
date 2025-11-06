import os
import argparse
import math
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly


def rms_envelope(x: np.ndarray, win_len: int, hop: int) -> np.ndarray:
	# compute RMS envelope with frames of win_len and hop
	n = len(x)
	frames = 1 + max(0, (n - win_len) // hop)
	rms = []
	for i in range(0, n - win_len + 1, hop):
		w = x[i:i+win_len]
		rms.append(np.sqrt(np.mean(w.astype('float64')**2)))
	if len(rms) == 0:
		return np.array([0.0], dtype=float)
	return np.array(rms, dtype=float)


def detect_active_region(x: np.ndarray, sr: int, win_ms=20, hop_ms=10, thresh_factor=3.0):
	win = max(1, int(sr * win_ms / 1000))
	hop = max(1, int(sr * hop_ms / 1000))
	env = rms_envelope(x, win, hop)
	# estimate noise floor as median of lowest 20% frames
	sorted_env = np.sort(env)
	n = len(sorted_env)
	noise_med = float(np.median(sorted_env[:max(1, n//5)])) if n>0 else 0.0
	thresh = max(noise_med * thresh_factor, noise_med + 1e-8)
	active_idx = np.where(env > thresh)[0]
	if active_idx.size == 0:
		# fallback: use entire signal
		return 0, len(x)
	start_frame = active_idx[0]
	end_frame = active_idx[-1]
	start_sample = max(0, start_frame * hop)
	end_sample = min(len(x), (end_frame * hop) + win)
	return start_sample, end_sample


def center_and_pad_segment(x: np.ndarray, start: int, end: int, target_samples: int) -> np.ndarray:
	seg = x[start:end]
	L = len(seg)
	if L >= target_samples:
		# center based on energy centroid
		energy = seg.astype('float64')**2
		if energy.sum() <= 0:
			center = L // 2
		else:
			center = int((energy * np.arange(L)).sum() / energy.sum())
		half = target_samples // 2
		seg_start = max(0, center - half)
		if seg_start + target_samples > L:
			seg_start = max(0, L - target_samples)
		out = seg[seg_start:seg_start+target_samples]
		return out
	else:
		# pad to target length, centering the segment
		pad_total = target_samples - L
		pad_left = pad_total // 2
		pad_right = pad_total - pad_left
		out = np.concatenate((np.zeros(pad_left, dtype=seg.dtype), seg, np.zeros(pad_right, dtype=seg.dtype)))
		return out


def resample_to_target(x: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
	if orig_sr == target_sr:
		return x
	# use resample_poly with integer up/down
	g = math.gcd(orig_sr, target_sr)
	up = target_sr // g
	down = orig_sr // g
	y = resample_poly(x, up, down)
	return y


def process_file(path: str, out_dir: str, target_sr: int = 32768, target_len_s: float = 1.0):
	x, sr = sf.read(path)
	if x.ndim > 1:
		x = x.mean(axis=1)
	x = x.astype('float32')
	start, end = detect_active_region(x, sr, win_ms=20, hop_ms=10, thresh_factor=3.0)
	target_samples = int(round(target_sr * target_len_s))
	# extract segment from original at original sr that contains active region; we want 1s at target sr
	# to avoid resampling a huge clip, first center/pad in original sr domain for target_len in seconds
	orig_target_samples = int(round(sr * target_len_s))
	seg_orig = center_and_pad_segment(x, start, end, orig_target_samples)
	# resample to target_sr
	seg_resampled = resample_to_target(seg_orig, sr, target_sr)
	# ensure exact length
	if len(seg_resampled) < target_samples:
		pad = target_samples - len(seg_resampled)
		seg_resampled = np.concatenate((seg_resampled, np.zeros(pad, dtype=seg_resampled.dtype)))
	elif len(seg_resampled) > target_samples:
		seg_resampled = seg_resampled[:target_samples]

	# save
	fname = os.path.basename(path)
	name, _ = os.path.splitext(fname)
	out_path = os.path.join(out_dir, name + f"_norm_{target_sr}Hz_{target_len_s:.2f}s.wav")
	sf.write(out_path, seg_resampled, target_sr, subtype='PCM_16')
	print(f"Saved: {out_path}")


def process_folder(input_dir: str, out_dir: str, target_sr: int = 32768, target_len_s: float = 1.0):
	if not os.path.isdir(out_dir):
		os.makedirs(out_dir, exist_ok=True)
	files = sorted([f for f in os.listdir(input_dir) if f.lower().endswith('.wav')])
	if not files:
		print('No wav files found in', input_dir)
		return
	for f in files:
		p = os.path.join(input_dir, f)
		try:
			process_file(p, out_dir, target_sr, target_len_s)
		except Exception as e:
			print('Error processing', p, e)


def parse_args():
	p = argparse.ArgumentParser(description='Normalize WAVs: trim silence and resample to 32768 Hz, length 1s')
	p.add_argument('input_dir', help='Carpeta con WAVs')
	p.add_argument('--out', default=None, help='Directorio de salida (default: input_dir/normalized)')
	p.add_argument('--sr', type=int, default=32768, help='Sample rate objetivo (default 32768)')
	p.add_argument('--len', type=float, default=1.0, help='Duración objetivo en segundos (default 1.0)')
	return p.parse_args()


if __name__ == '__main__':
	args = parse_args()
	outdir = args.out if args.out else os.path.join(args.input_dir, 'normalized')
	process_folder(args.input_dir, outdir, target_sr=args.sr, target_len_s=args.len)

