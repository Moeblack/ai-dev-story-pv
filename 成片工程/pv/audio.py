"""音轨：BGM（Fly Me to the Moon · 小野丽莎）+ 程序合成的开罗式 8-bit 音效。输出 输出/mix.wav。"""
import os, sys, subprocess
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import ROOT
import scenes

SR = 48000
BGM = os.path.join(os.path.dirname(ROOT), '音频', 'FlyMeToTheMoon-小野丽莎.flac')
OUT = os.path.join(ROOT, '输出')
rng = np.random.default_rng(7)

def tt(d):
    return np.arange(int(d * SR)) / SR

def env(n, a=0.004, r=0.05):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr and nr < n:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e

def sq(f, d, vol=0.3, duty=0.5):
    t = tt(d)
    ph = (np.cumsum(np.broadcast_to(f, t.shape) / SR)) % 1.0
    return vol * np.where(ph < duty, 1.0, -1.0) * env(len(t))

def sine(f, d, vol=0.5):
    t = tt(d)
    ph = np.cumsum(np.broadcast_to(f, t.shape) / SR) * 2 * np.pi
    return vol * np.sin(ph)

def noise(d, vol=0.3):
    return vol * rng.uniform(-1, 1, int(d * SR))

def lp(x, fc, order=4):
    return sosfilt(butter(order, fc, 'low', fs=SR, output='sos'), x)

def bp(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)

def cat(*xs):
    return np.concatenate(xs)

def decay(x, k):
    return x * np.exp(-np.arange(len(x)) / SR * k)

N = {  # 音名
    'C5': 523.25, 'E5': 659.25, 'G5': 783.99, 'G#5': 830.61, 'B5': 987.77, 'C6': 1046.5, 'E6': 1318.5, 'G6': 1568.0,
    'G4': 392.0, 'F#4': 369.99, 'F4': 349.23, 'E4': 329.63, 'A5': 880.0,
}

def arp(notes, step, hold, vol=0.22, duty=0.25):
    parts = [sq(N[n], step, vol, duty) for n in notes[:-1]]
    parts.append(decay(sq(N[notes[-1]], hold, vol, duty), 4))
    return cat(*parts)

def sweep(f0, f1, d, vol=0.25, kind='sq'):
    f = np.geomspace(f0, f1, int(d * SR))
    return (sq(f, d, vol) if kind == 'sq' else sine(f, d, vol)) * env(len(f))

