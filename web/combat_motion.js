/* Authored frame playback and precise threat diagrams. No combat rules live here. */
window.VanDaoMotion = (() => {
  const bitmaps = new Map(),
    pending = new Map(),
    observed = new Map();
  function load(id, meta) {
    if (bitmaps.has(id) || pending.has(id) || !meta) return;
    const task = fetch("/assets/motion/" + id + ".png")
      .then((r) => {
        if (!r.ok) throw Error("Animation unavailable");
        return r.blob();
      })
      .then(async (blob) => {
        if (typeof createImageBitmap === "function")
          return createImageBitmap(blob, {
            resizeWidth: Math.min(768, meta.width),
            resizeHeight: Math.round(
              meta.height * Math.min(1, 768 / meta.width),
            ),
            resizeQuality: "high",
          });
        const image = new Image(),
          url = URL.createObjectURL(blob);
        await new Promise((resolve, reject) => {
          image.onload = resolve;
          image.onerror = reject;
          image.src = url;
        });
        URL.revokeObjectURL(url);
        return image;
      })
      .then((bitmap) => bitmaps.set(id, bitmap))
      .catch(() => null);
    pending.set(id, task);
  }
  function frame(meta, action, elapsed, duration, clock, windup) {
    const key =
      action === "walk"
        ? "walk"
        : action === "death"
          ? "death"
          : action === "hurt"
            ? "hurt"
            : action === "ultimate"
              ? "ultimate"
              : [
                    "skill",
                    "deploy",
                    "ability",
                    "channel",
                    "phase",
                    "mend",
                  ].includes(action)
                ? "skill"
                : action === "attack"
                  ? "attack"
                  : "idle";
    const frames = meta.states[key] || meta.states.idle || meta.states.walk;
    let index = 0;
    if (key === "walk") index = Math.floor(clock * 8) % frames.length;
    else if (key === "attack")
      index =
        elapsed < windup
          ? 0
          : elapsed < windup + 0.075
            ? 1
            : elapsed < windup + 0.17
              ? 2
              : 3;
    else if (frames.length > 1)
      index = Math.min(
        frames.length - 1,
        Math.floor(
          (Math.max(0, elapsed) / Math.max(0.001, duration)) * frames.length,
        ),
      );
    return {
      key,
      index: Math.min(index, frames.length - 1),
      source: frames[Math.min(index, frames.length - 1)],
    };
  }
  function draw(
    c,
    id,
    meta,
    x,
    y,
    size,
    action,
    clock,
    started,
    until,
    windup,
    alpha = 1,
  ) {
    if (!meta) return false;
    load(id, meta);
    const bitmap = bitmaps.get(id);
    if (!bitmap) return false;
    const f = frame(
        meta,
        action,
        clock - started,
        until - started,
        clock,
        windup,
      ),
      r = f.source,
      s = bitmap.width / meta.width;
    const factor = size / (meta.cell_h * 0.88),
      foot = meta.cell_h * 0.94;
    c.save();
    c.globalAlpha = alpha;
    c.drawImage(
      bitmap,
      r.x * s,
      r.y * s,
      r.w * s,
      r.h * s,
      x + (r.dx - meta.cell_w / 2) * factor,
      y + (r.dy - foot) * factor,
      r.w * factor,
      r.h * factor,
    );
    c.restore();
    const key = id + ":" + f.key;
    if (!observed.has(key)) observed.set(key, new Set());
    observed.get(key).add(f.index);
    return true;
  }
  function threats(c, s, B, front = false) {
    c.save();
    c.beginPath();
    c.rect(B.x + B.cw, B.y, 9 * B.cw, 5 * B.ch);
    c.clip();
    for (const t of s.telegraphs || []) {
      const support = t.kind === "MENDING CHANT",
        color = support ? "#9ce9af" : "#ffd285",
        edge = support ? "#84edab" : "#ffaf80",
        duration = t.duration || 2;
      c.strokeStyle = edge;
      c.fillStyle = support ? "#87d4a51c" : "#dc644c20";
      c.lineWidth = front ? 1.2 : 1;
      const x = B.x + (t.x || 0) * B.cw,
        y = B.y + ((t.lanes?.[0] ?? 2) + 0.5) * B.ch;
      if (t.shape === "circle") {
        c.beginPath();
        c.ellipse(x, y, t.radius * B.cw, t.radius * B.ch, 0, 0, Math.PI * 2);
        front ? c.stroke() : c.fill();
      } else if (t.shape === "segment") {
        const radius = (t.radius || 0.75) * B.cw;
        front
          ? c.strokeRect(x - radius, y - 14, radius * 2, 28)
          : c.fillRect(x - radius, y - 14, radius * 2, 28);
      } else
        for (const lane of t.lanes) {
          const yy = B.y + lane * B.ch;
          if (front) {
            c.strokeRect(B.x + B.cw + 1, yy + 1, 9 * B.cw - 2, B.ch - 2);
            for (let col = 1; col <= 9; col++) {
              c.beginPath();
              c.moveTo(B.x + col * B.cw + 3, yy + 27);
              c.lineTo(B.x + col * B.cw + 11, yy + 20);
              c.stroke();
            }
          } else c.fillRect(B.x + B.cw, yy, 9 * B.cw, B.ch);
        }
      if (front) {
        const bx = Math.max(
            B.x + B.cw + 2,
            Math.min(B.x + 9 * B.cw - 100, t.x ? x - 36 : B.x + B.cw + 5),
          ),
          by = Math.max(B.y + 1, Math.min(B.y + 4 * B.ch, y - 14));
        c.fillStyle = "#111e2af5";
        c.fillRect(bx, by, 100, 13);
        c.fillStyle = color;
        c.font = "10px VT323";
        c.textAlign = "left";
        c.textBaseline = "top";
        const label = support
          ? "INTERRUPT"
          : t.kind === "SPORE CLOUD"
            ? "SPORES"
            : t.kind === "SHOULDER RUSH"
              ? "RUSH"
              : "SHIELD";
        c.fillText(
          label + " " + Math.max(0, t.ttl).toFixed(1) + "s",
          bx + 4,
          by + 2,
        );
        c.fillStyle = edge;
        c.fillRect(bx, by + 12, 100 * Math.min(1, t.ttl / duration), 1);
      }
    }
    c.restore();
  }
  function bars(c, u, x, y, size, selected, hover, smart) {
    const hp = Math.max(0, Math.min(1, u.hp / u.max_hp)),
      show =
        !smart ||
        (u.friendly && u.mana / u.mana_max < 0.3) ||
        u.boss ||
        u.squad_role ||
        hp < 0.999 ||
        selected ||
        hover;
    if (!show) return;
    const by = y - size - 5,
      w = u.friendly ? 22 : 20;
    c.fillStyle = "#08131e";
    c.fillRect(x - w / 2 - 1, by - 1, w + 2, u.friendly ? 7 : 5);
    c.fillStyle = u.friendly ? "#9ee5cf" : "#ffa583";
    c.fillRect(x - w / 2, by, w * hp, 2);
    if (u.shield > 0) {
      c.fillStyle = "#b8d9ff";
      c.fillRect(x - w / 2, by + 2, w * Math.min(1, u.shield / u.max_hp), 1);
    }
    if (u.friendly) {
      c.fillStyle = "#a4cfee";
      c.fillRect(x - w / 2, by + 4, w * Math.min(1, u.mana / u.mana_max), 1);
    }
    if (u.squad_role) {
      c.fillStyle =
        u.squad_role === "guard"
          ? "#9dcfe9"
          : u.squad_role === "mender"
            ? "#a0e8b8"
            : "#f1c27e";
      c.font = "9px VT323";
      c.textAlign = "center";
      c.textBaseline = "top";
      c.fillText(
        { guard: "G", mender: "M", striker: "S" }[u.squad_role],
        x + 14,
        by - 1,
      );
    }
  }
  return {
    load,
    draw,
    frame,
    threats,
    bars,
    get loaded() {
      return [...bitmaps.keys()];
    },
    get observed() {
      return Object.fromEntries([...observed].map(([k, v]) => [k, [...v]]));
    },
  };
})();
