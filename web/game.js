/* VAN DAO — browser presentation. Combat and rules run in the Python server. */
"use strict";
(() => {
  const canvas = document.getElementById("game"),
    ctx = canvas.getContext("2d", { alpha: false });
  const live = document.getElementById("live-status"),
    fileInput = document.getElementById("import-save");
  ctx.imageSmoothingEnabled = false;
  const W = 512,
    H = 288,
    B = { x: 92, y: 60, cw: 32, ch: 32, cols: 12, rows: 5 };
  canvas.width = W * 3;
  canvas.height = H * 3;
  ctx.setTransform(3, 0, 0, 3, 0, 0);
  const C = {
    ink: "#101a24",
    deep: "#0b131e",
    panel: "#152831",
    edge: "#52685f",
    jade: "#8de0bd",
    gold: "#e7c777",
    cream: "#f0e6c7",
    muted: "#93a8a0",
    dim: "#627a78",
    red: "#ef8076",
    ice: "#99dceb",
    violet: "#baacee",
  };
  const heroOrder = [
    "gatherer",
    "sword",
    "fire",
    "frost",
    "monk",
    "lightning",
    "herbalist",
    "formation",
  ];
  const shortNames = {
    gatherer: "YUN",
    sword: "SHEN",
    fire: "LIAN",
    frost: "BING",
    monk: "JIN",
    lightning: "LEI",
    herbalist: "MU",
    formation: "ZHEN",
  };
  const regionNames = {
    wharf: "GLASS LANTERN WHARF",
    terrace: "AZURE SPIRIT TERRACES",
    tomb: "BONE MAUSOLEUM",
  };
  const regionColor = { wharf: C.jade, terrace: C.ice, tomb: C.violet };
  let catalog = { heroes: [], enemies: [], stages: [], relics: [] },
    heroes = {},
    enemies = {},
    stages = {},
    images = {},
    atlas = {};
  let scene = "title",
    overlay = null,
    selectedHero = null,
    inspectUnit = null,
    stagePreview = null,
    rosterHero = "sword",
    buttons = [],
    pointer = { x: -1, y: -1 },
    toast = null;
  let archiveEnemy = "tide",
    archivePage = 0;
  let battleEpoch = 0;
  let selectionEpoch = 0;
  let seenEffects = new Set();
  let battleId = null,
    state = null,
    previousState = null,
    stateReceived = 0,
    polling = false,
    lastEvent = 0,
    commandBusy = false,
    resultApplied = false,
    battleStarted = 0;
  let now = 0,
    particles = [],
    slot = Number(localStorage.getItem("vanDao.activeSlot") || 0),
    profile,
    saveTimer = null,
    serverError = false,
    profileSaved = true;
  const freshProfile = () => ({
    version: 1,
    completed: [],
    stones: 0,
    insight: 0,
    upgrades: {},
    best: {},
    settings: {
      master: 0.6,
      music: 0.28,
      sfx: 0.65,
      shake: true,
      integer: false,
    },
    updated: Date.now(),
  });
  function loadProfile(index) {
    try {
      const v = JSON.parse(
        localStorage.getItem("vanDao.slot." + index) || "null",
      );
      return normalizeProfile(v);
    } catch {
      return freshProfile();
    }
  }
  function normalizeProfile(v) {
    const d = freshProfile();
    if (!v || v.version !== 1) return d;
    d.completed = Array.isArray(v.completed)
      ? v.completed.filter((x) => typeof x === "string").slice(0, 100)
      : [];
    d.stones = Math.max(0, Math.min(999999, Number(v.stones) || 0));
    d.insight = Math.max(0, Math.min(999999, Number(v.insight) || 0));
    for (const [k, b] of Object.entries(v.upgrades || {}))
      if (heroOrder.includes(k) && ["A", "B"].includes(b)) d.upgrades[k] = b;
    d.best = v.best && typeof v.best === "object" ? v.best : {};
    for (const k of ["master", "music", "sfx"]) {
      const value = Number(v.settings?.[k] ?? d.settings[k]);
      d.settings[k] = Number.isFinite(value)
        ? Math.max(0, Math.min(1, value))
        : d.settings[k];
    }
    for (const k of ["shake", "integer"])
      d.settings[k] =
        typeof v.settings?.[k] === "boolean" ? v.settings[k] : d.settings[k];
    return d;
  }
  profile = loadProfile(slot);
  function saveProfile() {
    profile.updated = Date.now();
    profileSaved = false;
    try {
      localStorage.setItem("vanDao.slot." + slot, JSON.stringify(profile));
      localStorage.setItem("vanDao.activeSlot", String(slot));
      profileSaved = true;
    } catch {
      notify("SAVE STORAGE IS FULL. EXPORT YOUR SAVE.", C.red, 6);
    }
    mirrorSave();
  }
  let saveDB = null;
  try {
    const req = indexedDB.open("van-dao-saves", 1);
    req.onupgradeneeded = () => req.result.createObjectStore("slots");
    req.onsuccess = () => {
      saveDB = req.result;
      mirrorSave();
    };
  } catch {}
  function mirrorSave() {
    if (!saveDB) return;
    try {
      saveDB
        .transaction("slots", "readwrite")
        .objectStore("slots")
        .put(JSON.parse(JSON.stringify(profile)), slot);
    } catch {}
  }
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const rect = (x, y, w, h, color) => {
    ctx.fillStyle = color;
    ctx.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h));
  };
  function text(str, x, y, color = C.cream, scale = 1, align = "left") {
    str = String(str ?? "")
      .replace(/[—–]/g, "-")
      .replace(/[‘’]/g, "'")
      .replace(/[“”]/g, '"')
      .replace(/×/g, "x");
    ctx.save();
    ctx.font = `${13 * scale}px VT323, monospace`;
    ctx.textBaseline = "top";
    ctx.textAlign = align;
    ctx.fillStyle = color;
    ctx.fillText(str, x, y - 1);
    ctx.restore();
  }
  function wrapped(
    str,
    x,
    y,
    maxW,
    color = C.muted,
    lineHeight = 10,
    maxLines = 10,
  ) {
    let line = "",
      lines = 0;
    for (const word of String(str ?? "")
      .replace(/[—–]/g, "-")
      .split(/\s+/)) {
      ctx.font = "13px VT323, monospace";
      if (ctx.measureText(line + word).width > maxW && line) {
        text(line.trim(), x, y + lines * lineHeight, color);
        line = "";
        if (++lines >= maxLines) return lines;
      }
      line += word + " ";
    }
    if (line && lines < maxLines)
      text(line.trim(), x, y + lines * lineHeight, color);
    return lines + 1;
  }
  function panel(x, y, w, h, edge = C.edge, fill = C.panel) {
    rect(x + 2, y, w - 4, h, C.deep);
    rect(x, y + 2, w, h - 4, C.deep);
    rect(x + 1, y + 1, w - 2, h - 2, edge);
    rect(x + 2, y + 2, w - 4, h - 4, fill);
    rect(x + 3, y + 3, w - 6, 1, "#344940");
    rect(x + 3, y + h - 4, w - 6, 1, "#0a151c");
  }
  function line(x1, y1, x2, y2, color) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(Math.round(x1) + 0.5, Math.round(y1) + 0.5);
    ctx.lineTo(Math.round(x2) + 0.5, Math.round(y2) + 0.5);
    ctx.stroke();
  }
  const inside = (p, r) =>
    p.x >= r.x && p.x < r.x + r.w && p.y >= r.y && p.y < r.y + r.h;
  function button(id, label, x, y, w, h, fn, opt = {}) {
    const r = { id, label, x, y, w, h, fn, disabled: !!opt.disabled };
    buttons.push(r);
    const hover = inside(pointer, r) && !r.disabled;
    panel(
      x,
      y,
      w,
      h,
      r.disabled
        ? "#35434a"
        : opt.active
          ? C.gold
          : hover
            ? C.jade
            : opt.edge || C.edge,
      r.disabled ? "#172128" : hover ? "#284238" : opt.fill || "#1b3035",
    );
    text(
      String(label).slice(0, Math.max(1, Math.floor((w - 10) / 6.5))),
      x + w / 2,
      y + (h - 7) / 2,
      r.disabled ? C.dim : opt.active ? C.gold : opt.color || C.cream,
      1,
      "center",
    );
    return r;
  }
  function notify(message, color = C.gold, duration = 3) {
    toast = {
      message: String(message).toUpperCase().replace(/[—–]/g, "-"),
      color,
      until: performance.now() + duration * 1000,
    };
    live.textContent = message;
  }
  function bg(name, shade = 0) {
    if (images[name]) ctx.drawImage(images[name], 0, 0, W, H);
    else rect(0, 0, W, H, C.ink);
    if (shade) {
      ctx.fillStyle = `rgba(7,14,21,${shade})`;
      ctx.fillRect(0, 0, W, H);
    }
  }
  function sprite(id, x, y, scale = 1, frame = null, alpha = 1) {
    const s = atlas[id] || atlas[id?.replaceAll("_", "")];
    if (!s || !images.sprites) return;
    const f =
      frame === null
        ? Math.floor(now / 260) % (s.frames || 1)
        : frame % (s.frames || 1);
    ctx.globalAlpha = alpha;
    ctx.drawImage(
      images.sprites,
      s.x + f * s.w,
      s.y,
      s.w,
      s.h,
      Math.round(x),
      Math.round(y),
      s.w * scale,
      s.h * scale,
    );
    ctx.globalAlpha = 1;
  }
  function icon(type, x, y, color = C.gold) {
    if (type === "qi") {
      rect(x + 3, y, 2, 2, color);
      rect(x + 1, y + 2, 6, 4, color);
      rect(x + 2, y + 6, 4, 2, color);
      rect(x + 3, y + 2, 2, 3, "#fbf0c4");
    } else if (type === "gate") {
      rect(x, y + 1, 8, 2, color);
      rect(x + 1, y + 3, 2, 5, color);
      rect(x + 5, y + 3, 2, 5, color);
      rect(x + 3, y + 3, 2, 1, color);
    } else if (type === "stone") {
      rect(x + 2, y, 4, 1, color);
      rect(x + 1, y + 1, 6, 5, color);
      rect(x + 2, y + 6, 4, 1, color);
      rect(x + 2, y + 2, 2, 2, C.cream);
    } else if (type === "lock") {
      rect(x + 2, y, 4, 1, color);
      rect(x + 1, y + 1, 1, 3, color);
      rect(x + 6, y + 1, 1, 3, color);
      rect(x, y + 4, 8, 5, color);
      rect(x + 3, y + 5, 2, 2, C.deep);
    } else if (type === "star") {
      rect(x + 3, y, 2, 8, color);
      rect(x, y + 3, 8, 2, color);
      rect(x + 1, y + 1, 2, 2, color);
      rect(x + 5, y + 1, 2, 2, color);
      rect(x + 1, y + 5, 2, 2, color);
      rect(x + 5, y + 5, 2, 2, color);
    }
  }
  function unlocked(h) {
    return (
      h?.unlock === "start" ||
      !h?.unlock ||
      profile.completed.includes(h.unlock)
    );
  }
  function stageUnlocked(s) {
    return (
      s.index === 0 ||
      profile.completed.includes(
        catalog.stages.find((x) => x.index === s.index - 1)?.id,
      )
    );
  }
  function realm() {
    return profile.completed.includes("tomb-3")
      ? 3
      : profile.completed.includes("terrace-3")
        ? 2
        : profile.completed.includes("wharf-3")
          ? 1
          : 0;
  }
  function header(
    title,
    back = () => {
      scene = "title";
      overlay = null;
    },
  ) {
    rect(0, 0, W, 25, "#101d26");
    rect(0, 24, W, 1, "#51604b");
    button("back", "<", 7, 5, 20, 15, back);
    text(title, 36, 9, C.gold);
    icon("stone", 275, 8);
    text(profile.stones, 287, 9, C.cream);
    text("SLOT " + (slot + 1), W - 8, 9, C.muted, 1, "right");
  }
  function drawTitle() {
    bg("title");
    text("THE LAST IMMORTAL GATE", 24, 14, C.muted);
    line(24, 29, 206, 29, C.edge);
    text("VAN DAO", 25, 43, C.deep, 3);
    text("VAN DAO", 23, 41, C.cream, 3);
    text("IMMORTAL WAR", 25, 82, C.gold, 1.3);
    wrapped(
      "The gate is failing. Your formation is its last light.",
      25,
      112,
      164,
      C.jade,
      14,
      3,
    );
    button("begin", "BEGIN CAMPAIGN", 24, 164, 174, 27, () => {
      scene = "campaign";
      audio.play("confirm");
    });
    button("roster", "CULTIVATORS", 24, 198, 174, 24, () => (scene = "roster"));
    button("saves", "SAVE SLOTS", 24, 229, 84, 24, () => (overlay = "saves"));
    button(
      "settings",
      "SETTINGS",
      114,
      229,
      84,
      24,
      () => (overlay = "settings"),
    );
    button(
      "archive",
      "MONSTER ARCHIVE",
      278,
      241,
      210,
      23,
      () => (scene = "archive"),
    );
    text("Original art / Offline play", W - 16, H - 13, C.muted, 0.95, "right");
    if (battleId && state && isPlaying(state))
      button("resume", "RESUME BATTLE", 278, 211, 210, 24, () => {
        scene = "battle";
        command({ action: "pause", paused: false });
      });
    drawAmbient("title");
  }
  function drawCampaign() {
    bg("title", 0.58);
    header("THE FRACTURED LEYLINES");
    text("CHOOSE AN ENCOUNTER", 13, 32, C.muted);
    text(
      "KEEPER: " +
        ["QI GATHERING", "JADE AWAKENING", "FOUNDATION", "GOLDEN CORE"][
          realm()
        ],
      W - 12,
      32,
      C.jade,
      1,
      "right",
    );
    const names = {
      wharf: ["I", "LANTERN WHARF"],
      terrace: ["II", "AZURE TERRACE"],
      tomb: ["III", "BONE TOMB"],
    };
    ["wharf", "terrace", "tomb"].forEach((reg, i) => {
      const x = 16 + i * 165;
      panel(x, 55, 150, 157, regionColor[reg], "#14262e");
      if (images[reg]) {
        ctx.save();
        ctx.beginPath();
        ctx.rect(x + 3, 58, 144, 42);
        ctx.clip();
        ctx.drawImage(images[reg], x - 15, 30, 192, 108);
        ctx.restore();
        rect(x + 3, 100, 144, 3, "#152831");
      }
      text(
        names[reg][0] + "  " + names[reg][1],
        x + 75,
        112,
        regionColor[reg],
        1,
        "center",
      );
      const list = catalog.stages.filter((s) => s.region === reg);
      list.forEach((s, j) => {
        const done = profile.completed.includes(s.id),
          open = stageUnlocked(s);
        let label =
          (done ? "* " : open ? "> " : "  ") +
          (j === 2 ? "BOSS: " : "") +
          String(j + 1);
        if (j < 2) label += "  " + (j === 0 ? "FIRST LIGHT" : "RISING TIDE");
        if (reg === "terrace" && j < 2)
          label =
            (done ? "* " : open ? "> " : "  ") +
            (j + 1) +
            " " +
            ["LEY GARDEN", "SKY HUNTERS"][j];
        if (reg === "tomb" && j < 2)
          label =
            (done ? "* " : open ? "> " : "  ") +
            (j + 1) +
            " " +
            ["SEALED GATE", "SOUL PYRES"][j];
        if (j === 2) label = (done ? "* " : open ? "> " : "  ") + "3 BOSS";
        button(
          "stage-" + s.id,
          label,
          x + 6,
          130 + j * 24,
          138,
          21,
          () => {
            stagePreview = s;
            overlay = "stage";
          },
          {
            disabled: !open,
            active: open && !done,
            color: done ? C.jade : C.cream,
          },
        );
      });
    });
    button(
      "roster",
      "CULTIVATE ROSTER",
      12,
      227,
      134,
      19,
      () => (scene = "roster"),
    );
    button(
      "saves",
      "SAVE / LOAD",
      152,
      227,
      103,
      19,
      () => (overlay = "saves"),
    );
    button(
      "settings",
      "SETTINGS",
      261,
      227,
      111,
      19,
      () => (overlay = "settings"),
    );
    button("archive", "BESTIARY", 380, 227, 116, 20, () => (scene = "archive"));
    if (profile.completed.includes("tomb-3"))
      text(
        "THE EMPEROR IS FALLEN. A NEW DAWN BEGINS.",
        192,
        177,
        C.gold,
        1,
        "center",
      );
  }
  function drawRoster() {
    bg("title", 0.75);
    header("CULTIVATION HALL", () => (scene = "campaign"));
    const h = heroes[rosterHero] || catalog.heroes[0];
    heroOrder.forEach((id, i) => {
      button(
        "hero-" + id,
        shortNames[id] + (unlocked(heroes[id]) ? "" : " / LOCK"),
        10,
        35 + i * 29,
        100,
        26,
        () => (rosterHero = id),
        { active: rosterHero === id },
      );
      sprite(id, 10, 29 + i * 29, 0.8);
    });
    panel(120, 34, 380, 240, C.edge);
    sprite(h.id, 132, 41, 2);
    text(h.name, 208, 44, C.gold, 1.35);
    text(h.title, 208, 65, C.jade);
    text(`${h.hp} HP / ${h.armor} armor / ${h.cost} Qi`, 208, 82);
    wrapped(h.description, 132, 113, 351, C.cream, 13, 3);
    wrapped(
      h.skill.name + ": " + h.skill.description,
      132,
      155,
      350,
      C.jade,
      13,
      2,
    );
    wrapped(
      h.ultimate.name + ": " + h.ultimate.description,
      132,
      184,
      350,
      C.gold,
      13,
      2,
    );
    if (!unlocked(h)) {
      wrapped(
        "Unlock: Clear " + (stages[h.unlock]?.name || h.unlock),
        132,
        230,
        350,
        C.gold,
        14,
        2,
      );
      return;
    }
    const current = profile.upgrades[h.id];
    for (const [i, key] of ["A", "B"].entries()) {
      const b = h.branches[key],
        x = 130 + i * 181;
      button(
        "branch-" + key,
        (current === key ? "* " : "") + key + " " + b.name,
        x,
        217,
        174,
        22,
        () => buyBranch(h.id, key, b.cost),
        { disabled: !!current && current !== key, active: current === key },
      );
      wrapped(b.description, x + 2, 243, 170, C.muted, 11, 2);
    }
  }
  function drawArchive() {
    bg("tomb", 0.75);
    header("MONSTER ARCHIVE", () => (scene = "campaign"));
    const list = catalog.enemies,
      visible = list.slice(archivePage * 6, archivePage * 6 + 6);
    visible.forEach((e, i) => {
      button(
        "enemy-" + e.id,
        e.name,
        10,
        38 + i * 32,
        174,
        29,
        () => (archiveEnemy = e.id),
        { active: archiveEnemy === e.id },
      );
      sprite(e.id, 12, 34 + i * 32, 0.85);
    });
    button(
      "archive-prev",
      "<",
      10,
      244,
      50,
      25,
      () => (archivePage = Math.max(0, archivePage - 1)),
      { disabled: archivePage === 0 },
    );
    text(
      `${archivePage + 1} / ${Math.ceil(list.length / 6)}`,
      98,
      252,
      C.muted,
      1,
      "center",
    );
    button(
      "archive-next",
      ">",
      135,
      244,
      49,
      25,
      () =>
        (archivePage = Math.min(
          Math.ceil(list.length / 6) - 1,
          archivePage + 1,
        )),
      { disabled: archivePage >= Math.ceil(list.length / 6) - 1 },
    );
    const e = enemies[archiveEnemy] || list[0];
    if (!e) return;
    panel(195, 35, 307, 239, regionColor[e.boss ? "tomb" : "wharf"]);
    sprite(e.id, 205, 42, 2, Math.floor(now / 240) % 4);
    wrapped(e.name, 276, 47, 214, C.gold, 16, 2);
    text(e.boss ? "BOSS / 3 PHASES" : e.role, 276, 86, C.jade);
    text(`HP ${e.hp} / Armor ${e.armor} / Shield ${e.shield || 0}`, 207, 115);
    text(`ATK ${e.damage} ${e.damage_type} / ${e.interval}s`, 207, 132);
    text(`Speed ${e.speed} tiles/s / Reach ${e.range}`, 207, 149);
    const resist = Object.entries(e.resistances || {})
      .map(([k, v]) => `${k} ${v >= 0 ? "+" : ""}${Math.round(v * 100)}%`)
      .join(" / ");
    text(resist || "No elemental resistance", 207, 166, C.ice, 0.9);
    const ability = e.abilities?.[0];
    text(ability?.name || "Special behavior", 207, 188, C.gold);
    wrapped(
      ability?.description || e.description,
      207,
      204,
      282,
      C.cream,
      12,
      3,
    );
    wrapped(
      "Counter: " + (e.counterplay || "Use mixed damage."),
      207,
      242,
      282,
      C.jade,
      12,
      2,
    );
  }
  function buyBranch(id, branch, cost) {
    if (profile.upgrades[id])
      return notify("THIS CULTIVATOR HAS ALREADY CHOSEN A PATH.");
    if (profile.stones < cost)
      return notify(
        "NEED " + (cost - profile.stones) + " MORE SPIRIT STONES.",
        C.red,
      );
    profile.stones -= cost;
    profile.upgrades[id] = branch;
    saveProfile();
    audio.play("upgrade");
    notify("CULTIVATION COMPLETE. PATH " + branch + " AWAKENED.", C.jade);
  }
  function isPlaying(s) {
    return s && ["playing", "running", "active"].includes(s.status);
  }
  function unitX(unit) {
    return B.x + Number(unit.x ?? Number(unit.col) + 0.5) * B.cw;
  }
  function unitY(unit) {
    return B.y + (Number(unit.lane) + 1) * B.ch;
  }
  function renderedX(unit) {
    if (unit.friendly || state?.paused || !previousState) return unitX(unit);
    const before = (previousState.enemies || []).find((e) => e.id === unit.id);
    if (!before) return unitX(unit);
    const mix = clamp((now - stateReceived) / 55, 0, 1);
    return B.x + (before.x + (unit.x - before.x) * mix) * B.cw;
  }
  function drawBattle() {
    const s = state;
    if (!s) {
      bg("title", 0.8);
      text("AWAKENING THE FORMATION...", 192, 105, C.jade, 1, "center");
      return;
    }
    bg(s.region || "wharf");
    // Tile and range indicators sit behind the sprites, never over attack feedback.
    for (let lane = 0; lane < 5; lane++)
      for (let col = 1; col <= 9; col++) {
        const x = B.x + col * B.cw,
          y = B.y + lane * B.ch;
        rect(x, y, 1, B.ch, "#8aa58528");
        rect(x, y, B.cw, 1, "#8aa58528");
      }
    const tile = tileAt(pointer);
    if (selectedHero && tile && isPlaying(s) && !s.paused) {
      const occupied = (s.heroes || []).some(
        (h) => h.col === tile.col && h.lane === tile.lane,
      );
      ctx.globalAlpha = 0.3;
      rect(
        B.x + tile.col * B.cw,
        B.y + tile.lane * B.ch,
        B.cw,
        B.ch,
        occupied ? C.red : C.jade,
      );
      ctx.globalAlpha = 1;
      sprite(
        selectedHero,
        B.x + tile.col * B.cw + 1,
        B.y + (tile.lane + 1) * B.ch - 29,
        1,
        null,
        0.55,
      );
    }
    for (const tile of s.hazard?.tiles || []) {
      const type = tile.type || tile.tag;
      if (type === "water") {
        ctx.globalAlpha = tile.blocked ? 0.42 : 0.15;
        rect(
          B.x + tile.col * B.cw + 1,
          B.y + tile.lane * B.ch + 1,
          B.cw - 2,
          B.ch - 2,
          C.ice,
        );
        ctx.globalAlpha = 1;
      }
      if (type === "node" || type === "leyline") {
        icon(
          "star",
          B.x + tile.col * B.cw + 13,
          B.y + tile.lane * B.ch + 9,
          C.jade,
        );
      }
      if (
        tile.blocked ||
        ["blocked", "tomb_seal", "sealed", "water_deep"].includes(type)
      ) {
        const x = B.x + tile.col * B.cw,
          y = B.y + tile.lane * B.ch;
        rect(x + 1, y + 1, B.cw - 2, B.ch - 2, "#322f3899");
        text(
          type.includes("seal") ? "X" : "~",
          x + 17,
          y + 9,
          C.violet,
          1,
          "center",
        );
      }
    }
    for (const tell of s.telegraphs || []) {
      for (const lane of tell.lanes || []) {
        const y = B.y + lane * B.ch;
        ctx.globalAlpha = 0.12 + Math.sin(now / 80) * 0.05;
        rect(B.x + B.cw, y, 10 * B.cw, B.ch, C.red);
        ctx.globalAlpha = 1;
        for (let x = B.x + B.cw; x < B.x + 11 * B.cw; x += 6) {
          rect(x, y, 3, 1, C.red);
          rect(x, y + B.ch - 1, 3, 1, C.red);
        }
        text("!", B.x + 7, y + 9, C.red);
      }
    }
    const upcoming = (stages[s.stage]?.waves || []).find(
      (w) => (w.at ?? w.time) > s.time + 0.05,
    );
    if (upcoming) {
      const remaining = (upcoming.at ?? upcoming.time) - s.time;
      for (const spawn of upcoming.spawns || upcoming.enemies || []) {
        const y = B.y + (spawn.lane + 0.5) * B.ch;
        text("<", 486, y - 4, C.gold);
        if (remaining < 10)
          text(Math.ceil(remaining), 505, y - 4, C.gold, 1, "right");
      }
    }
    drawDefenses(s);
    drawAmbient(s.region || "wharf");
    const units = [
      ...(s.heroes || []).map((x) => ({ ...x, friendly: true })),
      ...(s.enemies || []).map((x) => ({ ...x, friendly: false })),
    ].sort((a, b) => a.lane - b.lane || a.x - b.x);
    for (const u of units) {
      let x = renderedX(u),
        y = unitY(u),
        size = u.friendly
          ? 32
          : enemies[u.type]?.boss ||
              String(u.type).includes("lord") ||
              String(u.type).includes("emperor")
            ? 44
            : 32;
      let bob = !s.paused && u.action === "attack" ? Math.sin(now / 65) * 1 : 0;
      const selected = inspectUnit === u.id && u.friendly;
      if (selected) {
        rect(x - 12, y - 3, 24, 2, C.gold);
        rect(x - 8, y - 1, 16, 1, C.gold);
      }
      if (u.frozen > 0) {
        rect(x - 12, y - 24, 24, 23, "#9ce8ef45");
      }
      sprite(
        u.type,
        x - size / 2 + bob,
        y - size + 3,
        size / 32,
        null,
        u.hidden ? 0.42 : 1,
      );
      const hp = clamp(Number(u.hp || 0) / Number(u.max_hp || u.hp || 1), 0, 1);
      rect(x - 11, y - 29, 22, 3, C.deep);
      rect(x - 11, y - 29, 22 * hp, 2, u.friendly ? C.jade : C.red);
      if (u.shield > 0)
        rect(
          x - 11,
          y - 26,
          clamp(u.shield / (u.max_hp || 100), 0, 1) * 22,
          1,
          C.ice,
        );
      if (u.friendly) {
        rect(x - 10, y + 2, 20, 2, "#13222b");
        rect(
          x - 10,
          y + 2,
          20 * clamp(u.resonance / 100, 0, 1),
          2,
          u.resonance >= 100 ? C.gold : C.violet,
        );
        if (u.resonance >= 100) icon("star", x - 3, y - 41, C.gold);
      } else if (u.burn > 0) {
        rect(x + 8, y - 15, 2, 4, "#ed8d4c");
        rect(x + 9, y - 17, 2, 4, C.gold);
      }
      if (u.phase > 1) text("P" + u.phase, x, y - 38, C.violet, 1, "center");
    }
    for (const p of s.projectiles || []) {
      const x = B.x + Number(p.x || 0) * B.cw,
        y = B.y + (Number(p.lane || 0) + 0.5) * B.ch;
      const color =
        { fire: "#ffa260", frost: C.ice, lightning: C.violet, sword: C.jade }[
          p.type
        ] || C.gold;
      rect(x - 5, y, 8, 2, color);
      rect(x + 1, y - 1, 4, 4, color);
      rect(x - 8, y, 2, 1, C.cream);
    }
    for (const o of s.orbs || []) {
      const x = B.x + Number(o.x ?? o.col ?? 1) * B.cw,
        y =
          B.y +
          (Number(o.lane || 0) + 0.3) * B.ch +
          Math.sin(now / 200 + o.id) * 2;
      icon("qi", x - 4, y - 3, C.gold);
    }
    drawEffects(s);
    drawHUD(s);
    drawCards(s);
    const unit = (s.heroes || []).find((h) => h.id === inspectUnit);
    if (unit && !selectedHero) drawInspect(unit);
    if (s.paused && !overlay) {
      panel(119, 82, 146, 61, C.gold);
      text("BATTLE PAUSED", 192, 94, C.gold, 1, "center");
      button("resume", "RESUME", 132, 111, 120, 20, () =>
        command({ action: "pause", paused: false }),
      );
    }
    if (!isPlaying(s)) drawResults();
    if (W / H > innerWidth / innerHeight + 1 && innerWidth < 600) {
      panel(91, 4, 202, 17, C.gold);
      text("ROTATE FOR A WIDER BATTLEFIELD", 192, 9, C.gold, 1, "center");
    }
  }
  function drawAmbient(region) {
    const t = now / 1000;
    ctx.globalAlpha = 0.45;
    for (let i = 0; i < 14; i++) {
      const x =
          (i * 79 + Math.floor(t * (region === "terrace" ? 11 : 3))) % 384,
        y = (i * 37 + Math.floor(Math.sin(t * 0.5 + i) * 5)) % 180;
      const color =
        region === "tomb" ? C.ice : region === "terrace" ? C.jade : C.gold;
      rect(x, y, i % 3 === 0 ? 2 : 1, 1, color);
    }
    ctx.globalAlpha = 1;
  }
  function drawDefenses(s) {
    wrapped(
      stages[s.stage]?.stronghold || "Immortal Palace",
      5,
      223,
      80,
      C.gold,
      10,
      2,
    );
    for (const ward of s.defenses || []) {
      const x = B.x + ward.x * B.cw,
        y = B.y + (ward.lane + 0.5) * B.ch;
      if (ward.status === "spent") {
        line(B.x + 9, y - 5, B.x + 23, y + 5, C.dim);
        line(B.x + 23, y - 5, B.x + 9, y + 5, C.dim);
        continue;
      }
      const color = ward.status === "sweeping" ? C.cream : C.gold;
      rect(x - 6, y - 10, 12, 19, "#22424c");
      line(x - 8, y - 4, x + 8, y + 4, color);
      line(x - 8, y + 4, x + 8, y - 4, color);
      rect(x - 2, y - 13, 4, 25, color);
      rect(x - 9, y - 1, 18, 3, C.jade);
      if (ward.status === "sweeping") {
        for (let i = 1; i < 5; i++) rect(x - i * 7, y - 7 + i * 3, 5, 2, C.ice);
      }
    }
    if (
      pointer.x >= B.x &&
      pointer.x < B.x + B.cw &&
      pointer.y >= B.y &&
      pointer.y < B.y + 5 * B.ch
    ) {
      panel(95, 223, 380, 16, C.gold);
      text(
        "Guardian seal: one automatic rescue per lane. Place heroes to its right.",
        102,
        226,
        C.gold,
        0.9,
      );
    }
  }
  function drawHUD(s) {
    rect(0, 0, W, 27, "#10202a");
    rect(0, 26, W, 1, C.edge);
    icon("qi", 8, 8, C.gold);
    text(Math.floor(s.qi || 0), 22, 8, C.gold);
    icon("gate", 80, 8, C.jade);
    text(s.gate ?? 3, 94, 8);
    text("Wave " + (s.wave || 0) + "/" + (s.wave_count || 0), 126, 8);
    text(formatTime(s.time), 237, 8, C.muted);
    button("pause", s.paused ? ">" : "II", 303, 4, 28, 19, () =>
      command({ action: "pause", paused: !s.paused }),
    );
    button("speed", (s.speed || 1) + "x", 335, 4, 39, 19, () => {
      const values = realm() >= 3 ? [1, 1.5, 2] : [1, 1.5];
      command({
        action: "speed",
        value: values[(values.indexOf(s.speed || 1) + 1) % values.length],
      });
    });
    button("battle-settings", "Menu", 378, 4, 48, 19, () => {
      command({ action: "pause", paused: true });
      overlay = "battleMenu";
    });
    button("help", "Guide", 430, 4, 72, 19, () => {
      command({ action: "pause", paused: true });
      overlay = "controls";
    });
    rect(0, 28, W, 25, "#10202ae8");
    text(stages[s.stage]?.name || s.stage, 8, 32, C.jade);
    text(
      (s.hazard?.phase || "") + " / " + (s.hazard?.countdown ?? 0) + "s",
      W - 8,
      32,
      C.muted,
      1,
      "right",
    );
    for (let i = 0; i < realm(); i++)
      button(
        "relic-" + i,
        ["1", "2", "3"][i],
        5 + i * 27,
        251,
        24,
        22,
        () => command({ action: "relic", slot: i }),
        { disabled: s.relics_used?.includes(catalog.relics[i]?.id) },
      );
    const boss = s.enemies?.find((e) => e.boss);
    if (boss) {
      panel(158, 47, 270, 13, C.violet);
      rect(161, 50, 264 * clamp(boss.hp / boss.max_hp, 0, 1), 6, "#a65874");
      text(
        (enemies[boss.type]?.name || "Boss") + " / Phase " + boss.phase,
        293,
        49,
        C.cream,
        0.9,
        "center",
      );
    }
  }
  function drawCards(s) {
    rect(85, 238, W - 85, 50, "#0c1822");
    heroOrder.forEach((id, i) => {
      const h = heroes[id],
        x = 88 + i * 52,
        available = unlocked(h),
        cd = Number(s.cards?.[id] || 0);
      panel(x, 241, 50, 45, selectedHero === id ? C.gold : C.edge);
      sprite(id, x + 4, 246, 0.9, null, available ? 1 : 0.25);
      text(i + 1, x + 3, 243, C.muted, 0.85);
      text(
        available ? h.cost : "LOCK",
        x + 46,
        243,
        available ? (s.qi >= h.cost ? C.gold : C.red) : C.dim,
        0.85,
        "right",
      );
      text(
        shortNames[id],
        x + 25,
        274,
        available ? C.cream : C.dim,
        0.9,
        "center",
      );
      if (cd > 0) {
        rect(x + 2, 243, 46, 37 * clamp(cd / h.cooldown, 0, 1), "#0b131ebb");
        text(Math.ceil(cd) + "s", x + 25, 258, C.cream, 1, "center");
      }
      buttons.push({
        id: "card-" + id,
        x,
        y: 241,
        w: 50,
        h: 45,
        fn: () => selectCard(id),
        disabled: !available,
      });
    });
    if (selectedHero) {
      const h = heroes[selectedHero];
      panel(135, 221, 340, 16, C.gold);
      text(
        h.name + " / " + h.cost + " Qi / Choose an empty tile",
        305,
        224,
        C.gold,
        0.95,
        "center",
      );
    }
  }
  function drawInspect(u) {
    const h = heroes[u.type] || {};
    const x = 200,
      y = 184;
    panel(x, y, 177, 47, C.gold);
    text((h.name || u.type).slice(0, 20), x + 6, y + 5, C.gold);
    text(
      "HP " +
        Math.ceil(u.hp) +
        "  DAO " +
        Math.floor(u.resonance || 0) +
        "/100",
      x + 6,
      y + 15,
      C.muted,
    );
    button(
      "ultimate",
      "Q ULTIMATE",
      x + 5,
      y + 27,
      103,
      16,
      () => command({ action: "ultimate", unit: u.id }),
      { disabled: u.resonance < 100 },
    );
    button("recall", "RECALL", x + 112, y + 27, 59, 16, () => {
      command({ action: "sell", unit: u.id });
      inspectUnit = null;
    });
  }
  function drawEffects(s) {
    for (const e of s.effects || []) {
      let x = B.x + Number(e.x ?? 0) * B.cw,
        y = B.y + (Number(e.lane ?? 0) + 0.55) * B.ch;
      const age = Number(e.age || 0),
        radius = 4 + Math.min(12, age * 16);
      const color = ["heal", "qi", "aura", "array"].includes(e.kind)
        ? C.jade
        : ["shield", "freeze"].includes(e.kind)
          ? C.ice
          : ["lightning", "phase", "resurrect"].includes(e.kind)
            ? C.violet
            : ["hurt", "fire", "eruption", "breach"].includes(e.kind)
              ? C.red
              : C.gold;
      ctx.globalAlpha = clamp(Number(e.ttl || 0.3) / 0.18, 0, 1);
      if (["lightning", "sword", "melee"].includes(e.kind)) {
        for (let i = 0; i < 6; i++) {
          const ox = (i % 2 ? 3 : -2) + i - 4;
          rect(x + ox, y - 16 + i * 4, 2, 5, color);
        }
      } else if (["fire", "eruption"].includes(e.kind)) {
        for (let i = 0; i < 7; i++) {
          const height = 4 + ((i * 7 + Math.floor(age * 22)) % 12);
          rect(x - 10 + i * 3, y - height, 3, height, i % 2 ? C.gold : C.red);
        }
      } else if (!["damage", "hurt", "recall", "absorb"].includes(e.kind)) {
        for (let i = 0; i < 8; i++) {
          const angle = (i * Math.PI) / 4;
          rect(
            x + Math.cos(angle) * radius,
            y + Math.sin(angle) * radius * 0.55,
            2,
            2,
            color,
          );
        }
        if (["heal", "shield", "freeze"].includes(e.kind)) {
          rect(x - 1, y - 7, 2, 8, color);
          rect(x - 4, y - 4, 8, 2, color);
        }
      }
      if (e.text) {
        const label = String(e.text).slice(0, 40);
        const half = label.length * 3;
        text(
          label,
          clamp(x, half + 4, W - half - 4),
          y - 12 - age * 8,
          color,
          1,
          "center",
        );
      }
      ctx.globalAlpha = 1;
    }
    particles = particles.filter((p) => now - p.start < p.life);
    for (const p of particles) {
      const t = (now - p.start) / p.life;
      ctx.globalAlpha = 1 - t;
      rect(p.x + p.dx * t, p.y + p.dy * t, 2, 2, p.color);
      ctx.globalAlpha = 1;
    }
  }
  function formatTime(t) {
    t = Math.max(0, Math.floor(Number(t) || 0));
    return Math.floor(t / 60) + ":" + String(t % 60).padStart(2, "0");
  }
  function drawResults() {
    const s = state,
      won = ["victory", "won"].includes(s.status);
    panel(72, 57, 240, 107, won ? C.gold : C.red, "#12212b");
    text(
      won ? "THE GATE ENDURES" : "THE GATE HAS FALLEN",
      192,
      70,
      won ? C.gold : C.red,
      1,
      "center",
    );
    text(stages[s.stage]?.name || s.stage, 192, 85, C.cream, 1, "center");
    text(
      "TIME " + formatTime(s.time) + "  ENEMIES " + (s.kills || 0),
      192,
      98,
      C.muted,
      1,
      "center",
    );
    text(
      won
        ? resultApplied
          ? "PROGRESS SAVED"
          : "SAVING YOUR VICTORY..."
        : "REFORM YOUR LINE. TRY ANOTHER TACTIC.",
      192,
      111,
      won ? C.jade : C.muted,
      1,
      "center",
    );
    button("retry", won ? "NEXT STAGE" : "TRY AGAIN", 87, 132, 98, 20, () => {
      const next = catalog.stages.find(
        (x) => x.index === (stages[s.stage]?.index ?? 0) + 1,
      );
      if (won && next) startBattle(next.id);
      else if (won) leaveBattle();
      else startBattle(s.stage);
    });
    button("results-campaign", "CAMPAIGN", 192, 132, 104, 20, () =>
      leaveBattle(),
    );
  }
  function drawOverlay() {
    if (!overlay) return;
    ctx.fillStyle = "rgba(6,12,19,.8)";
    ctx.fillRect(0, 0, W, H);
    if (overlay === "stage") {
      const s = stagePreview;
      panel(55, 35, 274, 150, regionColor[s.region]);
      text(
        "CHAPTER " + s.chapter + " / " + s.id.toUpperCase(),
        70,
        47,
        regionColor[s.region],
      );
      text(s.name, 70, 62, C.gold);
      wrapped(s.description, 70, 78, 242, C.cream, 11, 4);
      wrapped(s.mechanic, 70, 124, 242, C.muted, 10, 2);
      text(
        `${s.waves.length} waves / ${s.enemy_count} foes / ${s.duration_label}`,
        70,
        139,
        C.gold,
        0.9,
      );
      button("start", "DEFEND THE GATE", 70, 155, 160, 20, () =>
        startBattle(s.id),
      );
      button("close", "BACK", 237, 155, 76, 20, () => (overlay = null));
      return;
    }
    if (overlay === "settings") {
      panel(69, 28, 246, 164, C.gold);
      text("SOUND & DISPLAY", 192, 40, C.gold, 1, "center");
      for (const [i, key] of ["master", "music", "sfx"].entries()) {
        const y = 61 + i * 24;
        text(key.toUpperCase(), 82, y + 4, C.muted);
        const val = profile.settings[key];
        rect(139, y + 4, 116, 5, "#0d1b25");
        rect(139, y + 4, 116 * val, 5, C.jade);
        text(Math.round(val * 100), 296, y + 3, C.cream, 1, "right");
        buttons.push({
          id: "volume-" + key,
          x: 132,
          y: y - 3,
          w: 132,
          h: 19,
          fn: (p) => {
            profile.settings[key] = clamp((p.x - 139) / 116, 0, 1);
            audio.update();
            saveProfile();
          },
        });
      }
      button(
        "shake",
        "SHAKE " + (profile.settings.shake ? "ON" : "OFF"),
        81,
        135,
        107,
        18,
        () => {
          profile.settings.shake = !profile.settings.shake;
          saveProfile();
        },
      );
      button(
        "pixel-mode",
        profile.settings.integer ? "INTEGER PIXEL" : "FIT DISPLAY",
        195,
        135,
        107,
        18,
        () => {
          profile.settings.integer = !profile.settings.integer;
          saveProfile();
          resize();
        },
      );
      button("close", "BACK", 128, 163, 128, 18, () => (overlay = null));
      return;
    }
    if (overlay === "battleMenu") {
      panel(108, 40, 168, 137, C.gold);
      text("SPIRIT REST", 192, 52, C.gold, 1, "center");
      button("resume", "RESUME", 122, 71, 140, 20, () => {
        overlay = null;
        command({ action: "pause", paused: false });
      });
      button(
        "settings",
        "SETTINGS",
        122,
        96,
        140,
        19,
        () => (overlay = "settings"),
      );
      button(
        "controls",
        "HOW TO PLAY",
        122,
        120,
        140,
        19,
        () => (overlay = "controls"),
      );
      button("leave", "LEAVE BATTLE", 122, 144, 140, 19, () => leaveBattle());
      return;
    }
    if (overlay === "controls") {
      panel(47, 26, 290, 165, C.gold);
      text("KEEPER'S FIELD GUIDE", 192, 39, C.gold, 1, "center");
      const guide = [
        "1. CHOOSE A HERO. TAP AN EMPTY TILE.",
        "2. GATHERERS CREATE QI FOR YOUR ARMY.",
        "3. SWORDS SHOOT RIGHT. MONKS BLOCK.",
        "4. SELECT A HERO. Q CASTS A FULL ULTIMATE.",
        "5. SPACE PAUSES. ESC CANCELS SELECTION.",
        "6. EACH LANE HAS ONE GUARDIAN SEAL RESCUE.",
        "7. COLUMN 0 IS RESERVED. DEPLOY IN 1-9.",
        "TIP: YUN IN THE MIDDLE, SHEN AHEAD OF HIM.",
        "FIRST THREATS: MIDDLE, THEN UPPER-MIDDLE.",
      ];
      guide.forEach((t, i) =>
        text(t, 61, 55 + i * 11, i >= 6 ? C.jade : C.muted),
      );
      button("close", "UNDERSTOOD", 119, 173, 146, 19, () => (overlay = null));
      return;
    }
    if (overlay === "saves") {
      panel(65, 22, 254, 174, C.gold);
      text("CHRONICLES OF THE KEEPER", 192, 34, C.gold, 1, "center");
      for (let i = 0; i < 3; i++) {
        const p = loadProfile(i);
        button(
          "slot-" + i,
          (i === slot ? "> " : "  ") +
            "SLOT " +
            (i + 1) +
            " / " +
            p.completed.length +
            " STAGES",
          80,
          54 + i * 25,
          224,
          20,
          () => {
            if (scene === "battle" && isPlaying(state))
              return notify(
                "LEAVE YOUR CURRENT BATTLE BEFORE SWITCHING.",
                C.red,
              );
            slot = i;
            profile = loadProfile(i);
            saveProfile();
            audio.update();
            notify("SLOT " + (i + 1) + " LOADED.", C.jade);
          },
          { active: i === slot },
        );
      }
      button("export", "EXPORT", 80, 135, 69, 18, exportSave);
      button("import", "IMPORT", 157, 135, 69, 18, () => fileInput.click());
      button("reset", "RESET", 234, 135, 70, 18, () => (overlay = "reset"));
      button("close", "BACK", 126, 165, 132, 18, () => (overlay = null));
      return;
    }
    if (overlay === "reset") {
      panel(71, 66, 242, 86, C.red);
      text("ERASE SLOT " + (slot + 1) + "?", 192, 79, C.red, 1, "center");
      text("THIS CANNOT BE UNDONE.", 192, 94, C.muted, 1, "center");
      button(
        "cancel",
        "KEEP SAVE",
        85,
        116,
        102,
        21,
        () => (overlay = "saves"),
      );
      button("erase", "ERASE", 195, 116, 102, 21, () => {
        profile = freshProfile();
        saveProfile();
        overlay = "saves";
        notify("THIS SAVE SLOT HAS BEEN RESET.");
      });
    }
  }
  function drawToast() {
    if (!toast || now > toast.until) return;
    const message =
        toast.message.length > 59
          ? toast.message.slice(0, 56) + "..."
          : toast.message,
      w = Math.min(372, message.length * 6 + 16),
      y = scene === "battle" ? 45 : 4;
    panel((W - w) / 2, y, w, 18, toast.color, "#14232c");
    text(message, W / 2, y + 5, toast.color, 1, "center");
  }
  function render(t) {
    now = t;
    buttons = [];
    ctx.setTransform(3, 0, 0, 3, 0, 0);
    ctx.imageSmoothingEnabled = false;
    if (scene === "title") drawTitle();
    else if (scene === "campaign") drawCampaign();
    else if (scene === "roster") drawRoster();
    else if (scene === "archive") drawArchive();
    else if (scene === "battle") drawBattle();
    if (overlay) buttons = [];
    if (overlay) {
      const offset = { x: (W - 384) / 2, y: (H - 216) / 2 },
        originalPointer = pointer;
      pointer = { x: pointer.x - offset.x, y: pointer.y - offset.y };
      ctx.save();
      ctx.translate(offset.x, offset.y);
      drawOverlay();
      ctx.restore();
      pointer = originalPointer;
      for (const b of buttons) {
        b.x += offset.x;
        b.y += offset.y;
        const action = b.fn;
        b.fn = (p) => action(p ? { x: p.x - offset.x, y: p.y - offset.y } : p);
      }
    }
    drawToast();
    canvas.dataset.scene =
      overlay === "settings"
        ? "settings"
        : scene === "battle" && state && !isPlaying(state)
          ? "results"
          : scene;
    canvas.dataset.battleId = battleId || "";
    canvas.style.cursor = buttons.some((b) => inside(pointer, b) && !b.disabled)
      ? "pointer"
      : "default";
    requestAnimationFrame(render);
  }
  function tileAt(p) {
    const col = Math.floor((p.x - B.x) / B.cw),
      lane = Math.floor((p.y - B.y) / B.ch);
    return col >= 1 && col <= 9 && lane >= 0 && lane < 5 ? { col, lane } : null;
  }
  function leaveBattle() {
    battleEpoch++;
    const old = battleId;
    battleId = null;
    state = null;
    selectedHero = null;
    inspectUnit = null;
    scene = "campaign";
    overlay = null;
    sessionStorage.removeItem("vanDao.battle");
    if (old) fetch("/api/battle/" + old, { method: "DELETE" }).catch(() => {});
  }
  function selectCard(id) {
    const h = heroes[id];
    if (!h || !unlocked(h))
      return notify("THIS CULTIVATOR HAS NOT JOINED YOUR SECT.", C.red);
    selectionEpoch++;
    selectedHero = selectedHero === id ? null : id;
    inspectUnit = null;
    audio.play("select");
  }
  async function api(url, data) {
    const r = await fetch(url, {
      method: data === undefined ? "GET" : "POST",
      headers: data === undefined ? {} : { "Content-Type": "application/json" },
      body: data === undefined ? undefined : JSON.stringify(data),
    });
    let out;
    try {
      out = await r.json();
    } catch {
      throw Error("The Python server returned an invalid response.");
    }
    if (!r.ok)
      throw Error(
        out.message ||
          out.error ||
          "The Python server could not complete this action.",
      );
    return out;
  }
  async function startBattle(id) {
    const epoch = ++battleEpoch;
    const old = battleId;
    battleId = null;
    sessionStorage.removeItem("vanDao.battle");
    overlay = null;
    selectedHero = null;
    inspectUnit = null;
    lastEvent = 0;
    seenEffects = new Set();
    resultApplied = false;
    state = null;
    scene = "battle";
    try {
      if (old)
        await fetch("/api/battle/" + old, { method: "DELETE" }).catch(() => {});
      if (epoch !== battleEpoch) return;
      battleStarted = performance.now();
      const seed = (Date.now() ^ ((slot + 1) * 10739)) >>> 0;
      const out = await api("/api/battle", {
        stage: id,
        seed,
        upgrades: profile.upgrades,
        realm: realm(),
      });
      if (epoch !== battleEpoch) {
        fetch("/api/battle/" + out.battle_id, { method: "DELETE" }).catch(
          () => {},
        );
        return;
      }
      battleId = out.battle_id;
      sessionStorage.setItem("vanDao.battle", battleId);
      acceptState(out.state);
      audio.play("start");
      if (!profile.completed.length && id === "wharf-1")
        notify(
          "SELECT YUN, THEN TAP A TILE. KEYS 1-8 SELECT HEROES.",
          C.jade,
          7,
        );
      if (!polling) {
        polling = true;
        poll();
      }
    } catch (e) {
      if (epoch !== battleEpoch) return;
      scene = "campaign";
      notify(e.message, C.red, 7);
    }
  }
  async function command(data) {
    const requested = battleId;
    if (!requested) return;
    const placing = data.action === "place";
    const selectedAtStart = selectionEpoch;
    if (placing && commandBusy) {
      notify("PLACEMENT IN PROGRESS.", C.muted, 1);
      return { ok: false, message: "Placement already in progress." };
    }
    if (placing) commandBusy = true;
    try {
      const out = await api("/api/battle/" + requested + "/command", data);
      if (requested !== battleId) return out;
      if (out.state) acceptState(out.state);
      if (!out.ok) {
        notify(out.message || "THAT ACTION IS NOT AVAILABLE.", C.red);
        audio.play("error");
      } else if (placing) {
        audio.hero(data.hero, "deploy");
        if (selectionEpoch === selectedAtStart && selectedHero === data.hero)
          selectedHero = null;
      } else if (data.action === "ultimate") audio.play("cast");
      return out;
    } catch (e) {
      if (requested === battleId) notify(e.message, C.red, 5);
      return { ok: false, message: e.message };
    } finally {
      if (placing) commandBusy = false;
    }
  }
  async function poll() {
    if (!battleId) {
      polling = false;
      return;
    }
    const requested = battleId;
    try {
      const snapshot = await api("/api/battle/" + requested);
      if (requested !== battleId) {
        setTimeout(poll, 50);
        return;
      }
      acceptState(snapshot);
      if (serverError) {
        serverError = false;
        notify("CONNECTION RESTORED.", C.jade);
      }
    } catch (e) {
      if (requested === battleId && !serverError) {
        serverError = true;
        notify("LOCAL SERVER DISCONNECTED. KEEP PYTHON RUNNING.", C.red, 8);
      }
    }
    setTimeout(poll, serverError ? 1500 : 50);
  }
  function acceptState(s) {
    if (s?.state) s = s.state;
    if (!s) return;
    previousState = state;
    state = s;
    stateReceived = performance.now();
    const activeEffects = new Set();
    for (const effect of s.effects || []) {
      activeEffects.add(effect.id);
      if (seenEffects.has(effect.id)) continue;
      const effectSound = {
        damage: "hit",
        hurt: "hit",
        kill: "kill",
        heal: "heal",
        qi: "qi",
        fire: "skill",
        lightning: "skill",
        slam: "skill",
        shield: "heal",
      }[effect.kind];
      if (effectSound) audio.play(effectSound);
    }
    seenEffects = activeEffects;
    for (const e of s.events || []) {
      if (Number(e.seq || 0) <= lastEvent) continue;
      lastEvent = Math.max(lastEvent, Number(e.seq || 0));
      const kind = e.kind || "";
      if (e.actor) audio.hero(e.actor, kind);
      if (
        [
          "warning",
          "phase",
          "boss",
          "breach",
          "altar",
          "drain",
          "guardian",
        ].includes(kind)
      ) {
        audio.play(kind === "altar" ? "upgrade" : "warning");
        notify(e.text, kind === "altar" ? C.jade : C.red, 2.5);
      }
      if (
        [
          "kill",
          "death",
          "place",
          "ultimate",
          "qi",
          "hit",
          "victory",
          "defeat",
          "orb",
          "skill",
        ].includes(kind)
      )
        audio.play(kind);
      if (
        e.x !== undefined &&
        e.lane !== undefined &&
        ["hit", "kill", "ultimate", "skill", "heal"].includes(kind)
      ) {
        for (let i = 0; i < (kind === "kill" ? 8 : 4); i++)
          particles.push({
            x: B.x + e.x * B.cw,
            y: B.y + (e.lane + 0.5) * B.ch,
            dx: Math.cos(i * 1.7) * 12,
            dy: Math.sin(i * 1.7) * 10 - 7,
            start: performance.now(),
            life: 450,
            color:
              kind === "heal"
                ? C.jade
                : kind === "ultimate"
                  ? C.violet
                  : C.gold,
          });
      }
    }
    if (!isPlaying(s) && !resultApplied) {
      resultApplied = true;
      if (["victory", "won"].includes(s.status)) {
        const first = !profile.completed.includes(s.stage);
        if (first) {
          profile.completed.push(s.stage);
          const reward = s.rewards || stages[s.stage]?.reward || {};
          profile.stones += Number(reward.stones ?? reward.spirit_stones ?? 0);
          profile.insight += Number(reward.insight || 0);
        }
        const old = profile.best[s.stage];
        if (!old || s.time < old.time)
          profile.best[s.stage] = {
            time: s.time,
            gate: s.gate,
            kills: s.kills,
          };
        saveProfile();
        audio.play("victory");
      } else audio.play("defeat");
    }
  }
  function exportSave() {
    saveProfile();
    const blob = new Blob(
      [JSON.stringify({ game: "van-dao", ...profile }, null, 2)],
      { type: "application/json" },
    );
    const url = URL.createObjectURL(blob),
      a = document.createElement("a");
    a.href = url;
    a.download = "van-dao-slot-" + (slot + 1) + ".json";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 3000);
    notify("SAVE FILE EXPORTED.", C.jade);
  }
  fileInput.addEventListener("change", async () => {
    try {
      const file = fileInput.files[0];
      if (!file) return;
      if (file.size > 1000000) throw Error("Save file is too large.");
      const data = JSON.parse(await file.text());
      if (
        data.version !== 1 ||
        !Array.isArray(data.completed) ||
        !data.upgrades
      )
        throw Error("This is not a compatible VAN DAO save.");
      profile = normalizeProfile(data);
      saveProfile();
      audio.update();
      notify("SAVE IMPORTED INTO SLOT " + (slot + 1) + ".", C.jade);
    } catch (e) {
      notify(e.message, C.red, 5);
    }
    fileInput.value = "";
  });
  const audio = {
    context: null,
    master: null,
    musicGain: null,
    sfxGain: null,
    step: 0,
    timer: null,
    last: {},
    heroCounts: {},
    theme: "lobby",
    nextNote: 0,
    init() {
      if (this.context) {
        if (this.context.state === "suspended") this.context.resume();
        return;
      }
      try {
        this.context = new (window.AudioContext || window.webkitAudioContext)();
        this.master = this.context.createGain();
        this.musicGain = this.context.createGain();
        this.sfxGain = this.context.createGain();
        this.musicGain.connect(this.master);
        this.sfxGain.connect(this.master);
        const limiter = this.context.createDynamicsCompressor();
        limiter.threshold.value = -8;
        limiter.knee.value = 6;
        limiter.ratio.value = 12;
        limiter.attack.value = 0.003;
        limiter.release.value = 0.15;
        this.master.connect(limiter);
        limiter.connect(this.context.destination);
        this.update();
        this.timer = setInterval(() => this.music(), 100);
      } catch {}
    },
    update() {
      if (!this.context) return;
      const t = this.context.currentTime;
      this.master.gain.setTargetAtTime(profile.settings.master * 0.4, t, 0.08);
      this.musicGain.gain.setTargetAtTime(profile.settings.music, t, 0.08);
      this.sfxGain.gain.setTargetAtTime(profile.settings.sfx, t, 0.08);
    },
    tone(f, d = 0.12, type = "triangle", volume = 0.2, bus = "sfx", delay = 0) {
      if (!this.context) return;
      const ac = this.context,
        t = ac.currentTime + delay,
        o = ac.createOscillator(),
        g = ac.createGain();
      o.type = type;
      o.frequency.setValueAtTime(f, t);
      o.connect(g);
      g.connect(bus === "music" ? this.musicGain : this.sfxGain);
      g.gain.setValueAtTime(0.001, t);
      g.gain.exponentialRampToValueAtTime(Math.max(0.002, volume), t + 0.008);
      g.gain.exponentialRampToValueAtTime(0.001, t + d);
      o.start(t);
      o.stop(t + d + 0.02);
    },
    noise(duration = 0.09, volume = 0.08, filter = 1800) {
      if (!this.context) return;
      const ac = this.context,
        count = Math.floor(ac.sampleRate * duration),
        b = ac.createBuffer(1, count, ac.sampleRate),
        data = b.getChannelData(0);
      for (let i = 0; i < count; i++)
        data[i] = (Math.random() * 2 - 1) * (1 - i / count) ** 2;
      const source = ac.createBufferSource(),
        gain = ac.createGain(),
        low = ac.createBiquadFilter();
      source.buffer = b;
      low.type = "lowpass";
      low.frequency.value = filter;
      gain.gain.value = volume;
      source.connect(low);
      low.connect(gain);
      gain.connect(this.sfxGain);
      source.start();
    },
    hero(actor, action) {
      if (!this.context) return;
      const stamp = performance.now(),
        key = "hero-" + actor;
      if (stamp - (this.last[key] || 0) < 150) return;
      this.last[key] = stamp;
      this.heroCounts[actor] = (this.heroCounts[actor] || 0) + 1;
      const profiles = {
        gatherer: { notes: [880, 1320, 1760], wave: "sine", decay: 0.22 },
        sword: {
          notes: [440, 660],
          wave: "triangle",
          decay: 0.065,
          noise: 4200,
        },
        fire: {
          notes: [147, 294, 392],
          wave: "sawtooth",
          decay: 0.14,
          noise: 900,
        },
        frost: {
          notes: [1175, 1568, 2349],
          wave: "sine",
          decay: 0.16,
          noise: 6500,
        },
        monk: {
          notes: [82, 123, 164],
          wave: "triangle",
          decay: 0.18,
          noise: 450,
        },
        lightning: {
          notes: [740, 1480, 370],
          wave: "square",
          decay: 0.045,
          noise: 8000,
        },
        herbalist: { notes: [523, 659, 784], wave: "sine", decay: 0.25 },
        formation: {
          notes: [196, 294, 392, 588],
          wave: "triangle",
          decay: 0.3,
        },
      };
      const p = profiles[actor];
      if (!p) return;
      const ultimate = action === "ultimate";
      p.notes.forEach((n, i) =>
        this.tone(
          n * (ultimate ? 1.5 : 1),
          p.decay * (ultimate ? 2 : 1),
          p.wave,
          0.1,
          "sfx",
          i * (ultimate ? 0.08 : 0.025),
        ),
      );
      if (p.noise) this.noise(ultimate ? 0.2 : 0.07, 0.06, p.noise);
    },
    play(kind) {
      if (!this.context) return;
      const t = performance.now();
      if (t - (this.last[kind] || 0) < (kind === "hit" ? 100 : 35)) return;
      this.last[kind] = t;
      const sounds = {
        select: [523, 0.06, "triangle", 0.16],
        confirm: [659, 0.1, "triangle", 0.25],
        place: [392, 0.17, "triangle", 0.25],
        start: [262, 0.3, "triangle", 0.22],
        qi: [880, 0.16, "sine", 0.2],
        orb: [1047, 0.1, "sine", 0.15],
        hit: [176, 0.035, "square", 0.1],
        kill: [147, 0.1, "triangle", 0.18],
        death: [110, 0.14, "triangle", 0.15],
        error: [98, 0.12, "sawtooth", 0.13],
        cast: [784, 0.25, "triangle", 0.25],
        ultimate: [784, 0.3, "triangle", 0.26],
        skill: [659, 0.09, "triangle", 0.14],
        upgrade: [988, 0.3, "sine", 0.25],
        heal: [698, 0.15, "sine", 0.12],
        warning: [196, 0.28, "square", 0.16],
      };
      if (kind === "victory") {
        [523, 659, 784, 1047].forEach((n, i) =>
          this.tone(n, 0.35, "triangle", 0.25, "sfx", i * 0.13),
        );
        return;
      }
      if (kind === "defeat") {
        [262, 247, 196].forEach((n, i) =>
          this.tone(n, 0.45, "triangle", 0.22, "sfx", i * 0.2),
        );
        return;
      }
      if (sounds[kind]) this.tone(...sounds[kind]);
    },
    music() {
      if (!this.context || !profile.settings.music || document.hidden) return;
      if (scene === "battle" && state?.paused) return;
      const theme = scene === "battle" ? state?.region || "wharf" : "lobby";
      if (theme !== this.theme) {
        this.theme = theme;
        this.step = 0;
        this.nextNote = 0;
      }
      const scores = {
        lobby: {
          bpm: 76,
          root: 48,
          lead: "triangle",
          melody: [
            12, 16, 19, 24, 19, 16, 14, 16, 12, 7, 12, 14, 16, 19, 16, 7, 9, 12,
            16, 21, 19, 16, 14, 12, 7, 9, 12, 16, 14, 7, 4, 7,
          ],
        },
        wharf: {
          bpm: 104,
          root: 45,
          lead: "triangle",
          melody: [
            12, 15, 19, 22, 24, 19, 15, 12, 10, 12, 15, 19, 22, 19, 15, 7, 12,
            15, 17, 24, 22, 19, 17, 15, 10, 7, 10, 15, 19, 17, 15, 12,
          ],
        },
        terrace: {
          bpm: 90,
          root: 50,
          lead: "sine",
          melody: [
            12, 19, 24, 26, 24, 19, 16, 14, 12, 16, 19, 21, 24, 21, 19, 16, 14,
            19, 21, 26, 28, 26, 24, 19, 16, 14, 12, 7, 9, 12, 16, 19,
          ],
        },
        tomb: {
          bpm: 84,
          root: 38,
          lead: "triangle",
          melody: [
            12, 13, 19, 24, 22, 19, 13, 12, 7, 12, 15, 19, 18, 15, 13, 7, 12,
            19, 25, 24, 19, 18, 15, 13, 12, 7, 6, 7, 12, 13, 7, 0,
          ],
        },
      };
      const score = scores[theme],
        ac = this.context;
      if (this.nextNote > ac.currentTime + 0.12) return;
      if (this.nextNote < ac.currentTime) this.nextNote = ac.currentTime + 0.02;
      const i = this.step++,
        beat = 60 / score.bpm / 2,
        delay = this.nextNote - ac.currentTime,
        hz = (n) => 440 * 2 ** ((score.root + n - 69) / 12);
      this.tone(
        hz(score.melody[i % 32]),
        theme === "terrace" ? 0.38 : 0.22,
        score.lead,
        0.1,
        "music",
        delay,
      );
      if (i % 4 === 0) {
        this.tone(
          hz([0, 5, 7, 0][Math.floor(i / 8) % 4] - 12),
          beat * 3.6,
          "sine",
          0.12,
          "music",
          delay,
        );
        this.tone(55, 0.09, "sine", 0.12, "music", delay);
      }
      if (i % 8 === 4)
        this.tone(hz(7), 0.05, "triangle", 0.045, "music", delay);
      if (i % 16 === 0) {
        this.tone(hz(12), beat * 7, "sine", 0.025, "music", delay);
        this.tone(hz(19), beat * 7, "sine", 0.02, "music", delay);
      }
      if (
        scene === "battle" &&
        state?.enemies?.some((e) => e.boss) &&
        i % 2 === 0
      )
        this.tone(73, 0.07, "triangle", 0.09, "music", delay);
      this.nextNote += beat;
    },
  };
  function point(event) {
    const r = canvas.getBoundingClientRect();
    return {
      x: ((event.clientX - r.left) * W) / r.width,
      y: ((event.clientY - r.top) * H) / r.height,
    };
  }
  canvas.addEventListener("pointermove", (e) => {
    pointer = point(e);
  });
  canvas.addEventListener("pointerleave", () => (pointer = { x: -1, y: -1 }));
  canvas.addEventListener("pointerdown", async (e) => {
    e.preventDefault();
    canvas.focus();
    pointer = point(e);
    audio.init();
    if (e.button === 2) {
      selectedHero = null;
      inspectUnit = null;
      return;
    }
    const target = [...buttons].reverse().find((b) => inside(pointer, b));
    if (target) {
      if (!target.disabled) {
        audio.play("select");
        target.fn(pointer);
      }
      return;
    }
    if (overlay) return;
    if (scene !== "battle" || !state || !isPlaying(state) || state.paused)
      return;
    const tile = tileAt(pointer);
    if (selectedHero && tile) {
      await command({
        action: "place",
        hero: selectedHero,
        lane: tile.lane,
        col: tile.col,
      });
      return;
    }
    if (selectedHero) {
      if (
        pointer.x >= B.x &&
        pointer.x < B.x + B.cw &&
        pointer.y >= B.y &&
        pointer.y < B.y + 5 * B.ch
      ) {
        notify(
          "Guardian seals occupy column 0: one automatic lane rescue. Deploy to their right.",
          C.gold,
          5,
        );
        return;
      }
      selectedHero = null;
      return;
    }
    const unit = (state.heroes || []).find(
      (u) =>
        Math.abs(unitX(u) - pointer.x) < 16 &&
        Math.abs(unitY(u) - 15 - pointer.y) < 19,
    );
    inspectUnit = unit ? unit.id : null;
  });
  canvas.addEventListener("contextmenu", (e) => {
    e.preventDefault();
    selectedHero = null;
    inspectUnit = null;
  });
  addEventListener("keydown", (e) => {
    if (
      ["Space", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(
        e.code,
      )
    )
      e.preventDefault();
    audio.init();
    if (e.code === "Escape") {
      if (overlay) overlay = null;
      else if (selectedHero || inspectUnit !== null) {
        selectedHero = null;
        inspectUnit = null;
      } else if (scene === "battle") {
        command({ action: "pause", paused: true });
        overlay = "battleMenu";
      }
      return;
    }
    if (scene !== "battle" || overlay || !state || !isPlaying(state)) return;
    if (e.code === "Space") command({ action: "pause", paused: !state.paused });
    else if (/^[1-8]$/.test(e.key)) selectCard(heroOrder[Number(e.key) - 1]);
    else if (e.code === "KeyQ" && inspectUnit !== null)
      command({ action: "ultimate", unit: inspectUnit });
  });
  function resize() {
    const w = innerWidth,
      h = innerHeight,
      fit = Math.min(w / W, h / H);
    const scale = profile.settings.integer && fit >= 1 ? Math.floor(fit) : fit;
    canvas.style.width = Math.floor(W * scale) + "px";
    canvas.style.height = Math.floor(H * scale) + "px";
  }
  addEventListener("resize", resize);
  document.addEventListener("visibilitychange", () => {
    if (
      document.hidden &&
      scene === "battle" &&
      isPlaying(state) &&
      !state.paused
    )
      command({ action: "pause", paused: true });
  });
  function loadImage(url) {
    return new Promise((resolve) => {
      const im = new Image();
      im.onload = () => resolve(im);
      im.onerror = () => resolve(null);
      im.src = url;
    });
  }
  async function init() {
    try {
      await document.fonts.load("13px VT323");
      await document.fonts.ready;
      catalog = await api("/api/catalog");
      for (const key of ["heroes", "enemies", "stages", "relics"])
        if (!Array.isArray(catalog[key]))
          catalog[key] = Object.values(catalog[key] || {});
      heroes = Object.fromEntries(catalog.heroes.map((h) => [h.id, h]));
      enemies = Object.fromEntries(catalog.enemies.map((h) => [h.id, h]));
      stages = Object.fromEntries(catalog.stages.map((s) => [s.id, s]));
      const names = ["title", "wharf", "terrace", "tomb", "sprites"];
      const assets = await Promise.all(
        names.map((name) => loadImage("/assets/" + name + ".png")),
      );
      names.forEach((n, i) => (images[n] = assets[i]));
      try {
        const r = await fetch("/assets/sprites.json");
        atlas = await r.json();
        if (atlas.sprites) atlas = atlas.sprites;
      } catch {}
      document.getElementById("loading").hidden = true;
      resize();
      requestAnimationFrame(render);
      live.textContent = "Ready. Begin your campaign.";
      const resume = sessionStorage.getItem("vanDao.battle");
      if (resume && !battleId) {
        try {
          const s = await api("/api/battle/" + resume);
          if (isPlaying(s) && !battleId && scene === "title") {
            battleId = resume;
            acceptState(s);
            command({ action: "pause", paused: true });
            polling = true;
            poll();
          }
        } catch {
          sessionStorage.removeItem("vanDao.battle");
        }
      }
    } catch (e) {
      document.querySelector("#loading span").textContent =
        e.message + " Keep the Python server running and reload.";
    }
  }
  window.VanDao = {
    startBattle,
    command,
    get state() {
      return state;
    },
    get scene() {
      return scene;
    },
    get profile() {
      return JSON.parse(JSON.stringify(profile));
    },
    get catalog() {
      return catalog;
    },
    get buttons() {
      return buttons.map(({ id, x, y, w, h, disabled }) => ({
        id,
        x,
        y,
        w,
        h,
        disabled,
      }));
    },
    get audioTheme() {
      return audio.theme;
    },
    get heroSounds() {
      return { ...audio.heroCounts };
    },
    get board() {
      return { ...B };
    },
    get audioActive() {
      return !!audio.context && audio.context.state === "running";
    },
    showCampaign() {
      scene = "campaign";
      overlay = null;
    },
    save: saveProfile,
  };
  init();
})();