def make():
    s = {}
    s['blip'] = cat(sq(880, 0.035, 0.18, 0.25), sq(1320, 0.05, 0.18, 0.25))
    s['open'] = cat(sq(660, 0.03, 0.14, 0.25), sq(990, 0.05, 0.14, 0.25))
    s['confirm'] = cat(sq(988, 0.06, 0.2, 0.25), decay(sq(1319, 0.16, 0.2, 0.25), 12))
    s['click'] = lp(noise(0.02, 0.5), 5000) * env(int(0.02 * SR), 0.001, 0.015)
    s['type'] = cat(lp(noise(0.012, 0.35), 6000), sq(1800, 0.01, 0.06))
    s['fanfare'] = arp(['C5', 'E5', 'G5', 'C6'], 0.08, 0.45)
    s['fanfare_small'] = arp(['G5', 'C6'], 0.09, 0.3)
    s['fanfare_big'] = cat(arp(['C5', 'E5', 'G5', 'C6', 'E6'], 0.07, 0.1), decay(
        sq(N['C6'], 0.9, 0.12, 0.25) + sq(N['E6'], 0.9, 0.1, 0.25) + sq(N['G6'], 0.9, 0.08, 0.25), 2.5))
    s['hire'] = arp(['E5', 'G#5', 'B5', 'E6'], 0.055, 0.3)
    s['alarm'] = cat(*[sq(f, 0.09, 0.16) for f in (880, 660, 880, 660)])
    s['coin'] = cat(sq(988, 0.06, 0.18, 0.25), decay(sq(1319, 0.3, 0.18, 0.25), 9))
    s['coin_big'] = cat(s['coin'][: int(0.12 * SR)], s['coin'])
    s['coin_down'] = sweep(1400, 180, 0.45, 0.16)
    s['pop'] = sweep(300, 1000, 0.07, 0.35, 'sine')
    s['pop_small'] = sweep(600, 1500, 0.05, 0.14, 'sine')
    w = bp(noise(0.45, 0.8), 500, 3000)
    s['whoosh'] = w * np.sin(np.linspace(0, np.pi, len(w)))
    s['whoosh_up'] = s['whoosh'] * 0.7 + sweep(300, 1800, 0.45, 0.08)
    s['error'] = cat(sq(196, 0.1, 0.2), np.zeros(int(0.04 * SR)), sq(196, 0.14, 0.2))
    s['stamp'] = decay(sine(90, 0.25, 0.9), 18) + np.pad(lp(noise(0.03, 0.6), 3000), (0, int(0.22 * SR)))
    s['beep'] = decay(sq(1000, 0.14, 0.18, 0.5), 6)
    launch_n = decay(lp(noise(0.9, 0.7), 2500), 4)
    s['launch'] = launch_n + np.pad(sweep(200, 1400, 0.5, 0.12), (0, len(launch_n) - int(0.5 * SR))) + \
        np.pad(decay(sine(70, 0.4, 0.8), 8), (0, len(launch_n) - int(0.4 * SR)))
    # 人群欢呼：粉红噪声包络 + 随机掌声
    d = 3.0
    pink = lp(noise(d, 1.0), 2500, 2)
    pink = bp(pink, 250, 3500)
    e = np.minimum(1, tt(d) / 0.4) * np.exp(-np.maximum(0, tt(d) - 1.2) * 1.2)
    claps = np.zeros(int(d * SR))
    for c in rng.uniform(0, d - 0.05, 90):
        i = int(c * SR)
        cl = bp(noise(0.02, 0.6), 1000, 5000)
        claps[i:i + len(cl)] += cl * np.exp(-np.arange(len(cl)) / SR * 150)
    s['cheer'] = (pink * 0.9 + claps) * e * 0.9
    # 爆炸
    d = 3.0
    bn = decay(lp(noise(d, 1.0), 900, 2), 1.6)
    sub = decay(sine(np.geomspace(70, 28, int(d * SR)), d, 1.0), 1.4)
    s['boom'] = (bn * 1.1 + sub) * 0.9
    s['thud'] = decay(sine(70, 0.3, 0.9), 14) + np.pad(lp(noise(0.02, 0.4), 2000), (0, int(0.28 * SR)))
    # 悲伤长号 wah-wah-wah-waaah
    parts = []
    for n_, dd in (('G4', 0.32), ('F#4', 0.32), ('F4', 0.32), ('E4', 1.0)):
        t_ = tt(dd)
        f = N[n_] * (1 + 0.012 * np.sin(2 * np.pi * 5.5 * t_) * (t_ > 0.3))
        x = lp(sq(f, dd, 0.22, 0.4), 1800) * env(len(t_), 0.02, 0.08)
        parts.append(x)
    s['sad'] = cat(*parts)
    return s

def main():
    os.makedirs(OUT, exist_ok=True)
    dur = scenes.DURATION
    n = int(dur * SR)
    bgm, sr = sf.read(BGM, always_2d=True)
    assert sr == SR, sr
    bgm = bgm[:n]
    if len(bgm) < n:
        bgm = np.pad(bgm, ((0, n - len(bgm)), (0, 0)))
    t = np.arange(n) / SR
    g = np.ones(n)
    g *= np.clip((dur - t) / 3.0, 0, 1)                     # 结尾 3s 淡出
    g *= 1 - 0.55 * np.exp(-np.maximum(0, t - 54.24) * 1.4) * (t >= 54.24)   # 核爆瞬间闪避
    bgm = bgm * g[:, None] * 0.85
    fx = np.zeros(n)
    lib = make()
    vol = {'boom': 0.9, 'cheer': 0.55, 'launch': 0.7, 'type': 0.6, 'pop_small': 0.6}
    for ts, name in scenes.SFX:
        x = lib[name] * vol.get(name, 0.75)
        i = int(ts * SR)
        j = min(n, i + len(x))
        fx[i:j] += x[: j - i]
    mix = bgm + fx[:, None] * 0.8
    raw = os.path.join(OUT, 'mix_raw.wav')
    sf.write(raw, mix.astype(np.float32), SR, subtype='FLOAT')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af', 'loudnorm=I=-15:TP=-1.5:LRA=11',
                    '-ar', str(SR), os.path.join(OUT, 'mix.wav')], check=True)
    print('mix ok', len(scenes.SFX), 'sfx')

if __name__ == '__main__':
    main()
