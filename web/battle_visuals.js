/* Region diagrams and cast choreography; combat stays authoritative in Python. */
"use strict";
window.VanDaoBattleArt = (() => {
  const colors = {
    gatherer: "#83f2be",
    sword: "#e0ffe7",
    fire: "#ff874c",
    frost: "#a5edff",
    monk: "#ffd97a",
    lightning: "#d6bcff",
    herbalist: "#a5f48b",
    formation: "#f5d888",
  };
  function path(c, points, color, width = 1, close = false, fill = false) {
    c.beginPath();
    points.forEach(([x, y], i) =>
      i
        ? c.lineTo(Math.round(x), Math.round(y))
        : c.moveTo(Math.round(x), Math.round(y)),
    );
    if (close) c.closePath();
    c.strokeStyle = color;
    c.fillStyle = color;
    c.lineWidth = width;
    fill ? c.fill() : c.stroke();
  }
  function ring(c, x, y, r, color, squash = 0.45, phase = 0) {
    const p = [];
    for (let i = 0; i <= 24; i++) {
      const a = (i * Math.PI) / 12 + phase;
      p.push([x + Math.cos(a) * r, y + Math.sin(a) * r * squash]);
    }
    path(c, p, color);
  }
  function sword(c, x, y, angle, length, color) {
    const dx = Math.cos(angle),
      dy = Math.sin(angle);
    path(
      c,
      [
        [x, y],
        [x + dx * length, y + dy * length],
      ],
      "#18283a",
      4,
    );
    path(
      c,
      [
        [x, y],
        [x + dx * length, y + dy * length],
      ],
      color,
      2,
    );
    path(
      c,
      [
        [x - dy * 3, y + dx * 3],
        [x + dy * 3, y - dx * 3],
      ],
      "#e5bf74",
      2,
    );
  }
  function lotus(c, x, y, r, color, t) {
    for (let i = 0; i < 8; i++) {
      const a = (i * Math.PI) / 4 + t * 0.1;
      path(
        c,
        [
          [x, y],
          [x + Math.cos(a - 0.3) * r * 0.65, y + Math.sin(a - 0.3) * r * 0.48],
          [x + Math.cos(a) * r, y + Math.sin(a) * r * 0.65],
          [x + Math.cos(a + 0.3) * r * 0.65, y + Math.sin(a + 0.3) * r * 0.48],
        ],
        color,
        1,
        true,
      );
    }
    ring(c, x, y, r * 0.6, "#fff0bd");
  }
  function bolt(c, x, y, tx, ty, color, seed) {
    const p = [[x, y]];
    for (let i = 1; i < 8; i++)
      p.push([
        x + ((tx - x) * i) / 8 + Math.sin(i * 7 + seed) * 5,
        y + ((ty - y) * i) / 8,
      ]);
    p.push([tx, ty]);
    path(c, p, color, 3);
    path(c, p, "#effbff", 1);
  }
  function artifact(c, image, g, x, y, size, region, time, active = false) {
    if (!image || !g) return;
    c.save();
    const bob =
      region === "terrace"
        ? Math.sin(time * 3) * 2
        : region === "tomb"
          ? Math.sin(time * 2) * 0.6
          : Math.sin(time * 4) * 0.7;
    const width = (size * g.w) / Math.max(g.w, g.h),
      height = (size * g.h) / Math.max(g.w, g.h);
    c.globalAlpha = 0.6;
    ring(
      c,
      x,
      y + size * 0.34,
      size * 0.45,
      region === "tomb"
        ? "#5df3ce"
        : region === "wharf"
          ? "#f1b45f"
          : "#b8f8ff",
    );
    c.globalAlpha = 1;
    c.drawImage(
      image,
      g.x,
      g.y,
      g.w,
      g.h,
      Math.round(x - width / 2),
      Math.round(y - height / 2 + bob),
      width,
      height,
    );
    if (active || region === "terrace")
      for (let i = 0; i < 6; i++) {
        const a = time * 2 + (i * Math.PI) / 3;
        c.fillStyle = region === "wharf" ? "#ffe28c" : "#b5f7e5";
        c.fillRect(
          Math.round(x + Math.cos(a) * size * 0.45),
          Math.round(y + Math.sin(a) * size * 0.36),
          2,
          2,
        );
      }
    c.restore();
  }
  function effects(c, s, bursts, B, text, layer) {
    c.save();
    c.beginPath();
    c.rect(B.x, B.y, B.cw * 12, B.ch * 5);
    c.clip();
    for (const b of bursts) {
      const age = s.time - b.start;
      if (age < 0 || age > b.duration) continue;
      const ult = b.kind === "ultimate",
        x = B.x + b.x * B.cw,
        y = B.y + (b.lane + 0.65) * B.ch,
        t = age,
        p = age / b.duration,
        color = colors[b.hero];
      c.globalAlpha = Math.min(1, age * 8) * Math.min(1, (1 - p) * 4);
      if (layer === "floor") {
        ring(c, x, y, ult ? 24 + Math.sin(t * 5) * 3 : 15, color);
        if (ult) {
          ring(c, x, y, 30, "#fff2bf", 0.45, -t);
          for (let i = 0; i < 8; i++) {
            const a = (i * Math.PI) / 4 + t * 0.4;
            path(
              c,
              [
                [x + Math.cos(a) * 21, y + Math.sin(a) * 10],
                [x + Math.cos(a) * 29, y + Math.sin(a) * 14],
              ],
              color,
              2,
            );
          }
        }
        continue;
      }
      const targets = b.targets || [],
        allies = b.allies || [];
      const at = (u) => [B.x + u.x * B.cw, B.y + (u.lane + 0.6) * B.ch];
      if (b.hero === "gatherer") {
        for (let i = 0; i < (ult ? 16 : 7); i++) {
          const a = i * 2.4 + t * 2,
            r = 8 + (i % 4) * 4,
            h = (t * 24 + i * 6) % 55;
          c.fillStyle = i % 3 ? "#92efbc" : "#ffe68c";
          c.fillRect(
            Math.round(x + Math.cos(a) * r),
            Math.round(y - h),
            ult ? 3 : 2,
            3,
          );
        }
        if (ult) {
          ring(c, x, y, 34, color);
          path(
            c,
            [
              [x - 10, y],
              [x - 7, y - 38],
              [x, y - 55],
              [x + 7, y - 38],
              [x + 10, y],
            ],
            "#e8ffcb",
            1,
            true,
          );
          c.globalAlpha *= 0.4;
          path(
            c,
            [
              [x - 17, y],
              [x, y - 62],
              [x + 17, y],
            ],
            color,
            1,
            true,
          );
        }
      } else if (b.hero === "sword") {
        const n = ult ? 10 : 3;
        for (let i = 0; i < n; i++) {
          const f = (t * 1.4 + i / n) % 1,
            xx = x + f * (ult ? 235 : 95),
            yy = y - 10 + Math.sin(i * 2.3) * 9;
          path(
            c,
            [
              [xx - 25, yy],
              [xx - 4, yy],
            ],
            "#8de8d8",
            2,
          );
          sword(c, xx, yy, -0.06, ult ? 24 : 18, "#efffce");
        }
      } else if (b.hero === "fire") {
        if (ult && age > 0.65) {
          for (const u of targets.slice(0, 3)) {
            const [tx, ty] = at(u);
            lotus(c, tx, ty, 18 + Math.sin(t * 7) * 4, "#ff8752", t);
            for (let i = 0; i < 6; i++) {
              c.fillStyle = i % 2 ? "#ffb95e" : "#ff684e";
              c.fillRect(
                tx - 13 + i * 5,
                ty - 10 - Math.sin(t * 10 + i) * 12,
                3,
                8,
              );
            }
          }
        } else {
          lotus(c, x + 13, y - 12, ult ? 26 : 17, color, t);
          for (let i = 0; i < 7; i++) {
            const a = i * 0.9 + t * 3;
            c.fillStyle = "#ffd38b";
            c.fillRect(x + Math.cos(a) * 23, y - 15 + Math.sin(a) * 13, 3, 3);
          }
        }
      } else if (b.hero === "frost") {
        if (ult) {
          for (let i = 0; i < 12; i++) {
            const tx = B.x + i * 32 + 16;
            path(
              c,
              [
                [tx - 8, y],
                [tx - 4, y - 19 - (i % 3) * 5],
                [tx, y - 28],
                [tx + 6, y - 11],
                [tx + 8, y],
              ],
              i % 2 ? "#b7eaff" : "#e5fbff",
              1,
              true,
            );
          }
        } else
          for (const u of allies.slice(0, 2)) {
            const [tx, ty] = at(u);
            path(
              c,
              [
                [tx, ty - 30],
                [tx + 13, ty - 15],
                [tx + 8, ty + 2],
                [tx - 8, ty + 2],
                [tx - 13, ty - 15],
              ],
              "#b0f6ff",
              2,
              true,
            );
            ring(c, tx, ty, 17, color);
          }
      } else if (b.hero === "monk") {
        if (ult) {
          for (let i = 0; i < 4; i++)
            path(
              c,
              [
                [x - 30 + i * 8, y],
                [x - 19 + i * 7, y - 24 - i * 6],
                [x - 3 + i * 9, y],
              ],
              i % 2 ? "#b99b5f" : "#ffe1a0",
              2,
            );
          ring(c, x, y - 15, 24, "#ffeeb0", 1);
        }
        for (let i = 0; i < 3; i++)
          ring(c, x + 18 + i * 13, y, 12 + ((t * 40 + i * 8) % 26), color);
        for (let i = 0; i < 9; i++) {
          const xx = x + 12 + i * 4,
            yy = y - Math.abs(Math.sin(t * 6 + i)) * 20;
          c.fillStyle = i % 2 ? "#d2ac66" : "#efe0ab";
          c.fillRect(xx, yy, 3, 3);
        }
      } else if (b.hero === "lightning") {
        const list = targets.slice(0, ult ? 5 : 3);
        for (let i = 0; i < list.length; i++) {
          const [tx, ty] = at(list[i]);
          if (!ult || age > 0.48)
            bolt(
              c,
              ult ? tx - 9 : x,
              ult ? B.y : y - 21,
              tx,
              ty - 8,
              color,
              Math.floor(t * 18) + i,
            );
          ring(c, tx, ty, 13, color);
        }
        if (ult) ring(c, x, y - 18, 25, "#eee3ff", 1);
      } else if (b.hero === "herbalist") {
        for (const u of allies) {
          const [tx, ty] = at(u);
          ring(c, tx, ty, ult ? 20 : 13, color);
          for (let i = 0; i < 4; i++) {
            const a = t * 2 + (i * Math.PI) / 2,
              yy = ty - 10 - Math.abs(Math.sin(a)) * 20;
            c.fillStyle = i % 2 ? "#d7ffb7" : "#6be5aa";
            c.fillRect(tx + Math.cos(a) * 13, yy, 4, 2);
          }
          if (ult) lotus(c, tx, ty, 12, "#b9f5a0", t);
        }
      } else if (b.hero === "formation") {
        const r = ult ? 64 : 37;
        ring(c, x, y, r, color);
        ring(c, x, y, r * 0.7, "#b5eac8", 0.45, -t * 0.15);
        for (let i = 0; i < 8; i++) {
          const a = (i * Math.PI) / 4,
            tx = x + Math.cos(a) * r,
            ty = y + Math.sin(a) * r * 0.45;
          path(
            c,
            [
              [tx - 4, ty - 3],
              [tx + 4, ty - 3],
            ],
            "#f4d98c",
            2,
          );
          path(
            c,
            [
              [tx - 4, ty + 1],
              [tx + 4, ty + 1],
            ],
            "#f4d98c",
            1,
          );
        }
        for (const u of ult ? allies : allies.slice(0, 3)) {
          const [tx, ty] = at(u);
          path(
            c,
            [
              [x, y - 10],
              [tx, ty - 10],
            ],
            "#d8f2b9",
            1,
          );
          ring(c, tx, ty, 12, color);
        }
      }
    }
    c.restore();
  }
  const briefings = {
    wharf: [
      [
        "Read the river",
        "Tide repeats every 48 seconds. The blue water cells are columns 3–4 in the marked lanes. Rising and high tide reduce attack speed by 15%. High tide blocks new placements and deals 15 Water damage every 6 seconds.",
      ],
      [
        "Calm the flood",
        "The Calm ritual costs 35 Qi and cools down for 30 seconds. It makes flood cells safe for 12 seconds. Save it for a high-tide assault; it does not repair the ferry bridge before its scheduled opening.",
      ],
      [
        "Your final river rescue",
        "The Jade River Ark sweeps each lane only once. It purges ordinary enemies and deals a phase-safe heavy hit to bosses. Guard all five lanes: the final assault arrives on every lane together.",
      ],
    ],
    terrace: [
      [
        "Build around healthy nodes",
        "A green node strengthens heroes on it or one orthogonal cell away: +12% attack speed and +20% mana regeneration. Diagonal cells do not receive the node bonus.",
      ],
      [
        "Keep the ley pure",
        "A Drainer within one tile corrupts a node after 2 seconds. Red nodes heal nearby enemies. Remove the Drainer and hold an adjacent cell for 3 seconds, or spend 35 Qi on Purify to cleanse every node and restore nearby mana.",
      ],
      [
        "Ride the wind, hold the sky",
        "Wind changes every 20 seconds and alters projectile travel. Purify also locks the wind for 10 seconds. The Heaven Sword Array rescues each lane once and shields heroes that it passes.",
      ],
    ],
    tomb: [
      [
        "Pierce the grave mist",
        "Mist fills the marked lanes for the last 6 seconds of each 24-second cycle. Mana regeneration falls by 30%; ordinary targeting reaches only 2.8 tiles. Fire, lightning and reveal can still hit fading ghosts.",
      ],
      [
        "Break their return",
        "In the final encounter, three altars resurrect dead souls after 6 seconds and feed the Emperor. Destroy them. The Soul Mirror ritual costs 35 Qi: it reveals ghosts, prevents resurrection for 6 seconds and cleanses curses.",
      ],
      [
        "Keep a soul in reserve",
        "Three curse stacks slow attacks by 20% for 8 seconds. Bring healing or cleansing. The Soul-Sealing Bell purges a lane once, prevents its victims returning and reveals ghosts. Later enemies can still breach a spent lane.",
      ],
    ],
  };
  function diagram(c, s, region, page, x, y, w, h, images, atlas, text) {
    c.save();
    c.translate(x, y);
    c.scale(w / 384, h / 190);
    c.drawImage(images[region], 0, 0, 384, 190);
    c.fillStyle = "#07182555";
    c.fillRect(0, 0, 384, 190);
    const bx = 72,
      by = 30,
      cw = 24,
      ch = 24;
    for (let lane = 0; lane < 5; lane++)
      for (let col = 0; col < 12; col++) {
        c.fillStyle = "#19303b66";
        c.fillRect(bx + col * cw, by + lane * ch, 23, 23);
        c.strokeStyle = "#a9c5b844";
        c.strokeRect(bx + col * cw, by + lane * ch, 23, 23);
      }
    const cell = (lane, col, color) => {
      c.fillStyle = color;
      c.fillRect(bx + col * cw + 1, by + lane * ch + 1, 22, 22);
    };
    if (region === "wharf") {
      for (const lane of s?.hazard?.tiles
        ?.filter((t) => t.type === "water")
        .map((t) => t.lane) || [1, 3])
        for (const col of [3, 4])
          cell(lane, col, page === 1 ? "#64dba0aa" : "#5ba3e6bb");
      if (page === 0) {
        for (let i = 0; i < 4; i++) {
          c.fillStyle = ["#79b5c9", "#91d3d8", "#4b88bd", "#9bbfc7"][i];
          c.fillRect(76 + i * 68, 158, 64, 9);
        }
      }
      if (page === 1) {
        ring(c, 168, 92, 39, "#b9ffd8");
        text("35 Qi  /  12s calm", 160, 160, "#c0f8d6", 0.85, "center");
      }
    } else if (region === "terrace") {
      for (const n of s?.nodes || [
        { lane: 1, col: 3 },
        { lane: 2, col: 2 },
        { lane: 3, col: 4 },
      ]) {
        for (const [dl, dc] of [
          [0, 0],
          [-1, 0],
          [1, 0],
          [0, -1],
          [0, 1],
        ])
          if (n.lane + dl >= 0 && n.lane + dl < 5)
            cell(
              n.lane + dl,
              n.col + dc,
              page === 1 ? "#bd6467aa" : "#8bd89f88",
            );
        ring(
          c,
          bx + (n.col + 0.5) * cw,
          by + (n.lane + 0.5) * ch,
          8,
          page === 1 ? "#ffac90" : "#d9ffc0",
          1,
        );
      }
      text(
        page === 1 ? "Drainer: 2s  >  Ally: 3s" : "+12% speed  /  +20% mana",
        192,
        160,
        "#dcf8c5",
        0.85,
        "center",
      );
      if (page === 2) {
        path(
          c,
          [
            [110, 75],
            [325, 75],
          ],
          "#d5f7ff",
          3,
        );
        path(
          c,
          [
            [325, 108],
            [110, 108],
          ],
          "#d5f7ff",
          2,
        );
      }
    } else {
      for (const lane of stagesMist(s)) {
        for (let col = 1; col < 12; col++) cell(lane, col, "#aba6dc77");
      }
      if (page === 1)
        for (const lane of [1, 2, 3]) {
          const tx = bx + 8.5 * cw,
            ty = by + (lane + 0.5) * ch;
          path(
            c,
            [
              [tx - 8, ty + 8],
              [tx, ty - 12],
              [tx + 8, ty + 8],
            ],
            "#b2efcd",
            2,
            true,
          );
          ring(c, tx, ty, 11, "#6be6c0");
        }
      text(
        page === 1
          ? "Altars: destroy before souls return"
          : "Mist: 6s / 24s   -30% mana",
        192,
        160,
        "#e1d5ff",
        0.85,
        "center",
      );
    }
    if (page === 2) {
      for (let lane = 0; lane < 5; lane++) {
        const xx = bx + 12,
          yy = by + (lane + 0.5) * ch;
        artifact(c, images.guardians, atlas[region], xx, yy, 32, region, 0);
        path(
          c,
          [
            [xx + 22, yy],
            [xx + 120, yy],
          ],
          "#ffe3a0",
          2,
        );
      }
      text("ONE RESCUE PER LANE", 190, 176, "#ffe3a0", 0.85, "center");
    } else {
      text("GATE", 27, 77, "#fff0c2", 0.85, "center");
      path(
        c,
        [
          [350, 88],
          [300, 88],
        ],
        "#ffdb9c",
        3,
      );
      text("ENEMIES", 322, 12, "#ffe8c3", 0.8, "center");
    }
    c.restore();
  }
  function stagesMist(s) {
    return s?.hazard?.tiles?.map((t) => t.lane) || [1, 3];
  }
  return { effects, diagram, artifact, briefings };
})();
