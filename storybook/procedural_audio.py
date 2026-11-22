"""Síntesis procedural de ambientes y efectos sonoros (solo NumPy).

Todo el audio se genera desde cero con ruido filtrado, osciladores y envolventes:
no usa grabaciones de terceros, funciona sin conexión y no tiene problemas de licencia.
"""
from __future__ import annotations

import numpy as np

SR = 22050


# ----------------------------------------------------------------- utilidades
def _noise(n, rng, sr, lo=None, hi=None):
    """Ruido blanco filtrado en frecuencia (paso alto `lo`, paso bajo `hi`), normalizado a pico 1."""
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1.0 / sr)
    mask = np.ones_like(f)
    if lo:
        mask = mask / (1 + (lo / np.maximum(f, 1e-3)) ** 4)
    if hi:
        mask = mask / (1 + (f / hi) ** 4)
    y = np.fft.irfft(spec * mask, n)
    return y / (np.max(np.abs(y)) + 1e-9)


def _lfo(n, rng, sr, rate, depth=0.7):
    """Modulación lenta aleatoria en [1-depth, 1]."""
    x = _noise(n, rng, sr, hi=rate)
    x = (x - x.min()) / (x.max() - x.min() + 1e-9)
    return (1 - depth) + depth * x


def _burst(length, sr, decay, rng, lo=None, hi=None):
    n = max(8, int(length * sr))
    t = np.arange(n) / sr
    return _noise(n, rng, sr, lo, hi) * np.exp(-t / decay)


def _tone(freq, length, sr, decay, attack=0.005, harmonics=(1.0,)):
    n = int(length * sr)
    t = np.arange(n) / sr
    x = sum(h * np.sin(2 * np.pi * freq * (k + 1) * t) for k, h in enumerate(harmonics))
    x = x / max(1e-9, sum(harmonics))
    return x * np.minimum(1.0, t / attack) * np.exp(-t / decay)


def _place(out, sig, pos, gain=1.0):
    pos = int(pos)
    end = min(len(out), pos + len(sig))
    if 0 <= pos < end:
        out[pos:end] += sig[: end - pos] * gain


def _echo(x, sr, delays=(0.23, 0.41, 0.67), gains=(0.5, 0.3, 0.18)):
    y = x.copy()
    for d, g in zip(delays, gains):
        k = int(d * sr)
        if 0 < k < len(x):
            y[k:] += x[:-k] * g
    return y


def make_loop(x, sr, fade_s=1.0):
    """Convierte un audio en bucle sin costura (crossfade entre final e inicio)."""
    n = int(fade_s * sr)
    if len(x) < 4 * n:
        return x
    w = np.linspace(0.0, 1.0, n)
    mixed = x[:n] * w + x[-n:] * (1 - w)
    return np.concatenate([mixed, x[n:-n]])


# ------------------------------------------------------------------ generadores
def wind(n, sr, rng):
    base = _noise(n, rng, sr, 60, 900) * _lfo(n, rng, sr, 0.2, 0.8)
    whistle = _noise(n, rng, sr, 500, 1800) * _lfo(n, rng, sr, 0.3, 0.9) * 0.25
    return base + whistle


def rain(n, sr, rng):
    x = _noise(n, rng, sr, 1500, 9000) * 0.6 + _noise(n, rng, sr, 300, 1200) * 0.15
    drops = np.zeros(n)
    for _ in range(int(25 * n / sr)):
        _place(drops, _burst(0.012, sr, 0.003, rng, 2500, 9000), rng.integers(0, n), rng.uniform(0.2, 0.8))
    return x + drops * 0.5


def storm(n, sr, rng):
    x = rain(n, sr, rng) * 0.8 + wind(n, sr, rng) * 0.4
    length = int(3.0 * sr)
    t = np.arange(length) / sr
    for _ in range(max(1, int(n / sr / 9))):
        rumble = _noise(length, rng, sr, 25, 140) * np.exp(-t / 1.1) * np.minimum(1, t / 0.15)
        _place(x, rumble * 2.0, rng.integers(0, max(1, n - length)))
    return x


def fire(n, sr, rng):
    x = _noise(n, rng, sr, 40, 500) * 0.35
    x += _noise(n, rng, sr, 800, 3500) * 0.08 * _lfo(n, rng, sr, 3, 0.6)
    for _ in range(int(14 * n / sr)):
        c = _burst(0.03, sr, rng.uniform(0.004, 0.012), rng, 1000, 6000)
        _place(x, c, rng.integers(0, n), rng.uniform(0.2, 1.0) * 0.9)
    return x


