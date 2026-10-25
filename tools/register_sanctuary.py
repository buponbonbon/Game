"""Authoring only: register unchanged generated PNG sources (requires Pillow)."""

import hashlib
import json
from pathlib import Path
import shutil
import sys
import statistics
from register_motion import principal_bounds


def register(paths, target):
    from PIL import Image

    target.mkdir(parents=True, exist_ok=True)
    atlas = dict(sources={}, npcs={}, avatars={}, decor={}, icons={})
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
        if source.resolve() != (target / (name + ".png")).resolve():
            shutil.copyfile(source, target / (name + ".png"))
        im = Image.open(source)
        atlas["sources"][name] = dict(
            width=im.width,
            height=im.height,
            sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        )
        if name in ("scene", "cartography"):
            continue
        alpha = im.getchannel("A")
        cols, rows = (
            (4, 2)
            if name == "npcs"
            else (
                (3, 1)
                if name == "decor"
                else (4, 4) if name.startswith("idle_") or name == "icons" else (8, 4)
            )
        )
        frames = []
        for i in range(cols * rows):
            x, y = round(i % cols * im.width / cols), round(
                i // cols * im.height / rows
            )
            right, bottom = round((i % cols + 1) * im.width / cols), round(
                (i // cols + 1) * im.height / rows
            )
            if name == "icons":
                # Measured transparent gutters in this authored source, not pixel edits.
                xb, yb = [0, 380, 680, 980, im.width], [0, 304, 585, 857, im.height]
                x, right = xb[i % 4 : i % 4 + 2]
                y, bottom = yb[i // 4 : i // 4 + 2]
            box = principal_bounds(alpha.crop((x, y, right, bottom)))
            if box is None:
                raise ValueError((name, i))
            l, t, r, b = box
            # Register feet from source alpha only; source pixels are unchanged.
            pixels = alpha.load()
            foot = []
            for fy in range(y + t + round((b - t) * 0.88), y + b):
                for fx in range(x + l, x + r):
                    if pixels[fx, fy] > 190:
                        foot.append(fx - (x + l))
            anchor_x = statistics.mean(foot) if foot else (r - l) / 2
            frames.append(
                dict(
                    x=x + l,
                    y=y + t,
                    w=r - l,
                    h=b - t,
                    dx=l,
                    dy=t,
                    anchor_x=round(anchor_x, 3),
                    anchor_y=b - t,
                )
            )
        if name == "npcs":
            atlas["npcs"] = dict(zip(ids, frames))
        elif name == "icons":
            atlas["icons"] = dict(
                zip(
                    [
                        "campaign",
                        "garden",
                        "alchemy",
                        "training",
                        "archive",
                        "merchant",
                        "missions",
                        "trials",
                        "saves",
                        "map",
                        "settings",
                        "avatar",
                        "stone",
                        "insight",
                        "plus",
                        "minus",
                    ],
                    frames,
                )
            )
        elif name == "decor":
            atlas["decor"] = dict(zip(["lantern", "chimes", "banner"], frames))
        else:
            metadata = dict(
                width=im.width,
                height=im.height,
                cell_w=im.width / cols,
                cell_h=im.height / 4,
                body_height=statistics.median(f["h"] for f in frames),
                states={
                    d: (
                        [frames[i * cols]]
                        if name.startswith("idle_")
                        else frames[i * cols : i * cols + cols]
                    )
                    for i, d in enumerate(["south", "west", "east", "north"])
                },
            )
            if name.startswith("idle_"):
                atlas["avatars"].setdefault(name[5:], {})["idle"] = metadata
            else:
                atlas["avatars"].setdefault(name, {}).update(metadata)
    (target / "atlas.json").write_text(json.dumps(atlas, indent=2) + "\n")
    return atlas


if __name__ == "__main__":
    register(
        json.loads(Path(sys.argv[1]).read_text()),
        Path(__file__).resolve().parents[1] / "web/assets/hub",
    )
