"""Authoring only: register unchanged generated PNG sources (requires Pillow)."""

import hashlib
import json
from pathlib import Path
import shutil
import sys
from register_motion import principal_bounds


def register(paths, target):
    from PIL import Image

    target.mkdir(parents=True, exist_ok=True)
    atlas = dict(sources={}, npcs={}, avatars={}, decor={})
    ids = [
        "gatherer",
        "sword",
        "fire",
        "frost",
        "monk",
        "lightning",
        "herbalist",
        "formation",
    ]
    for name, source in paths.items():
        source = Path(source)
        shutil.copyfile(source, target / (name + ".png"))
        im = Image.open(source)
        atlas["sources"][name] = dict(
            width=im.width,
            height=im.height,
            sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        )
        if name == "scene":
            continue
        alpha = im.getchannel("A")
        cols, rows = (4, 2) if name == "npcs" else (3, 1) if name == "decor" else (4, 4)
        frames = []
        for i in range(cols * rows):
            x, y = round(i % cols * im.width / cols), round(
                i // cols * im.height / rows
            )
            right, bottom = round((i % cols + 1) * im.width / cols), round(
                (i // cols + 1) * im.height / rows
            )
            box = principal_bounds(alpha.crop((x, y, right, bottom)))
            if box is None:
                raise ValueError((name, i))
            l, t, r, b = box
            frames.append(dict(x=x + l, y=y + t, w=r - l, h=b - t, dx=l, dy=t))
        if name == "npcs":
            atlas["npcs"] = dict(zip(ids, frames))
        elif name == "decor":
            atlas["decor"] = dict(zip(["lantern", "chimes", "banner"], frames))
        else:
            atlas["avatars"][name] = dict(
                width=im.width,
                height=im.height,
                cell_w=im.width / 4,
                cell_h=im.height / 4,
                states={
                    d: frames[i * 4 : i * 4 + 4]
                    for i, d in enumerate(["south", "west", "east", "north"])
                },
            )
    (target / "atlas.json").write_text(json.dumps(atlas, indent=2) + "\n")
    return atlas


if __name__ == "__main__":
    register(
        json.loads(Path(sys.argv[1]).read_text()),
        Path(__file__).resolve().parents[1] / "web/assets/hub",
    )
