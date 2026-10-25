"""Author original Chinese-inspired offline scores (optional NumPy + soundfile + ffmpeg).

Guqin/guzheng/pipa timbres use damped inharmonic string partials, pitch bends,
and transient plucks; dizi uses breath and vibrato. No sampled commercial music.
"""

from pathlib import Path
import json, subprocess, tempfile


def main():
    import numpy as np
    import soundfile as sf

    rate = 24000
    out = Path(__file__).resolve().parents[1] / "web/assets/audio/music"
    out.mkdir(parents=True, exist_ok=True)
    scores = {
        "lobby": (
            50,
            [0, 3, 5, 7, 10],
            [7, 4, 2, 0, 1, 2, 4, 3, 2, 1, 0, 2, 3, 4, 2, 0],
        ),
        "wharf_1": (
            50,
            [0, 2, 4, 7, 9],
            [0, 2, 4, 5, 4, 2, 1, 0, 2, 3, 4, 7, 5, 4, 2, 1],
        ),
        "wharf_2": (
            48,
            [0, 3, 5, 7, 10],
            [4, 1, 0, 2, 3, 5, 4, 2, 1, 3, 2, 0, 4, 7, 5, 3],
        ),
        "wharf_3": (
            46,
            [0, 2, 5, 7, 9],
            [0, 0, 4, 3, 5, 4, 7, 5, 2, 4, 1, 0, 3, 5, 4, 0],
        ),
        "terrace_1": (
            55,
            [0, 2, 4, 7, 9],
            [0, 2, 4, 7, 5, 4, 2, 1, 2, 4, 5, 7, 9, 7, 4, 2],
        ),
        "terrace_2": (
            57,
            [0, 2, 5, 7, 9],
            [7, 4, 5, 2, 4, 0, 2, 1, 5, 7, 4, 2, 3, 4, 1, 0],
        ),
        "terrace_3": (
            51,
            [0, 3, 5, 7, 10],
            [0, 3, 4, 0, 2, 5, 7, 4, 3, 1, 5, 2, 7, 5, 3, 0],
        ),
        "tomb_1": (
            45,
            [0, 3, 5, 7, 10],
            [0, 1, 4, 5, 3, 2, 1, 0, 2, 3, 1, 0, -1, 0, 2, 1],
        ),
        "tomb_2": (
            43,
            [0, 2, 3, 7, 10],
            [0, -1, 2, 1, 4, 3, 0, 2, 5, 2, 1, -2, 0, 3, 1, 0],
        ),
        "tomb_3": (
            42,
            [0, 3, 5, 7, 10],
            [0, 0, 3, 4, 1, 0, 5, 3, 2, 4, 0, 1, 7, 4, 3, 0],
        ),
    }
    titles = [
        "Sanctuary of Returning Breath",
        "Lanterns over Still Water",
        "The Drowned Ferry",
        "River King's Vow",
        "Jade Garden at Dawn",
        "Wings across the Clouds",
        "Granite Heart",
        "Unmarked Souls",
        "Procession of Coffins",
        "The Crown Must Fall",
    ]
    manifest = {
        "style": "Original Chinese-inspired guqin / guzheng / pipa / dizi and percussion arrangements",
        "tracks": {},
    }
    for theme_index, (theme, (root, scale, melody)) in enumerate(scores.items()):
        region = theme.split("_")[0]
        variation = (theme_index - 1) % 3 if theme_index else 0
        for phase in (
            ["setup"] if region == "lobby" else ["setup", "pressure", "onslaught"]
        ):
            intensity = {"setup": 0, "pressure": 1, "onslaught": 2}[phase]
            bpm = (
                70
                if region == "lobby"
                else {"wharf": 80, "terrace": 76, "tomb": 70}[region] + variation * 5
            ) + intensity * 19
            beat = 60 / bpm
            duration = beat * 64
            audio = np.zeros((round(duration * rate), 2), np.float64)
            rng = np.random.default_rng(831 + theme_index * 31 + intensity)

            def hz(degree, octave=0):
                n = root + scale[degree % 5] + 12 * (degree // 5 + octave)
                return 440 * 2 ** ((n - 69) / 12)

            def add(start, freq, length, vol, instrument="guqin", pan=0):
                count = round(length * rate)
                t = np.arange(count) / rate
                if instrument in ("guqin", "guzheng", "pipa"):
                    decay = {"guqin": 1.25, "guzheng": 1.7, "pipa": 4.0}[instrument]
                    harmonics = 10 if instrument == "guzheng" else 8
                    wave = np.zeros(count)
                    bend = 1 + (0.0015 if instrument == "guqin" else 0.003) * np.exp(
                        -t * 16
                    )
                    for harmonic in range(1, harmonics + 1):
                        phasev = (
                            2
                            * np.pi
                            * freq
                            * harmonic
                            * (1 + 0.0001 * harmonic**2)
                            * t
                            * bend
                        )
                        wave += (
                            np.sin(phasev)
                            / (harmonic ** (1.4 if instrument == "guzheng" else 1.8))
                            * np.exp(-t * (decay + harmonic * 0.28))
                        )
                    wave += rng.normal(0, 0.06, count) * np.exp(-t * 160)
                    wave *= np.minimum(t * 180, 1)
                elif instrument == "dizi":
                    phasev = 2 * np.pi * freq * t + 0.035 * np.sin(2 * np.pi * 5.2 * t)
                    wave = (
                        (
                            np.sin(phasev)
                            + 0.3 * np.sin(phasev * 2)
                            + 0.12 * np.sin(phasev * 3)
                            + rng.normal(0, 0.035, count)
                        )
                        * np.minimum(t * 15, 1)
                        * np.minimum((length - t) * 12, 1)
                        * np.exp(-t * 0.6)
                    )
                elif instrument == "gong":
                    wave = sum(
                        np.sin(2 * np.pi * freq * r * t)
                        * np.exp(-t * (1.8 + i * 0.6))
                        / (i + 1)
                        for i, r in enumerate([1, 1.43, 1.88, 2.37, 2.91])
                    )
                else:
                    wave = np.sin(
                        2 * np.pi * (freq * t + freq * 0.016 * (1 - np.exp(-t * 25)))
                    ) * np.exp(-t * 18) + rng.normal(0, 0.1, count) * np.exp(-t * 35)
                start = round(start * rate)
                indices = (np.arange(count) + start) % len(audio)
                for ch, gain in enumerate(
                    [1 - max(0, pan) * 0.6, 1 + min(0, pan) * 0.6]
                ):
                    np.add.at(audio[:, ch], indices, wave * vol * gain)

            for bar in range(16):
                harmony = ([0, 3, 4, 0], [0, 4, 2, 3], [0, 2, 4, 3])[variation][
                    bar // 4
                ]
                add(bar * 4 * beat, hz(harmony, -1), beat * 5, 0.17, "guqin", -0.2)
                for n in range(4):
                    degree = melody[(bar * 2 + n // 2) % len(melody)] + (
                        5 if bar >= 8 and bar % 2 else 0
                    )
                    if region == "lobby" and n % 2:
                        continue
                    add(
                        (bar * 4 + n) * beat,
                        hz(degree),
                        beat * 2.4,
                        0.16 if intensity == 0 else 0.13,
                        "guqin" if intensity == 0 else "guzheng",
                        -0.3,
                    )
                    if n % 2 == 0:
                        add(
                            (bar * 4 + n + 0.5) * beat,
                            hz(harmony + (2 if n else 4)),
                            beat * 1.7,
                            0.07,
                            "guzheng",
                            0.4,
                        )
                if bar % 4 == 2 or intensity >= 1:
                    add(
                        (bar * 4 + 1) * beat,
                        hz(melody[(bar * 2) % 16], 1),
                        beat * 1.6,
                        0.045,
                        "dizi",
                        0.3,
                    )
                if intensity >= 1:
                    for n in (0, 2, 3.5):
                        add((bar * 4 + n) * beat, 82, beat * 0.65, 0.13, "drum")
                    for n in range(8):
                        add(
                            (bar * 4 + n * 0.5) * beat,
                            hz(harmony + [0, 2, 4, 2][n % 4]),
                            beat * 0.8,
                            0.055,
                            "pipa",
                            0.4,
                        )
                if intensity == 2:
                    for n in range(16):
                        add(
                            (bar * 4 + n * 0.25) * beat,
                            hz(melody[(bar * 2) % 16] + (5 if n % 2 else 0)),
                            beat * 0.7,
                            0.025,
                            "pipa",
                            -0.4,
                        )
                    if bar % 4 == 0:
                        add(bar * 4 * beat, 110, beat * 3, 0.075, "gong")
            audio = np.tanh(audio * 1.4)
            peak = np.max(np.abs(audio))
            audio *= 0.88 / max(peak, 1e-6)
            name = theme + "_" + phase
            with tempfile.TemporaryDirectory() as tmp:
                wav = Path(tmp) / "track.wav"
                sf.write(wav, audio, rate)
                for ext, codec, bitrate in [
                    ("ogg", "libvorbis", "112k"),
                    ("mp3", "libmp3lame", "128k"),
                ]:
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-hide_banner",
                            "-loglevel",
                            "error",
                            "-nostdin",
                            "-y",
                            "-i",
                            str(wav),
                            "-c:a",
                            codec,
                            "-b:a",
                            bitrate,
                            str(out / (name + "." + ext)),
                        ],
                        check=True,
                    )
            manifest["tracks"][name] = {
                "ogg": name + ".ogg",
                "mp3": name + ".mp3",
                "bpm": bpm,
                "title": titles[theme_index],
                "theme": theme,
                "melody": melody,
                "intensity": intensity,
                "duration": round(duration, 5),
                "instruments": ["guqin", "guzheng", "dizi"]
                + (["pipa", "Chinese drum"] if intensity else [])
                + (["gong"] if intensity == 2 else []),
            }
            print(name, bpm, round(duration, 2), flush=True)
    (out / "music.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (out / "NOTICE.txt").write_text(
        "Original VAN DAO compositions and physically inspired synthesized instruments.\nNo copyrighted songs or third-party recordings sampled.\nStyles evoke guqin, guzheng, pipa, dizi and Chinese percussion; these are not acoustic instrument recordings.\n"
    )


if __name__ == "__main__":
    main()
