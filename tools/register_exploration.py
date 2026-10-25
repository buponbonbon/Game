"""Register original exploration source artwork without changing PNG pixels (Pillow authoring only)."""

from pathlib import Path
import hashlib, json, shutil, statistics, sys
from register_motion import principal_bounds

ROOT = Path(__file__).resolve().parents[1]
DIRECTIONS = [
    "south",
    "southwest",
    "west",
    "northwest",
    "north",
    "northeast",
    "east",
    "southeast",
]


def source(path, target):
    from PIL import Image

    path = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if path.resolve() != target.resolve():
        shutil.copyfile(path, target)
    im = Image.open(path)
    return im, dict(
        width=im.width,
        height=im.height,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def cuts(alpha, count, axis):
    width, height = alpha.size
    pixels = alpha.load()
    length = width if axis == "x" else height
    counts = [
        (
            sum(pixels[t, y] > 128 for y in range(height))
            if axis == "x"
            else sum(pixels[x, t] > 128 for x in range(width))
        )
        for t in range(length)
    ]
    result = [0]
    for i in range(1, count):
        ideal = length * i / count
        radius = length / count * 0.16
        candidates = range(
            max(result[-1] + 1, round(ideal - radius)),
            min(length, round(ideal + radius)),
        )
        result.append(min(candidates, key=lambda n: counts[n] + abs(n - ideal) * 0.35))
    return result + [length]


def frames(im, cols, rows, ybounds=None):
    alpha = im.getchannel("A")
    xb = cuts(alpha, cols, "x")
    yb = ybounds or cuts(alpha, rows, "y")
    pixels = alpha.load()
    result = []
    for row in range(rows):
        for col in range(cols):
            x, y, r, b = xb[col], yb[row], xb[col + 1], yb[row + 1]
            box = principal_bounds(alpha.crop((x, y, r, b)))
            if not box:
                raise ValueError(f"Missing frame {col}/{row}")
            l, t, rr, bb = box
            foot = []
            for yy in range(y + t + round((bb - t) * 0.89), y + bb):
                for xx in range(x + l, x + rr):
                    if pixels[xx, yy] > 190:
                        foot.append(xx - (x + l))
            result.append(
                dict(
                    x=x + l,
                    y=y + t,
                    w=rr - l,
                    h=bb - t,
                    dx=l,
                    dy=t,
                    anchor_x=round(statistics.mean(foot), 3) if foot else (rr - l) / 2,
                    anchor_y=bb - t,
                )
            )
    return result


def register(paths):
    target = ROOT / "web/assets/exploration"
    target.mkdir(parents=True, exist_ok=True)
    art = dict(sources={}, npcs={}, props={}, actions={})
    for name in ["campaign_map", "npcs", "props", "actions"]:
        im, info = source(paths[name], target / (name + ".png"))
        art["sources"][name] = info
        if name == "campaign_map":
            continue
        if name == "npcs":
            art["npcs"] = dict(
                zip(["mei", "tao", "qiao", "lin", "suyin", "ren"], frames(im, 3, 2))
            )
        elif name == "props":
            art["props"] = dict(
                zip(
                    [
                        "bed",
                        "wet_bed",
                        "overgrown",
                        "trellis",
                        "watering_can",
                        "hoe",
                        "seeds",
                        "harvest",
                        "flower",
                        "grass",
                        "chime",
                        "spring",
                    ],
                    frames(im, 4, 3),
                )
            )
        else:
            poses = frames(im, 8, 6, [0, 210, 417, 602, 783, 945, im.height])
            for index, id in enumerate(["sword", "gatherer", "herbalist"]):
                f = poses[index * 16 : index * 16 + 16]
                art["actions"][id] = dict(
                    width=im.width,
                    height=im.height,
                    body_height=max(v["h"] for v in f),
                    states=dict(
                        greet=f[:4], inspect=f[4:8], water=f[8:12], gather=f[12:16]
                    ),
                )
    (target / "exploration.json").write_text(json.dumps(art, indent=2) + "\n")
    folder = ROOT / "web/assets/hub"
    atlas = json.loads((folder / "atlas.json").read_text())
    atlas["extra_sources"] = {}
    for id in ["sword", "gatherer", "herbalist"]:
        im, info = source(paths["walk_" + id], folder / (id + ".png"))
        atlas["sources"][id] = info
        if id == "sword":
            f = frames(im, 8, 7, [0, 167, 329, 488, 653, 816, 992, 1176])
            states = dict(zip(DIRECTIONS[:7], [f[i * 8 : i * 8 + 8] for i in range(7)]))
        else:
            f = frames(im, 8, 8)
            states = dict(zip(DIRECTIONS, [f[i * 8 : i * 8 + 8] for i in range(8)]))
        idle = atlas["avatars"][id]["idle"]
        atlas["avatars"][id] = dict(
            width=im.width,
            height=im.height,
            cell_w=im.width / 8,
            cell_h=im.height / 8,
            body_height=statistics.median(v["h"] for v in f),
            states=states,
            idle=idle,
        )
    extra, info = source(paths["sword_southeast"], folder / "sword_southeast.png")
    atlas["sources"]["sword_southeast"] = info
    atlas["extra_sources"]["sword_southeast"] = info
    f = frames(extra, 8, 1)
    height = statistics.median(v["h"] for v in f)
    for v in f:
        v.update(source="sword_southeast", source_width=extra.width, body_height=height)
    atlas["avatars"]["sword"]["states"]["southeast"] = f
    idle_image, idle_info = source(
        paths["direction_idle"], folder / "direction_idle.png"
    )
    atlas["sources"]["direction_idle"] = idle_info
    atlas["extra_sources"]["direction_idle"] = idle_info
    idle_frames = frames(idle_image, 8, 3)
    for index, id in enumerate(["sword", "gatherer", "herbalist"]):
        poses = idle_frames[index * 8 : index * 8 + 8]
        atlas["avatars"][id]["idle"] = dict(
            source="direction_idle",
            width=idle_image.width,
            height=idle_image.height,
            body_height=statistics.median(v["h"] for v in poses),
            states={direction: [poses[i]] for i, direction in enumerate(DIRECTIONS)},
        )
        atlas["sources"].pop("idle_" + id, None)
        obsolete = folder / ("idle_" + id + ".png")
        if obsolete.exists():
            obsolete.unlink()
    (folder / "atlas.json").write_text(json.dumps(atlas, indent=2) + "\n")
    print(
        "Registered 3 x 64 directional walk frames, 48 interactions, 6 NPCs, 12 props and campaign map. Source PNGs unchanged."
    )


if __name__ == "__main__":
    register(json.loads(Path(sys.argv[1]).read_text()))