def ocean(n, sr, rng):
    swell = _lfo(n, rng, sr, 0.12, 0.85)
    return _noise(n, rng, sr, 80, 1400) * swell + 0.15 * _noise(n, rng, sr, 2000, 6000) * swell


def river(n, sr, rng):
    return _noise(n, rng, sr, 300, 5000) * _lfo(n, rng, sr, 7, 0.25) + 0.2 * _noise(n, rng, sr, 100, 400)


def _chirp(sr, rng):
    length = rng.uniform(0.08, 0.2)
    n = int(length * sr)
    t = np.arange(n) / sr
    f0 = rng.uniform(2200, 4200)
    f = f0 + (f0 * rng.uniform(0.6, 1.5) - f0) * t / length
    return np.sin(2 * np.pi * np.cumsum(f) / sr) * np.sin(np.pi * t / length) ** 2


def forest(n, sr, rng):
    x = wind(n, sr, rng) * 0.35
    pos = rng.uniform(0, 1)
    while pos < n / sr - 0.5:
        for _ in range(int(rng.integers(1, 4))):
            _place(x, _chirp(sr, rng), pos * sr, 0.35)
            pos += rng.uniform(0.1, 0.18)
        pos += rng.uniform(0.8, 2.5)
    return x


def night(n, sr, rng):
    x = wind(n, sr, rng) * 0.2
    t = np.arange(n) / sr
    k = np.ones(40) / 40
    gate = np.convolve((np.sin(2 * np.pi * 30 * t) > 0.3) * (np.sin(2 * np.pi * 1.8 * t) > 0.1), k, mode="same")
    x += np.sin(2 * np.pi * 4300 * t) * gate * 0.18 * _lfo(n, rng, sr, 0.2, 0.4)
    gate2 = np.convolve((np.sin(2 * np.pi * 27 * t) > 0.3) * (np.sin(2 * np.pi * 1.3 * t + 1) > 0.1), k, mode="same")
    x += np.sin(2 * np.pi * 3800 * t + 1.3) * gate2 * 0.12
    hoot_len = int(1.5 * sr)
    for _ in range(max(1, int(n / sr / 7))):
        p = int(rng.integers(0, max(1, n - hoot_len)))
        _place(x, _tone(420, 0.45, sr, 0.3, 0.05), p, 0.3)
        _place(x, _tone(350, 0.6, sr, 0.4, 0.05), p + int(0.55 * sr), 0.3)
    return x


def cave(n, sr, rng):
    t = np.arange(n) / sr
    x = 0.25 * np.sin(2 * np.pi * 55 * t) * _lfo(n, rng, sr, 0.1, 0.5) + 0.15 * np.sin(2 * np.pi * 82.4 * t + 1)
    x += _noise(n, rng, sr, 30, 300) * 0.2
    drips = np.zeros(n)
    for _ in range(int(0.5 * n / sr) + 2):
        _place(drips, _tone(rng.uniform(900, 2200), 0.25, sr, 0.05), rng.integers(0, n), 0.5)
    return x + _echo(drips, sr, (0.3, 0.55, 0.9), (0.5, 0.35, 0.2))


def tension(n, sr, rng):
    t = np.arange(n) / sr
    x = 0.3 * np.sin(2 * np.pi * 110 * t) + 0.25 * np.sin(2 * np.pi * 116.5 * t + 0.5) + 0.2 * np.sin(2 * np.pi * 164.8 * t + 1.1)
    x = x * _lfo(n, rng, sr, 0.25, 0.5)
    return x + _noise(n, rng, sr, 40, 400) * 0.25


def footsteps(n, sr, rng):
    x = wind(n, sr, rng) * 0.12
    t, step = 0.4, 0
    while t < n / sr - 0.3:
        thud = _burst(0.12, sr, 0.04, rng, 60, 700) + 0.6 * _tone(85 + rng.uniform(-10, 10), 0.12, sr, 0.04, 0.002)
        _place(x, thud, t * sr, 0.9 if step % 2 == 0 else 0.75)
        t += 0.55 + rng.uniform(-0.03, 0.03)
        step += 1
    return x


def heartbeat(n, sr, rng):
    x = tension(n, sr, rng) * 0.25
    t = 0.2
    while t < n / sr - 0.5:
        _place(x, _tone(52, 0.22, sr, 0.07, 0.004), t * sr, 1.0)
        _place(x, _tone(46, 0.2, sr, 0.06, 0.004), (t + 0.28) * sr, 0.7)
        t += 60 / 72
    return x


