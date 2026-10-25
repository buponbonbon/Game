"""Register image-generated animation sheets without modifying source PNG pixels.

Authoring only: python tools/register_motion.py paths.json (requires Pillow).
The game and preservation generator do not need Pillow or image generation.
"""

from pathlib import Path
import sys, json, shutil, hashlib


def principal_bounds(alpha):
    """Read alpha connectivity to ignore fragments from neighboring sheet cells.

    This produces source-coordinate metadata only; source pixels are untouched.
    """
    width, height = alpha.size
    data = alpha.tobytes()
    parents = []
    runs = []
    previous = []

    def root(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    for y in range(height):
        active = []
        x = 0
        while x < width:
            if data[y * width + x] < 128:
                x += 1
                continue
            left = x
            while x < width and data[y * width + x] >= 128:
                x += 1
            right = x
            index = len(parents)
            parents.append(index)
            runs.append((index, left, right, y))
            active.append((left, right, index))
            for pl, pr, pi in previous:
                if pl > right:
                    break
                if pr >= left:
                    parents[root(index)] = root(pi)
        previous = active
    groups = {}
    for index, left, right, y in runs:
        key = root(index)
        if key not in groups:
            groups[key] = [0, left, y, right, y + 1]
        g = groups[key]
        g[0] += right - left
        g[1] = min(g[1], left)
        g[2] = min(g[2], y)
        g[3] = max(g[3], right)
        g[4] = max(g[4], y + 1)
    if not groups:
        return None
    main = max(groups.values(), key=lambda g: g[0])
    selected = [main]
    for g in groups.values():
        if g is main:
            continue
        if (
            g[0] >= main[0] * 0.1
            and g[4] - g[2] >= height * 0.12
            and g[3] >= main[1] - 30
            and g[1] <= main[3] + 30
            and g[4] >= main[2] - 20
            and g[2] <= main[4] + 20
        ):
            selected.append(g)
    return (
        max(0, min(g[1] for g in selected) - 1),
        max(0, min(g[2] for g in selected) - 1),
        min(width, max(g[3] for g in selected) + 1),
        min(height, max(g[4] for g in selected) + 1),
    )


def register(paths, out):
    from PIL import Image

    heroes = {
        "gatherer",
        "sword",
        "fire",
        "frost",
        "monk",
        "lightning",
        "herbalist",
        "formation",
    }
    out.mkdir(parents=True, exist_ok=True)
    atlas = {}
    for id, source in paths.items():
        source = Path(source)
        target = out / (id + ".png")
        if source.resolve() != target.resolve():
            shutil.copyfile(source, target)
        im = Image.open(source)
        alpha = im.getchannel("A")
        frames = []
        for index in range(16):
            col, row = index % 4, index // 4
            x0 = round(col * im.width / 4)
            x1 = round((col + 1) * im.width / 4)
            y0 = round(row * im.height / 4)
            y1 = round((row + 1) * im.height / 4)
            box = principal_bounds(alpha.crop((x0, y0, x1, y1)))
            if not box:
                raise ValueError(f"Missing frame {id}/{index}")
            l, t, r, b = box
            frames.append(dict(x=x0 + l, y=y0 + t, w=r - l, h=b - t, dx=l, dy=t))
        states = (
            dict(
                idle=[frames[0]],
                hurt=[frames[1]],
                death=frames[2:4],
                attack=frames[4:8],
                skill=frames[8:12],
                ultimate=frames[12:16],
            )
            if id in heroes
            else dict(
                walk=frames[:4],
                attack=frames[4:8],
                skill=frames[8:12],
                idle=[frames[12]],
                hurt=[frames[13]],
                death=frames[14:16],
            )
        )
        atlas[id] = dict(
            width=im.width,
            height=im.height,
            cell_w=im.width / 4,
            cell_h=im.height / 4,
            sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            states=states,
        )
    (out / "motion.json").write_text(json.dumps(atlas, indent=2) + "\n")
    print(
        f"Registered {len(atlas)} actors / {len(atlas)*16} source frames without editing PNGs."
    )
    return atlas


if __name__ == "__main__":
    register(
        json.loads(Path(sys.argv[1]).read_text()),
        Path(__file__).resolve().parents[1] / "web/assets/motion",
    )
