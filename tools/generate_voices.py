"""Optional asset-authoring tool; the game itself needs none of these packages.

Requires kokoro-onnx 0.6.1, soundfile 0.13.1 and ffmpeg. Model downloads are
explicit local inputs; no network or speech synthesis occurs during gameplay.
"""

from pathlib import Path
import argparse, hashlib, json, subprocess, tempfile

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from game.performances import PERFORMANCES

EXPECTED = {
    "kokoro-v1.0.onnx": "beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a",
    "voices-v1.0.bin": "bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "web/assets/audio/voices",
    )
    parser.add_argument(
        "--heroes",
        nargs="+",
        choices=list(PERFORMANCES),
        help="Regenerate only selected voices, preserving other committed takes.",
    )
    args = parser.parse_args()
    import onnxruntime as ort
    import numpy as np
    import soundfile as sf
    from kokoro_onnx import Kokoro

    for name, checksum in EXPECTED.items():
        assert (
            hashlib.sha256((args.models / name).read_bytes()).hexdigest() == checksum
        ), name
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    options.log_severity_level = 3
    session = ort.InferenceSession(
        str(args.models / "kokoro-v1.0.onnx"),
        sess_options=options,
        providers=["CPUExecutionProvider"],
    )
    kokoro = Kokoro.from_session(session, str(args.models / "voices-v1.0.bin"))
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "language": "en",
        "synthesis": "Kokoro-82M v1.0, Apache-2.0 model, generated fictional character dialogue",
        "characters": {},
    }
    if args.heroes and (args.output / "voices.json").exists():
        manifest = json.loads((args.output / "voices.json").read_text())
    with tempfile.TemporaryDirectory() as tmp:
        for hero, (voice, accent, summon, ultimate, direction) in PERFORMANCES.items():
            if args.heroes and hero not in args.heroes:
                continue
            entries = {}
            for action, text in [("summon", summon), ("ultimate", ultimate)]:
                pieces = []
                for phrase, pace, energy, pause in text:
                    style = (
                        kokoro.get_voice_style(voice) * 0.82
                        + kokoro.get_voice_style(accent) * 0.18
                    )
                    pcm, rate = kokoro.create(
                        phrase,
                        voice=style,
                        speed=pace,
                        lang="en-gb" if voice.startswith("b") else "en-us",
                        sentence_pause=0.12,
                        clause_pause=0.06,
                    )
                    pcm = pcm * energy
                    # The last phrase builds in energy instead of a flat, constant gain.
                    pcm = pcm * np.linspace(0.91, 1.08, len(pcm))
                    pieces.extend([pcm, np.zeros(round(pause * rate), np.float32)])
                audio = np.concatenate(pieces)
                spoken = " ".join(p[0] for p in text)
                audio = np.nan_to_num(audio)
                peak = float(np.max(np.abs(audio)))
                if peak > 0:
                    audio = audio * 0.86 / max(peak, 0.01)
                assert len(audio) > rate * 0.4 and np.std(audio) > 0.01
                wav = Path(tmp) / (hero + "_" + action + ".wav")
                sf.write(wav, audio, rate)
                name = hero + "_" + action + ".mp3"
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
                        "-af",
                        (
                            "acompressor=threshold=0.28:ratio=2:attack=8:release=90,treble=g=2,aecho=0.8:0.35:48:0.10"
                            if action == "ultimate"
                            else "acompressor=threshold=0.35:ratio=1.5:attack=12:release=100"
                        ),
                        "-c:a",
                        "libmp3lame",
                        "-b:a",
                        "112k",
                        str(args.output / name),
                    ],
                    check=True,
                )
                entries[action] = {
                    "file": name,
                    "text": spoken,
                    "direction": direction,
                    "phrases": [
                        dict(text=p[0], pace=p[1], energy=p[2], pause=p[3])
                        for p in text
                    ],
                    "duration": round(len(audio) / rate, 3),
                    "voice": voice,
                }
                print(hero, action, entries[action]["duration"], flush=True)
            manifest["characters"][hero] = entries
    (args.output / "voices.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (args.output / "NOTICE.txt").write_text(
        "Original English dialogue synthesized for fictional VAN DAO characters.\nKokoro-82M model: Apache-2.0, hexgrad/Kokoro-82M.\nONNX conversion/runtime: thewh1teagle/kokoro-onnx (MIT).\nNo actor recording or real-person imitation is claimed. Audio is bundled for offline playback.\n"
    )


if __name__ == "__main__":
    main()
