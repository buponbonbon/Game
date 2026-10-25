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
    atlas = {},
    cultivators = {},
    guardianAtlas = {},
    previews = {},
    previewSignature = "",
    previewEpoch = 0;
  let voiceCaption = null,
    abilityBursts = [],
    tutorialPage = 0,
    tutorialReturn = null,
    sceneArt = { regions: {} };
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
  let rangeMode = "basic",
    libraryTab = "skill",
    libraryEnemy = false,
    libraryHero = "sword",
    rosterMode = "talents",
    selectedNode = { branch: "A", rank: 1 };
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
      music: 0.38,
      sfx: 0.65,
      voice: 0.8,
      shake: true,
      integer: false,
      autoUltimate: false,
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
    for (const [k, b] of Object.entries(v.upgrades || {})) {
      if (!heroOrder.includes(k)) continue;
      if (["A", "B"].includes(b)) d.upgrades[k] = b;
      else if (
        b &&
        ["A", "B"].includes(b.branch) &&
        Number.isInteger(b.rank) &&
        b.rank >= 0 &&
        b.rank <= 5
      )
        d.upgrades[k] = { branch: b.branch, rank: b.rank };
    }
    d.best = v.best && typeof v.best === "object" ? v.best : {};
    for (const k of ["master", "music", "sfx", "voice"]) {
      const value = Number(v.settings?.[k] ?? d.settings[k]);
      d.settings[k] = Number.isFinite(value)
        ? Math.max(0, Math.min(1, value))
        : d.settings[k];
    }
    for (const k of ["shake", "integer", "autoUltimate"])
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
    refreshPreviews();
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
    const r = {
      id,
      label,
      x,
      y,
      w,
      h,
      fn,
      disabled: !!opt.disabled,
      talentState: opt.talentState,
    };
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
    if (opt.talentState) {
      const owned = opt.talentState === "learned",
        next = opt.talentState === "available";
      panel(
        x,
        y,
        w,
        h,
        owned ? C.gold : next ? C.jade : opt.active ? "#91989f" : "#414a51",
        owned ? "#254d43" : "#222831",
      );
      if (owned) {
        rect(x + 4, y + 6, 5, 5, C.gold);
        line(x + 5, y + 8, x + 6, y + 10, C.deep);
        line(x + 6, y + 10, x + 9, y + 6, C.deep);
      } else {
        rect(x + 4, y + 7, 5, 5, next ? "#99b9ad" : "#69737b");
        line(x + 5, y + 7, x + 5, y + 4, next ? C.jade : C.dim);
        line(x + 5, y + 4, x + 8, y + 4, next ? C.jade : C.dim);
        line(x + 8, y + 4, x + 8, y + 7, next ? C.jade : C.dim);
      }
    }
    text(
      String(label).slice(0, Math.max(1, Math.floor((w - 10) / 6.5))),
      x + w / 2,
      y + (h - 7) / 2,
      opt.talentState
        ? opt.talentState === "learned"
          ? C.gold
          : opt.talentState === "available"
            ? "#a0b9ae"
            : "#6d7880"
        : r.disabled
          ? C.dim
          : opt.active
            ? C.gold
            : opt.color || C.cream,
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
    if (images[name])
      ctx.drawImage(
        images[name],
        0,
        sceneArt.regions[name]?.draw_y || 0,
        W,
        sceneArt.regions[name]?.draw_height || H,
      );
    else rect(0, 0, W, H, C.ink);
    if (shade) {
      ctx.fillStyle = `rgba(7,14,21,${shade})`;
      ctx.fillRect(0, 0, W, H);
    }
  }
  function sprite(
    id,
    x,
    y,
    scale = 1,
    frame = null,
    alpha = 1,
    action = "idle",
    started = 0,
  ) {
    const hero = cultivators[id];
    if (hero && images.cultivators) {
      const pose =
        hero.states[action === "deploy" ? "skill" : action] || hero.states.idle;
      const clock = scene === "battle" ? state?.time || 0 : now / 1000;
      const duration =
        action === "ultimate"
          ? 1.2
          : action === "attack"
            ? (previews[id]?.windup || 0.35) + 0.25
            : 0.5;
      const f =
        action !== "idle" && scene === "battle"
          ? Math.min(
              pose.frames - 1,
              Math.floor(
                (Math.max(0, clock - started) / duration) * pose.frames,
              ),
            )
          : Math.floor(clock * pose.fps) % pose.frames;
      ctx.globalAlpha = alpha;
      ctx.drawImage(
        images.cultivators,
        pose.x + f * hero.w,
        pose.y,
        hero.w,
        hero.h,
        Math.round(x),
        Math.round(y),
        32 * scale,
        32 * scale,
      );
      ctx.globalAlpha = 1;
      return;
    }
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
    const t = now / 1000;
    for (let i = 0; i < 6; i++) {
      const x = (i * 97 + t * 5) % W,
        y = 35 + i * 18;
      ctx.globalAlpha = 0.12;
      rect(x, y, 38, 2, C.jade);
      rect(x + 9, y - 2, 23, 2, C.cream);
      ctx.globalAlpha = 1;
    }
    text("THE LAST IMMORTAL GATE", 28, 18, C.muted);
    text("VAN DAO", 29, 43, C.deep, 3);
    text("VAN DAO", 27, 41, C.cream, 3);
    text("IMMORTAL WAR", 29, 82, C.gold, 1.35);
    wrapped(
      "Study the Dao. Shape your formation. Keep the immortal gate alive.",
      29,
      110,
      190,
      C.jade,
      14,
      3,
    );
    button(
      "begin",
      profile.completed.length ? "CONTINUE CAMPAIGN" : "BEGIN CAMPAIGN",
      28,
      160,
      194,
      28,
      () => {
        scene = "campaign";
        audio.play("confirm");
      },
    );
    button("roster", "CULTIVATION / TALENTS", 28, 194, 194, 25, () => {
      scene = "roster";
    });
    button(
      "archive",
      "MONSTER ARCHIVE",
      28,
      225,
      194,
      25,
      () => (scene = "archive"),
    );
    button("saves", "CHRONICLES", 28, 257, 94, 22, () => (overlay = "saves"));
    button(
      "settings",
      "SETTINGS",
      128,
      257,
      94,
      22,
      () => (overlay = "settings"),
    );
    panel(271, 39, 216, 57, C.edge, "#122833d9");
    text("KEEPER'S SANCTUARY", 379, 47, C.gold, 1.2, "center");
    text(
      `Chronicle ${slot + 1} / ${profile.completed.length} of 9 encounters`,
      379,
      70,
      C.cream,
      1,
      "center",
    );
    sprite("sword", 304, 132 + Math.sin(t * 1.4) * 2, 2.6);
    for (let i = 0; i < 5; i++) {
      const a = t * 0.5 + i * 1.26;
      rect(
        350 + Math.cos(a) * 48,
        177 + Math.sin(a) * 22,
        2,
        2,
        i % 2 ? C.jade : C.gold,
      );
    }
    const names = ["LANTERN WHARF", "AZURE TERRACES", "BONE MAUSOLEUM"];
    names.forEach((name, i) => {
      const x = 278 + i * 68;
      panel(x, 227, 64, 28, [C.jade, C.ice, C.violet][i]);
      text(
        ["RIVER", "SKY", "TOMB"][i],
        x + 32,
        236,
        [C.jade, C.ice, C.violet][i],
        0.95,
        "center",
      );
    });
    text("Guqin / Guzheng / Dizi", 379, 264, C.muted, 0.95, "center");
    if (battleId && state && isPlaying(state))
      button("resume", "RESUME BATTLE", 281, 103, 196, 24, () => {
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
  function talentProgress(id) {
    const value = profile.upgrades[id];
    return typeof value === "string"
      ? { branch: value, rank: 3 }
      : value || { branch: null, rank: 0 };
  }
  async function refreshPreviews() {
    if (!catalog.heroes.length) return;
    const signature = JSON.stringify(profile.upgrades);
    if (signature === previewSignature) return;
    previewSignature = signature;
    const epoch = ++previewEpoch;
    try {
      const result = await api("/api/hero-preview", {
        upgrades: profile.upgrades,
      });
      if (epoch === previewEpoch)
        previews = Object.fromEntries(result.heroes.map((h) => [h.id, h]));
    } catch (e) {
      previewSignature = "";
      notify("Restart the Python server to load the new rules.", C.red, 5);
    }
  }
  function showSkills(id, enemy = false) {
    libraryHero = id || "sword";
    libraryEnemy = enemy;
    libraryTab = "skill";
    if (scene === "battle" && isPlaying(state))
      command({ action: "pause", paused: true });
    overlay = "skills";
  }
  function skillDetails(h, tab, x, y, width) {
    const ability =
      tab === "basic" ? h.basic : tab === "ultimate" ? h.ultimate : h.skill;
    if (!ability) return;
    text(ability.name, x, y, C.gold, 1.15);
    const cd =
      tab === "basic"
        ? h.id === "gatherer"
          ? h.orb_interval
          : h.id === "herbalist"
            ? h.heal_interval
            : h.interval
        : ability.cooldown;
    text(
      `${tab === "basic" && h.id === "formation" ? "Continuous aura / base interval" : "Cooldown"} ${Number(cd || 0).toFixed(1)}s / Mana ${ability.mana_cost || 0}` +
        (tab === "ultimate" ? ` / Qi ${ability.qi_cost} / Dao 100` : ""),
      x,
      y + 18,
      C.ice,
    );
    wrapped(
      `Scaling: ${ability.scaling || "Fixed effect"}` +
        (ability.power ? ` = ${ability.power} before armor` : ""),
      x,
      y + 34,
      width,
      C.cream,
      12,
      2,
    );
    wrapped(
      ability.geometry?.description || "Self only.",
      x,
      y + 61,
      width,
      C.jade,
      12,
      2,
    );
    const target = ability.targets || ability.geometry?.targets;
    text(
      `Targets: ${target >= 99 ? "all eligible" : target || 1}`,
      x,
      y + 87,
      C.muted,
    );
    wrapped(
      ability.description || h.description,
      x,
      y + 103,
      width,
      C.cream,
      12,
      4,
    );
  }
  function buyTalent(id) {
    const h = heroes[id],
      current = talentProgress(id),
      { branch, rank } = selectedNode;
    if (battleId && isPlaying(state))
      return notify(
        "Finish or leave the current battle before changing talents.",
        C.gold,
      );
    if (!unlocked(h)) return notify("Clear the required chapter first.", C.red);
    if (current.branch && current.branch !== branch)
      return notify("This cultivator follows the other path.", C.red);
    if (rank !== current.rank + 1)
      return notify("Unlock the preceding node first.", C.red);
    const node = h.talents[branch][rank - 1];
    if (profile.stones < node.cost)
      return notify(
        `Need ${node.cost - profile.stones} more Spirit Stones.`,
        C.red,
      );
    profile.stones -= node.cost;
    profile.upgrades[id] = { branch, rank };
    saveProfile();
    audio.play("upgrade");
    notify(node.name + " awakened.", C.jade);
  }
  function drawRoster() {
    bg("title", 0.75);
    header("CULTIVATION HALL", () => (scene = "campaign"));
    const h = previews[rosterHero] || heroes[rosterHero] || catalog.heroes[0];
    heroOrder.forEach((id, i) => {
      button(
        "hero-" + id,
        shortNames[id] + (unlocked(heroes[id]) ? "" : " / LOCK"),
        8,
        34 + i * 30,
        104,
        27,
        () => {
          rosterHero = id;
          selectedNode = {
            branch: talentProgress(id).branch || "A",
            rank: Math.min(5, talentProgress(id).rank + 1),
          };
        },
        { active: rosterHero === id },
      );
      sprite(id, 8, 28 + i * 30, 0.8);
    });
    panel(121, 32, 382, 247, C.edge);
    sprite(h.id, 130, 37, 1.7);
    text(h.name, 193, 39, C.gold, 1.25);
    text(`${h.hp} HP / ${h.damage} ATK / ${h.cost} Qi`, 193, 57);
    text(
      `Mana ${h.mana_max} / Regen ${h.mana_regen.toFixed(2)}/s`,
      193,
      74,
      C.ice,
    );
    button(
      "roster-talents",
      "TALENT TREE",
      131,
      96,
      173,
      21,
      () => (rosterMode = "talents"),
      { active: rosterMode === "talents" },
    );
    button(
      "roster-skills",
      "SKILL DETAILS",
      310,
      96,
      182,
      21,
      () => showSkills(h.id),
      { active: rosterMode === "skills" },
    );
    if (rosterMode === "skills") {
      for (const [i, tab] of ["basic", "skill", "ultimate"].entries())
        button(
          "roster-tab-" + tab,
          tab,
          132 + i * 120,
          122,
          116,
          20,
          () => (libraryTab = tab),
          { active: libraryTab === tab },
        );
      skillDetails(h, libraryTab, 134, 150, 350);
      return;
    }
    text("GOLD learned / JADE next / GREY locked", 193, 86, C.muted, 0.7);
    const progress = talentProgress(h.id);
    for (const [i, branch] of ["A", "B"].entries()) {
      const x = 132 + i * 181;
      text(
        "PATH " + branch,
        x + 85,
        122,
        progress.branch === branch ? C.gold : C.jade,
        1,
        "center",
      );
      for (const node of h.talents[branch]) {
        const y = 137 + (node.rank - 1) * 21,
          owned = progress.branch === branch && progress.rank >= node.rank;
        if (node.rank > 1) line(x + 8, y - 3, x + 8, y + 1, C.edge);
        button(
          "talent-" + branch + node.rank,
          (owned ? "* " : node.kind === "special" ? "+ " : "") +
            node.rank +
            " " +
            node.name,
          x,
          y,
          172,
          19,
          () => (selectedNode = { branch, rank: node.rank }),
          {
            active:
              selectedNode.branch === branch && selectedNode.rank === node.rank,
            color: node.kind === "special" ? C.gold : C.cream,
            talentState: owned
              ? "learned"
              : unlocked(h) &&
                  (!progress.branch || progress.branch === branch) &&
                  node.rank === progress.rank + 1
                ? "available"
                : "locked",
          },
        );
      }
    }
    const node = h.talents[selectedNode.branch][selectedNode.rank - 1];
    wrapped(node.description, 133, 247, 270, C.jade, 11, 2);
    button(
      "buy-talent",
      "BUY " + node.cost,
      410,
      249,
      82,
      25,
      () => buyTalent(h.id),
      {
        disabled:
          !unlocked(h) ||
          (progress.branch && progress.branch !== selectedNode.branch) ||
          selectedNode.rank !== progress.rank + 1 ||
          profile.stones < node.cost,
      },
    );
  }
  function drawArchive() {
    bg("tomb", 0.75);
    header("MONSTER ARCHIVE", () => (scene = "campaign"));
    button("archive-ranks", "RANKS", 204, 4, 65, 19, () => (overlay = "ranks"));
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
    text(
      `Base HP ${e.hp} / Armor ${e.armor} / Shield ${e.shield || 0}`,
      207,
      115,
    );
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
  function drawRanges(s) {
    let actor = (s.heroes || []).find(
      (u) =>
        Math.abs(unitX(u) - pointer.x) < 16 &&
        pointer.y > unitY(u) - 32 &&
        pointer.y < unitY(u) + 3,
    );
    let h = actor?.stats,
      anchor = actor ? { x: actor.x, lane: actor.lane } : null;
    if (!actor && selectedHero) {
      h = previews[selectedHero] || heroes[selectedHero];
      const tile = tileAt(pointer);
      if (tile) anchor = { x: tile.col + 0.5, lane: tile.lane };
    }
    if (!actor && !h && pointer.y >= 241) {
      const index = Math.floor((pointer.x - 88) / 52);
      if (index >= 0 && index < 8) {
        h = previews[heroOrder[index]] || heroes[heroOrder[index]];
        anchor = { x: 2.5, lane: 2 };
      }
    }
    let enemy = false;
    if (!h) {
      actor = (s.enemies || []).find(
        (u) =>
          Math.abs(unitX(u) - pointer.x) < 16 &&
          pointer.y > unitY(u) - 32 &&
          pointer.y < unitY(u) + 3,
      );
      if (actor) {
        h = enemies[actor.type];
        anchor = { x: actor.x, lane: actor.lane };
        enemy = true;
      }
    }
    if (!h || !anchor) return;
    const ability = enemy
      ? rangeMode === "basic"
        ? { geometry: h.basic_geometry }
        : h.abilities?.[0]
      : rangeMode === "basic"
        ? h.basic
        : h[rangeMode];
    const scope = ability?.geometry;
    if (!scope) return;
    const color = enemy
      ? C.red
      : rangeMode === "ultimate"
        ? C.gold
        : rangeMode === "skill"
          ? C.ice
          : C.jade;
    for (let row = 0; row < 5; row++)
      for (let col = 1; col <= 11; col++) {
        const dx = col + 0.5 - anchor.x,
          dy = row - anchor.lane,
          r = scope.radius;
        const lanes =
          enemy && scope.shape === "lanes"
            ? actor.type === "riverlord"
              ? [actor.lane, (actor.lane + 1) % 5]
              : actor.type === "mountainlord"
                ? [...Array(5).keys()]
                    .sort(
                      (a, b) =>
                        s.heroes.filter((h) => h.lane === b).length -
                          s.heroes.filter((h) => h.lane === a).length || b - a,
                    )
                    .slice(0, 2)
                : s.telegraphs.find((t) => t.kind === "ROYAL DECREE")
                    ?.lanes || [0, 1, 2, 3, 4]
            : [];
        const match =
          (scope.shape === "lanes" && lanes.includes(row)) ||
          scope.shape === "field" ||
          (scope.shape === "lane"
            ? dy === 0
            : scope.shape === "self"
              ? Math.abs(dx) < 0.1 && dy === 0
              : scope.shape === "circle"
                ? Math.hypot(dx, dy) <= r
                : scope.shape === "front_circle"
                  ? dx >= -0.3 && Math.hypot(dx, dy) <= r
                  : dy === 0 &&
                    (enemy ? dx <= 0.3 && -dx <= r : dx >= -0.3 && dx <= r));
        if (match && !(scope.exclude_self && Math.abs(dx) < 0.1 && dy === 0)) {
          ctx.globalAlpha = 0.17;
          rect(
            B.x + col * B.cw + 1,
            B.y + row * B.ch + 1,
            B.cw - 2,
            B.ch - 2,
            color,
          );
          ctx.globalAlpha = 1;
          line(
            B.x + col * B.cw + 2,
            B.y + row * B.ch + 2,
            B.x + (col + 1) * B.cw - 3,
            B.y + row * B.ch + 2,
            color,
          );
        }
      }
    const label =
      scope.shape === "circle"
        ? `radius ${scope.radius} / ${scope.offsets.length} centers`
        : scope.shape === "line"
          ? `same lane / ${scope.radius} tiles`
          : scope.shape === "lanes"
            ? "marked lanes"
            : scope.shape === "lane"
              ? "whole lane"
              : scope.shape === "field"
                ? "whole board"
                : scope.shape === "front_circle"
                  ? `front arc ${scope.radius} tiles`
                  : "self";
    panel(130, 221, 373, 17, color);
    text(h.name + " / " + rangeMode + " / " + label, 137, 224, color, 0.78);
  }
  function drawBattle() {
    const s = state;
    if (!s) {
      bg("title", 0.8);
      text("AWAKENING THE FORMATION...", 192, 105, C.jade, 1, "center");
      return;
    }
    bg(s.region || "wharf");
    drawRanges(s);
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
          tile.corrupted ? C.red : C.jade,
        );
        if (tile.corrupted)
          text(
            "CORRUPT",
            B.x + tile.col * B.cw + 16,
            B.y + tile.lane * B.ch + 23,
            C.red,
            0.6,
            "center",
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
    drawMapEffects(s);
    drawAmbient(s.region || "wharf");
    window.VanDaoBattleArt.effects(ctx, s, abilityBursts, B, text, "floor");
    const units = [
      ...(s.heroes || []).map((x) => ({ ...x, friendly: true })),
      ...(s.enemies || []).map((x) => ({ ...x, friendly: false })),
    ].sort((a, b) => a.lane - b.lane || a.x - b.x);
    for (const u of units) {
      let x = renderedX(u),
        y = unitY(u),
        size = u.friendly
          ? u.action === "ultimate"
            ? 42
            : u.action === "skill"
              ? 36
              : 32
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
        u.action,
        u.action_started || 0,
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
        rect(x - 11, y - 23, 22, 2, C.deep);
        rect(x - 11, y - 23, 22 * clamp(u.mana / u.mana_max, 0, 1), 2, C.ice);
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
      if (["elite", "captain"].includes(u.rank))
        text(
          u.rank === "captain" ? "CAPT" : "ELITE",
          x,
          y - 36,
          C.gold,
          0.65,
          "center",
        );
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
    window.VanDaoBattleArt.effects(ctx, s, abilityBursts, B, text, "front");
    drawHUD(s);
    drawCards(s);
    const unit = (s.heroes || []).find((h) => h.id === inspectUnit);
    if (unit && !selectedHero) drawInspect(unit);
    if (s.paused && !overlay) {
      panel(142, 61, 222, 29, C.gold);
      text("PAUSED", 151, 70, C.gold, 0.9);
      button("resume", "RESUME", 205, 66, 73, 19, () =>
        command({ action: "pause", paused: false }),
      );
      button("pause-skills", "SKILLS", 283, 66, 73, 19, () =>
        showSkills(
          inspectUnit
            ? state.heroes.find((u) => u.id === inspectUnit)?.type
            : "sword",
        ),
      );
    }
    if (!isPlaying(s)) drawResults();
    if (W / H > innerWidth / innerHeight + 1 && innerWidth < 600) {
      panel(91, 4, 202, 17, C.gold);
      text("ROTATE FOR A WIDER BATTLEFIELD", 192, 9, C.gold, 1, "center");
    }
  }
  function drawMapEffects(s) {
    const t = s.time;
    if (s.region === "wharf") {
      for (let i = 0; i < 16; i++) {
        const x = (i * 37 + t * 10) % 512,
          y = 222 + (i % 3) * 3;
        ctx.globalAlpha = 0.22;
        rect(x, y, 10, 1, C.ice);
        ctx.globalAlpha = 1;
      }
      const flooded = ["HIGH TIDE", "RISING"].includes(s.hazard.phase);
      for (const tile of s.hazard.tiles || [])
        if (tile.type === "water") {
          const x = B.x + tile.col * 32,
            y = B.y + tile.lane * 32;
          for (let n = 0; n < 3; n++)
            line(
              x + 3 + n * 8,
              y + 13 + Math.sin(t * 2 + n) * 2,
              x + 9 + n * 8,
              y + 13 + Math.sin(t * 2 + n) * 2,
              flooded ? "#6ba5b8" : "#456d77",
            );
        }
    } else if (s.region === "terrace") {
      const direction = s.hazard.phase === "WEST WIND" ? -1 : 1;
      for (let i = 0; i < 18; i++) {
        const x = (((i * 57 + t * direction * 18) % 512) + 512) % 512,
          y = 55 + ((i * 17) % 175);
        line(x, y, x + 4, y - 2, C.jade);
      }
      for (const node of s.nodes || []) {
        const x = B.x + (node.col + 0.5) * 32,
          y = B.y + (node.lane + 0.5) * 32;
        ctx.globalAlpha = 0.15 + 0.05 * Math.sin(t * 3);
        rect(x - 12, y - 11, 24, 22, node.corrupted ? C.red : C.jade);
        ctx.globalAlpha = 1;
      }
    } else if (s.hazard.phase === "GRAVE MIST") {
      for (const lane of stages[s.stage]?.mist_lanes || []) {
        ctx.globalAlpha = 0.12;
        rect(B.x, B.y + lane * 32, 384, 32, "#7d96a5");
        ctx.globalAlpha = 1;
        for (let i = 0; i < 7; i++) {
          const x = B.x + ((i * 73 + t * 7) % 380);
          line(
            x,
            B.y + lane * 32 + 25,
            x + 28,
            B.y + lane * 32 + 25,
            "#728590",
          );
        }
      }
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
      const g = guardianAtlas[s.region];
      window.VanDaoBattleArt.artifact(
        ctx,
        images.guardians,
        g,
        x,
        y,
        41,
        s.region,
        s.time,
        ward.status === "sweeping",
      );
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
    text(Math.floor(s.qi || 0) + "/" + (s.qi_cap || 320), 22, 8, C.gold);
    icon("gate", 80, 8, C.jade);
    text(s.gate ?? 3, 94, 8);
    text("Wave " + (s.wave || 0) + "/" + (s.wave_count || 0), 126, 8);
    text(formatTime(s.time), 197, 8, C.muted);
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
    button("battle-settings", "Menu", 430, 4, 39, 19, () => {
      command({ action: "pause", paused: true });
      overlay = "battleMenu";
    });
    button("help", "?", 473, 4, 29, 19, () => {
      command({ action: "pause", paused: true });
      tutorialPage = 0;
      tutorialReturn = "battleMenu";
      overlay = "map-intro";
    });
    text(
      { setup: "SETUP", pressure: "PRESSURE", onslaught: "ONSLAUGHT" }[
        s.encounter?.id
      ] || "SETUP",
      289,
      8,
      C.gold,
      0.8,
      "right",
    );
    button(
      "auto-ultimate",
      s.auto_ultimate ? "A:ON" : "A:OFF",
      378,
      4,
      48,
      19,
      () => toggleAutoUltimate(),
      { active: s.auto_ultimate },
    );
    if (pointer.x >= 378 && pointer.x <= 426 && pointer.y < 27) {
      panel(145, 58, 358, 29, C.jade);
      text(
        "AUTO ULT: ultimate range, useful heals/buffs.",
        152,
        62,
        C.jade,
        0.85,
      );
      text(
        "Uses normal mana, Qi, Dao and cooldowns. Key A.",
        152,
        74,
        C.muted,
        0.8,
      );
    }
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
    if (s.final_assault?.incoming <= 15 && !s.final_assault?.active) {
      text(
        "ALL 5 LANES: " + Math.ceil(s.final_assault.incoming) + "s",
        252,
        32,
        C.red,
        0.8,
        "center",
      );
    } else if (s.final_assault?.active) {
      text(
        "FINAL ASSAULT / " + s.music.crowd + " alive",
        252,
        32,
        C.red,
        0.8,
        "center",
      );
    }
    button(
      "range-mode",
      "Range: " + rangeMode,
      366,
      44,
      137,
      14,
      () =>
        (rangeMode = ["basic", "skill", "ultimate"][
          (["basic", "skill", "ultimate"].indexOf(rangeMode) + 1) % 3
        ]),
    );
    const ritualLabel = { wharf: "Calm", terrace: "Purify", tomb: "Mirror" }[
      s.region
    ];
    button(
      "ritual",
      ritualLabel +
        " " +
        (s.ritual_cd > 0 ? Math.ceil(s.ritual_cd) + "s" : "35Q"),
      4,
      267,
      78,
      19,
      () => command({ action: "ritual" }),
      { disabled: s.paused || s.ritual_cd > 0 || s.qi < 35 },
    );
    if (pointer.x < 85 && pointer.y > 265) {
      panel(90, 245, 414, 40, C.gold);
      wrapped(
        stages[s.stage].ritual.description + " Cooldown 30s.",
        97,
        251,
        400,
        C.cream,
        12,
        2,
      );
    }
    for (let i = 0; i < realm(); i++)
      button(
        "relic-" + i,
        ["1", "2", "3"][i],
        5 + i * 27,
        245,
        24,
        18,
        () => command({ action: "relic", slot: i }),
        { disabled: s.relics_used?.includes(catalog.relics[i]?.id) },
      );
    const boss = s.enemies?.find((e) => e.boss);
    if (boss) {
      panel(96, 47, 264, 13, C.violet);
      rect(99, 50, 258 * clamp(boss.hp / boss.max_hp, 0, 1), 6, "#a65874");
      text(
        (enemies[boss.type]?.name || "Boss") + " / Phase " + boss.phase,
        228,
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
    const h = u.stats || previews[u.type] || heroes[u.type],
      ult = h.ultimate;
    panel(135, 164, 369, 75, C.gold);
    text(h.name + ` / HP ${Math.ceil(u.hp)}/${u.max_hp}`, 142, 169, C.gold);
    text(
      `Mana ${Math.floor(u.mana)}/${u.mana_max} (+${Number(u.mana_regen ?? h.mana_regen).toFixed(1)}/s) / Dao ${Math.floor(u.resonance)}/100`,
      142,
      183,
      C.ice,
    );
    text(
      `Ult: ${ult.mana_cost} MP / ${ult.qi_cost} Qi / 100 Dao / CD ${u.ultimate_cd > 0 ? Math.ceil(u.ultimate_cd) + "s" : "ready"}`,
      142,
      199,
      C.muted,
      0.85,
    );
    const ready =
      u.resonance >= 100 &&
      u.mana >= ult.mana_cost &&
      state.qi >= ult.qi_cost &&
      u.ultimate_cd <= 0 &&
      !state.paused;
    button(
      "ultimate",
      `Q ULT ${ult.mana_cost}MP`,
      142,
      215,
      100,
      19,
      () => command({ action: "ultimate", unit: u.id }),
      { disabled: !ready },
    );
    button(
      "auto-skill",
      u.auto_skill ? "AUTO ON" : "AUTO OFF",
      246,
      215,
      78,
      19,
      () =>
        command({ action: "auto_skill", unit: u.id, enabled: !u.auto_skill }),
    );
    button("unit-skills", "SKILLS", 328, 215, 78, 19, () => showSkills(u.type));
    button(
      "recall",
      "RECALL",
      410,
      215,
      87,
      19,
      () => {
        command({ action: "sell", unit: u.id });
        inspectUnit = null;
      },
      { disabled: state.paused },
    );
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
    ctx.fillRect(-(W - 384) / 2, -(H - 216) / 2, W, H);
    if (overlay === "map-intro") {
      const region = state?.region || "wharf",
        pages = window.VanDaoBattleArt.briefings[region],
        page = pages[tutorialPage];
      panel(-55, -23, 494, 266, regionColor[region]);
      text(regionNames[region], -42, -10, regionColor[region], 1.1);
      text(
        "FIELD BRIEFING  " + (tutorialPage + 1) + " / 3",
        424,
        -7,
        C.gold,
        0.85,
        "right",
      );
      text(
        stages[state?.stage]?.name || "Study the terrain",
        -42,
        12,
        C.muted,
        0.9,
      );
      window.VanDaoBattleArt.diagram(
        ctx,
        state,
        region,
        tutorialPage,
        -43,
        40,
        249,
        153,
        images,
        guardianAtlas,
        text,
      );
      text(page[0], 217, 39, C.gold, 0.95);
      wrapped(page[1], 217, 62, 207, C.cream, 13, 11);
      button(
        "intro-prev",
        "PREV",
        -42,
        211,
        72,
        22,
        () => (tutorialPage = Math.max(0, tutorialPage - 1)),
        { disabled: tutorialPage === 0 },
      );
      button(
        "intro-next",
        "NEXT",
        36,
        211,
        72,
        22,
        () => (tutorialPage = Math.min(2, tutorialPage + 1)),
        { disabled: tutorialPage === 2 },
      );
      text("You can reopen this guide during battle.", 116, 217, C.muted, 0.7);
      button(
        "intro-start",
        tutorialReturn ? "BACK" : "ENTER BATTLE",
        307,
        211,
        116,
        22,
        () => {
          if (tutorialReturn) overlay = tutorialReturn;
          else {
            overlay = null;
            pointer = { x: -1, y: -1 };
            command({ action: "pause", paused: false });
          }
        },
      );
      return;
    }
    if (overlay === "ranks") {
      panel(-45, -17, 474, 252, C.gold);
      text("MONSTER RANKS & ESCALATION", -31, -3, C.gold, 1.2);
      const notes = [
        "Swarm troops: 80% HP and 85% attack damage; elite/captain troops retain their stronger rank stats. Base HP rises 5% multiplicatively after every campaign encounter. The archive lists unscaled base stats; live enemy health bars use the scaled value.",
        "ELITE: 25% more HP, +2 armor, 10% more attack damage. Elite Lantern Demons grant 35 shield instead of 25 in the same radius-1.5 circle.",
        "CAPTAIN: 50% more HP, +3 armor, 15% more attack damage. Other enemies within radius 1.5 gain 10% movement speed. Appears in the final wave of non-boss encounters.",
        "Setup waves use ordinary enemies. Pressure adds one elite per pack; Onslaught makes about half each pack elite. Bosses keep their mandatory HP phases and visible warning lanes.",
      ];
      let y = 24;
      for (const note of notes)
        y += wrapped(note, -31, y, 440, C.cream, 12, 4) * 12 + 12;
      button(
        "ranks-close",
        "BACK",
        142,
        209,
        100,
        20,
        () => (overlay = scene === "archive" ? null : "skills"),
      );
      return;
    }
    if (overlay === "skills") {
      // This library uses the full logical viewport, rather than the legacy small modals.
      const list = libraryEnemy ? catalog.enemies : catalog.heroes;
      panel(-55, -23, 494, 266, C.gold);
      text(
        libraryEnemy ? "MONSTER FIELD MANUAL" : "CULTIVATOR FIELD MANUAL",
        -43,
        -11,
        C.gold,
        1.15,
      );
      button("library-heroes", "HEROES", 198, -14, 73, 21, () => {
        libraryEnemy = false;
        libraryHero = "sword";
      });
      button("library-enemies", "ENEMIES", 275, -14, 77, 21, () => {
        libraryEnemy = true;
        libraryHero = "tide";
      });
      button(
        "library-close",
        "BACK",
        357,
        -14,
        71,
        21,
        () => (overlay = scene === "battle" ? "battleMenu" : null),
      );
      const current = libraryEnemy
        ? enemies[libraryHero]
        : state?.heroes?.find((u) => u.type === libraryHero)?.stats ||
          previews[libraryHero] ||
          heroes[libraryHero];
      list.forEach((h, i) =>
        button(
          "library-" + h.id,
          libraryEnemy ? h.name : shortNames[h.id],
          -46,
          17 + i * (libraryEnemy ? 17 : 26),
          107,
          libraryEnemy ? 16 : 24,
          () => (libraryHero = h.id),
          { active: libraryHero === h.id },
        ),
      );
      if (!current) return;
      if (libraryEnemy)
        button(
          "library-ranks",
          "RANKS",
          128,
          -14,
          64,
          21,
          () => (overlay = "ranks"),
        );
      text(current.name, 73, 18, C.gold, 1.2);
      text(
        libraryEnemy
          ? `${current.hp} HP / ${current.armor} ARM / ${current.damage} ATK`
          : `${current.mana_max} max mana / +${current.mana_regen.toFixed(2)}/s / ${current.cost} Qi deployment`,
        73,
        39,
        C.ice,
        0.95,
      );
      if (libraryEnemy) {
        const a = current.abilities[0];
        text(
          `Base / basic reach ${current.range} left / attack ${current.interval}s`,
          73,
          55,
          C.muted,
          0.9,
        );
        text(a.name, 73, 72, C.gold);
        wrapped(a.description, 73, 91, 348, C.cream, 12, 4);
        text(
          a.cooldown
            ? `Ability cycle ${current.boss ? "10 / 9 / 8" : a.cooldown}s / windup ${a.windup}s`
            : "Passive ability",
          73,
          145,
          C.ice,
          0.9,
        );
        wrapped(a.geometry.description, 73, 160, 348, C.jade, 13, 3);
        wrapped(
          "Counter: " + current.counterplay,
          73,
          202,
          348,
          C.muted,
          12,
          3,
        );
      } else {
        for (const [i, tab] of ["basic", "skill", "ultimate"].entries())
          button(
            "library-tab-" + tab,
            tab,
            73 + i * 117,
            60,
            112,
            22,
            () => {
              libraryTab = tab;
              rangeMode = tab;
            },
            { active: libraryTab === tab },
          );
        skillDetails(current, libraryTab, 73, 84, 346);
      }
      return;
    }
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
      wrapped(
        s.mechanic + " / HP x" + s.hp_multiplier.toFixed(2),
        70,
        124,
        242,
        C.muted,
        10,
        2,
      );
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
      panel(69, 10, 246, 198, C.gold);
      text("SOUND & DISPLAY", 192, 23, C.gold, 1, "center");
      for (const [i, key] of ["master", "music", "sfx", "voice"].entries()) {
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
        158,
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
        158,
        107,
        18,
        () => {
          profile.settings.integer = !profile.settings.integer;
          saveProfile();
          resize();
        },
      );
      button("close", "BACK", 128, 185, 128, 18, () => (overlay = null));
      return;
    }
    if (overlay === "battleMenu") {
      panel(84, 22, 216, 207, C.gold);
      text("SPIRIT REST", 192, 32, C.gold, 1.2, "center");
      button("resume", "RESUME", 95, 52, 194, 22, () => {
        overlay = null;
        command({ action: "pause", paused: false });
      });
      button(
        "battle-skills",
        "CULTIVATOR / ENEMY SKILLS",
        95,
        78,
        194,
        22,
        () =>
          showSkills(
            inspectUnit
              ? state.heroes.find((u) => u.id === inspectUnit)?.type
              : "sword",
          ),
      );
      button("region-guide", "REGION MECHANICS", 95, 104, 194, 22, () => {
        tutorialPage = 0;
        tutorialReturn = "battleMenu";
        overlay = "map-intro";
      });
      button(
        "settings",
        "SOUND / VOICES",
        95,
        130,
        194,
        22,
        () => (overlay = "settings"),
      );
      button(
        "controls",
        "HOW TO PLAY",
        95,
        156,
        194,
        22,
        () => (overlay = "controls"),
      );
      button("leave", "LEAVE BATTLE", 95, 182, 194, 22, () => leaveBattle());
      return;
    }
    if (overlay === "region-guide") {
      const region = state?.region || "wharf",
        stage = stages[state?.stage];
      panel(-45, -17, 474, 252, regionColor[region]);
      text(regionNames[region], -31, -3, regionColor[region], 1.25);
      const sections = {
        wharf: [
          "Tide: 48s cycle. Low 0-20s, rising 20-28s, high 28-40s, receding 40-48s.",
          "Water cells: columns 3-4 in the marked lanes. Rising/high tide reduces attack speed 15%; high tide seals placement and deals 15 Water damage every 6s.",
          "Tide Miao move 15% faster at high tide. Fire and lightning can hit submerged corpses.",
          "Calm the River: 35 Qi, 30s cooldown. Suppresses floods for 12s.",
          "Jade River Ark: one rescue per lane; purges normal enemies, deals 35% boss max HP subject to phase gates and slows it.",
        ],
        terrace: [
          "Healthy ley node: heroes on it or one orthogonal cell away gain 12% attack speed and 20% mana regeneration.",
          "A Drainer within radius 1 corrupts a node after 2s. Corrupted nodes heal nearby enemies 3% max HP every 8s, radius 2.",
          "After the Drainer leaves, stand beside the node for 3s to purify it. Wind changes every 20s and affects projectile travel.",
          "Purify the Ley: 35 Qi, 30s cooldown. Purifies all nodes, locks wind 10s, restores 15 mana beside nodes.",
          "Heaven Sword Array: one rescue per lane; purges normal enemies, damages bosses and shields allies it passes.",
        ],
        tomb: [
          "Grave mist lasts the last 6s of each 24s cycle. In mist lanes, mana regeneration falls 30%; blades cannot target beyond 2.8 cells without reveal.",
          "Fire/lightning pierce ghost fades. Three curse stacks reduce attack speed 20% for 8s; cleansing counters this.",
          "Final encounter: three targetable altars resurrect dead souls after 6s at 35% HP and enable boss shields. Destroy the altars first.",
          "Soul Mirror: 35 Qi, 30s cooldown. Reveals ghosts, stops resurrection 6s and cleanses allied curses.",
          "Soul-Sealing Bell: one rescue per lane; purges souls and reveals the field during its sweep and for 6s afterward.",
        ],
      }[region];
      let y = 22;
      for (let i = 0; i < sections.length; i++) {
        text(String(i + 1) + ".", -31, y, C.gold);
        y += wrapped(sections[i], -13, y, 420, C.cream, 11, 4) * 11 + 6;
      }
      button(
        "region-close",
        "BACK",
        142,
        209,
        100,
        20,
        () => (overlay = "battleMenu"),
      );
      return;
    }
    if (overlay === "controls") {
      panel(47, 26, 290, 165, C.gold);
      text("KEEPER'S FIELD GUIDE", 192, 39, C.gold, 1, "center");
      const guide = [
        "1. CHOOSE A HERO. TAP AN EMPTY TILE.",
        "2. QI CAP 320; THREE YUN: 100/80/60% YIELD.",
        "3. SWORDS SHOOT RIGHT. MONKS BLOCK.",
        "4. Q ULT: 100 DAO + HERO MANA + SHARED QI.",
        "5. SPACE PAUSES. ESC CANCELS SELECTION.",
        "6. EACH LANE HAS ONE GUARDIAN SEAL RESCUE.",
        "7. COLUMN 0 IS RESERVED. DEPLOY IN 1-9.",
        "UPKEEP: 1 QI / 6 HEROES, ROUNDED UP / 24S.",
        "MENU > SKILLS: COSTS, RANGES, SCALING.",
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
      y = overlay ? 0 : scene === "battle" ? 45 : 4;
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
    if (!overlay && voiceCaption && now < voiceCaption.until) {
      const captionY = inspectUnit !== null ? 60 : 221;
      panel(126, captionY, 378, 17, C.edge, "#10232bef");
      text(voiceCaption.text, 132, captionY + 3, C.cream, 0.82);
    }
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
    abilityBursts = [];
    audio.stopVoices();
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
    audio.stopVoices();
    abilityBursts = [];
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
        paused: true,
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
      tutorialPage = 0;
      tutorialReturn = null;
      overlay = "map-intro";
      if (profile.settings.autoUltimate)
        await command({ action: "auto_ultimate", enabled: true });
      if (!profile.completed.length && id === "wharf-1" && !overlay)
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
  async function toggleAutoUltimate() {
    if (!state) return;
    const enabled = !state.auto_ultimate;
    const out = await command({ action: "auto_ultimate", enabled });
    if (state?.auto_ultimate === enabled) {
      profile.settings.autoUltimate = enabled;
      saveProfile();
      notify(
        "Auto ultimate " +
          (enabled ? "ON: targets in range; useful buffs and heals." : "OFF."),
        enabled ? C.jade : C.muted,
        3,
      );
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
    // A command response and polling can arrive out of order. Never rewind casts,
    // preferences or the simulation clock with a stale HTTP snapshot.
    if (
      state &&
      state.stage === s.stage &&
      state.seed === s.seed &&
      (s.tick < state.tick ||
        (s.tick === state.tick && (s.revision || 0) < (state.revision || 0)))
    )
      return;
    abilityBursts = abilityBursts.filter(
      (b) => s.time >= b.start && s.time - b.start < b.duration,
    );
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
      if (
        e.actor &&
        ["hero_skill", "ultimate"].includes(kind) &&
        s.time - e.time < 0.5
      ) {
        const ult = kind === "ultimate",
          friendly = s.heroes.find(
            (u) =>
              u.type === e.actor &&
              u.lane === e.lane &&
              Math.abs(u.x - e.x) < 0.1,
          );
        const targets = s.enemies
          .filter((u) => u.lane === e.lane)
          .sort((a, b) => a.x - b.x)
          .slice(0, 5)
          .map((u) => ({ id: u.id, x: u.x, lane: u.lane }));
        const radius =
          e.actor === "formation"
            ? ult
              ? 2
              : 2.5
            : e.actor === "frost"
              ? 2
              : 3;
        let allies = s.heroes.filter(
          (u) =>
            ((ult && e.actor === "herbalist") ||
              Math.hypot(u.x - e.x, u.lane - e.lane) <= radius) &&
            !(e.actor === "formation" && !ult && u.id === friendly?.id),
        );
        allies.sort(
          e.actor === "formation" && !ult
            ? (a, b) =>
                b.resonance - a.resonance || a.hp / a.max_hp - b.hp / b.max_hp
            : (a, b) => a.hp / a.max_hp - b.hp / b.max_hp,
        );
        if (!ult)
          allies = allies.slice(
            0,
            e.actor === "formation"
              ? 3
              : e.actor === "frost"
                ? friendly?.stats?.shield_targets || 1
                : 1,
          );
        allies = allies.map((u) => ({ id: u.id, x: u.x, lane: u.lane }));
        abilityBursts.push({
          hero: e.actor,
          kind: ult ? "ultimate" : "skill",
          start: e.time,
          duration: ult
            ? ["gatherer", "formation"].includes(e.actor)
              ? 6
              : 2.1
            : 1.1,
          x: e.x,
          lane: e.lane,
          targets,
          allies,
        });
        if (abilityBursts.length > 70) abilityBursts.shift();
      }
      if (e.actor) {
        audio.hero(e.actor, kind);
        if (
          (kind === "place" || kind === "ultimate") &&
          s.time - (e.time || 0) < 1
        )
          audio.voice(e.actor, kind === "place" ? "summon" : "ultimate");
      }
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
        } else {
          profile.stones += Number(s.rewards?.replay_stones || 0);
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
    voiceEpoch: 0,
    voiceGain: null,
    voiceManifest: null,
    musicManifest: null,
    buffers: {},
    loadingMusic: "",
    currentMusic: null,
    musicPhase: "setup",
    musicEpoch: 0,
    voiceQueue: [],
    voiceBusy: false,
    voiceSource: null,
    playedVoices: {},
    playedThemes: {},
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
        this.voiceGain = this.context.createGain();
        this.voiceGain.connect(this.master);
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
      this.master.gain.setTargetAtTime(
        profile.settings.master * 0.4 * (document.hidden ? 0 : 1),
        t,
        0.08,
      );
      this.musicGain.gain.setTargetAtTime(
        profile.settings.music *
          (this.voiceBusy ? 0.45 : 1) *
          (this.musicPhase === "onslaught" ? 1.12 : 1) *
          (scene === "battle" && state?.paused ? 0 : 1),
        t,
        0.18,
      );
      this.voiceGain.gain.setTargetAtTime(
        profile.settings.voice ?? 0.8,
        t,
        0.08,
      );
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
    pluck(frequency, duration, volume, delay = 0) {
      for (let n = 1; n <= 7; n++)
        this.tone(
          frequency * n * (1 + 0.0001 * n * n),
          duration / (1 + n * 0.3),
          "sine",
          volume / n ** 1.6,
          "sfx",
          delay,
        );
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
        [587.33, 659.25, 880, 1174.66].forEach((n, i) =>
          this.pluck(n, 0.6, 0.19, i * 0.15),
        );
        return;
      }
      if (kind === "defeat") {
        [440, 349.23, 293.66].forEach((n, i) =>
          this.pluck(n, 0.8, 0.17, i * 0.24),
        );
        return;
      }
      if (sounds[kind]) this.tone(...sounds[kind]);
    },
    async buffer(url) {
      if (this.buffers[url]) return this.buffers[url];
      const promise = fetch(url)
        .then((r) => {
          if (!r.ok) throw Error("Missing audio asset");
          return r.arrayBuffer();
        })
        .then((b) => this.context.decodeAudioData(b));
      this.buffers[url] = promise;
      try {
        return await promise;
      } catch (e) {
        delete this.buffers[url];
        throw e;
      }
    },
    stopVoices() {
      this.voiceEpoch++;
      this.voiceQueue = [];
      voiceCaption = null;
      if (this.voiceSource) {
        try {
          this.voiceSource.stop();
        } catch {}
      }
    },
    voice(hero, action) {
      if (!this.context || !this.voiceManifest) return;
      const line = this.voiceManifest.characters[hero]?.[action];
      if (!line) return;
      const item = {
        hero,
        action,
        line,
        epoch: this.voiceEpoch,
        expires: performance.now() + (action === "ultimate" ? 4000 : 6000),
      };
      this.voiceQueue = this.voiceQueue.filter(
        (q) =>
          q.expires > performance.now() &&
          !(q.hero === hero && q.action === action),
      );
      if (action === "ultimate") this.voiceQueue.unshift(item);
      else if (this.voiceQueue.length < 3) this.voiceQueue.push(item);
      this.voiceQueue = this.voiceQueue.slice(0, 5);
      this.pumpVoice();
    },
    async pumpVoice() {
      this.voiceQueue = this.voiceQueue.filter(
        (q) => q.expires > performance.now(),
      );
      if (this.voiceBusy || !this.voiceQueue.length) return;
      this.voiceBusy = true;
      this.update();
      const item = this.voiceQueue.shift();
      voiceCaption = {
        text: (heroes[item.hero]?.name || item.hero) + ": " + item.line.text,
        until: performance.now() + (item.line.duration + 1) * 1000,
      };
      try {
        const buffer = await this.buffer(
          "/assets/audio/voices/" + item.line.file,
        );
        if (
          item.epoch === this.voiceEpoch &&
          (profile.settings.voice ?? 0.8) > 0
        ) {
          await new Promise((resolve) => {
            const source = this.context.createBufferSource();
            source.buffer = buffer;
            source.connect(this.voiceGain);
            this.voiceSource = source;
            source.onended = resolve;
            source.start();
            this.playedVoices[item.hero + "_" + item.action] =
              (this.playedVoices[item.hero + "_" + item.action] || 0) + 1;
          });
        }
      } catch (e) {
        notify("Voice unavailable; dialogue remains in subtitles.", C.muted, 2);
      } finally {
        this.voiceBusy = false;
        this.voiceSource = null;
        this.update();
        this.pumpVoice();
      }
    },
    music() {
      if (!this.context || !this.musicManifest) return;
      this.update();
      const battle = scene === "battle" && isPlaying(state),
        region = battle
          ? state.music?.theme || state.stage.replaceAll("-", "_")
          : "lobby",
        phase = battle ? state.music?.intensity || "setup" : "setup";
      this.theme = region;
      this.musicPhase = phase;
      const key = region + "_" + phase;
      if (
        document.hidden ||
        (state?.paused && battle) ||
        this.loadingMusic === key ||
        this.currentMusic?.key === key
      )
        return;
      const epoch = ++this.musicEpoch;
      this.loadingMusic = key;
      const track = this.musicManifest.tracks[key];
      if (!track) {
        this.loadingMusic = "";
        return;
      }
      const probe = document.createElement("audio"),
        file = probe.canPlayType('audio/ogg; codecs="vorbis"')
          ? track.ogg
          : track.mp3;
      this.buffer("/assets/audio/music/" + file)
        .then((buffer) => {
          if (epoch !== this.musicEpoch) return;
          const t = this.context.currentTime,
            source = this.context.createBufferSource(),
            gain = this.context.createGain();
          source.buffer = buffer;
          source.loop = true;
          source.loopEnd = Math.min(track.duration, buffer.duration);
          source.connect(gain);
          gain.connect(this.musicGain);
          gain.gain.setValueAtTime(0.001, t);
          gain.gain.linearRampToValueAtTime(0.9, t + 1.1);
          source.start();
          if (this.currentMusic) {
            this.currentMusic.gain.gain.cancelScheduledValues(t);
            this.currentMusic.gain.gain.setTargetAtTime(0.001, t, 0.3);
            this.currentMusic.source.stop(t + 1.3);
          }
          this.currentMusic = { key, source, gain };
          this.loadingMusic = "";
          this.playedThemes[key] = true;
          const musicKeys = Object.keys(this.buffers).filter((k) =>
            k.includes("/music/"),
          );
          while (musicKeys.length > 3) delete this.buffers[musicKeys.shift()];
        })
        .catch(() => {
          if (epoch === this.musicEpoch) this.loadingMusic = "";
        });
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
    if (scene !== "battle" || !state || !isPlaying(state)) return;
    const tile = tileAt(pointer);
    if (selectedHero && tile && !state.paused) {
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
    if (e.code === "KeyA") toggleAutoUltimate();
    else if (e.code === "Space")
      command({ action: "pause", paused: !state.paused });
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
      if (catalog.version !== "1.3.0")
        throw Error("Stop the old Python server and run the updated run.py.");
      for (const key of ["heroes", "enemies", "stages", "relics"])
        if (!Array.isArray(catalog[key]))
          catalog[key] = Object.values(catalog[key] || {});
      heroes = Object.fromEntries(catalog.heroes.map((h) => [h.id, h]));
      enemies = Object.fromEntries(catalog.enemies.map((h) => [h.id, h]));
      stages = Object.fromEntries(catalog.stages.map((s) => [s.id, s]));
      const names = [
        "title",
        "wharf",
        "terrace",
        "tomb",
        "sprites",
        "cultivators",
        "guardians",
      ];
      const assets = await Promise.all(
        names.map((name) => loadImage("/assets/" + name + ".png")),
      );
      names.forEach((n, i) => (images[n] = assets[i]));
      try {
        const r = await fetch("/assets/sprites.json");
        atlas = await r.json();
        if (atlas.sprites) atlas = atlas.sprites;
      } catch {}
      cultivators = await (await fetch("/assets/cultivators.json")).json();
      guardianAtlas = await (await fetch("/assets/guardians.json")).json();
      sceneArt = await (await fetch("/assets/scenes.json")).json();
      audio.voiceManifest = await (
        await fetch("/assets/audio/voices/voices.json")
      ).json();
      audio.musicManifest = await (
        await fetch("/assets/audio/music/music.json")
      ).json();
      await refreshPreviews();
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
      return buttons.map(({ id, x, y, w, h, disabled, talentState }) => ({
        id,
        x,
        y,
        w,
        h,
        disabled,
        talentState,
      }));
    },
    get previews() {
      return JSON.parse(JSON.stringify(previews));
    },
    get rangeMode() {
      return rangeMode;
    },
    get library() {
      return {
        hero: libraryHero,
        tab: libraryTab,
        enemy: libraryEnemy,
        open: overlay === "skills",
      };
    },
    get voiceEvents() {
      return { ...audio.playedVoices };
    },
    get musicTracks() {
      return { ...audio.playedThemes };
    },
    get castingEffects() {
      return abilityBursts.map((b) => ({ ...b }));
    },
    get briefingPage() {
      return overlay === "map-intro" ? tutorialPage : null;
    },
    get musicPhase() {
      return audio.musicPhase;
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