def magic(n, sr, rng):
    scale = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5, 1174.7, 1318.5]
    x = np.zeros(n)
    t = 0.2
    while t < n / sr - 0.5:
        f = float(rng.choice(scale))
        _place(x, _tone(f, 1.2, sr, 0.35, 0.01, (1.0, 0.3, 0.1)), t * sr, rng.uniform(0.3, 0.7))
        t += rng.uniform(0.25, 0.7)
    x = _echo(x, sr, (0.25, 0.5), (0.4, 0.25))
    tt = np.arange(n) / sr
    pad = _noise(n, rng, sr, 2500, 7000) * 0.05 * _lfo(n, rng, sr, 0.3, 0.8)
    return x + pad + 0.08 * np.sin(2 * np.pi * 261.6 * tt) * _lfo(n, rng, sr, 0.2, 0.6)


def city(n, sr, rng):
    x = _noise(n, rng, sr, 40, 350) * 0.5 + _noise(n, rng, sr, 300, 2500) * 0.12 * _lfo(n, rng, sr, 0.5, 0.7)
    length = int(2.2 * sr)
    tt = np.arange(length) / sr
    for _ in range(max(1, int(n / sr / 8))):
        car = _noise(length, rng, sr, 150, 1500) * np.sin(np.pi * tt / (length / sr)) ** 2
        _place(x, car * 0.4, rng.integers(0, max(1, n - length)))
    hl = int(0.35 * sr)
    th = np.arange(hl) / sr
    horn = (np.sin(2 * np.pi * 420 * th) + np.sin(2 * np.pi * 530 * th)) * 0.5
    horn *= np.minimum(1, th / 0.02) * np.minimum(1, (0.35 - th) / 0.03)
    for _ in range(max(1, int(n / sr / 12))):
        _place(x, horn * 0.15, rng.integers(0, max(1, n - hl)))
    return x


def crowd(n, sr, rng):
    x = np.zeros(n)
    for _ in range(6):
        x += _noise(n, rng, sr, 180, 1800) * _lfo(n, rng, sr, rng.uniform(2.5, 5), 0.9)
    return x / 3


def creak(n, sr, rng):
    x = tension(n, sr, rng) * 0.3
    for _ in range(max(1, int(n / sr / 6))):
        length = int(rng.uniform(0.9, 1.6) * sr)
        t = np.arange(length) / sr
        dur = length / sr
        f = 180 + 120 * np.sin(np.pi * t / dur) + 12 * np.sin(2 * np.pi * 14 * t)
        ph = 2 * np.pi * np.cumsum(f) / sr
        saw = 2 * ((ph / (2 * np.pi)) % 1) - 1
        saw = np.convolve(saw, np.ones(6) / 6, mode="same") * np.sin(np.pi * t / dur)
        _place(x, saw * 0.35, rng.integers(0, max(1, n - length)))
    return x


def spaceship(n, sr, rng):
    t = np.arange(n) / sr
    x = 0.3 * np.sin(2 * np.pi * 60 * t) + 0.15 * np.sin(2 * np.pi * 120.7 * t) + _noise(n, rng, sr, 50, 500) * 0.15
    x = x * _lfo(n, rng, sr, 0.3, 0.3)
    for _ in range(int(0.5 * n / sr) + 2):
        _place(x, _tone(float(rng.choice([880, 1320, 1760, 1046])), 0.15, sr, 0.06, 0.003), rng.integers(0, n), 0.25)
    return x


def clock(n, sr, rng):
    x = _noise(n, rng, sr, 30, 250) * 0.05
    t, k = 0.3, 0
    while t < n / sr - 0.2:
        c = _burst(0.03, sr, 0.006, rng, 1500, 5000) + 0.5 * _tone(1800 if k % 2 == 0 else 1500, 0.03, sr, 0.01, 0.001)
        _place(x, c, t * sr, 0.9 if k % 2 == 0 else 0.6)
        t += 1.0
        k += 1
    return x


GENERATORS = {
    "wind": wind, "rain": rain, "storm": storm, "fire": fire, "ocean": ocean,
    "river": river, "forest": forest, "night": night, "cave": cave,
    "footsteps": footsteps, "heartbeat": heartbeat, "tension": tension,
    "magic": magic, "city": city, "crowd": crowd, "creak": creak,
    "spaceship": spaceship, "clock": clock,
}
SOUND_TYPES = list(GENERATORS)


def render(sound_type: str, seconds: float, seed: int = 7):
    """Devuelve (audio float32 en [-1,1], frecuencia de muestreo) como bucle sin costura."""
    fn = GENERATORS.get(sound_type, tension)
    rng = np.random.default_rng(seed)
    n = int(max(8.0, seconds) * SR)
    x = fn(n, SR, rng)
    x = make_loop(x, SR, 1.0)
    peak = np.max(np.abs(x))
    x = x / peak * 0.8 if peak > 0 else x
    return x.astype(np.float32), SR
