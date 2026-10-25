/* HD sanctuary: navigable scenery, NPC conversations and existing-system links. */
window.VanDaoSanctuary = (() => {
  const gold = "#ead39a",
    cream = "#f7efdc",
    jade = "#a5e5ce",
    muted = "#b4c2bd";
  function round(c, x, y, w, h, r = 5) {
    c.beginPath();
    c.moveTo(x + r, y);
    c.arcTo(x + w, y, x + w, y + h, r);
    c.arcTo(x + w, y + h, x, y + h, r);
    c.arcTo(x, y + h, x, y, r);
    c.arcTo(x, y, x + w, y, r);
    c.closePath();
  }
  class Sanctuary {
    constructor(map, assets, atlas, hooks) {
      this.map = map;
      this.assets = assets;
      this.atlas = atlas;
      this.hooks = hooks;
      this.nav = new VanDaoHubNavigation.Navigation(map);
      this.keys = new Set();
      this.dialog = null;
      this.route = [];
      this.target = null;
      this.position = { ...map.spawn };
      this.direction = "south";
      this.session = null;
      this.last = 0;
      this.clock = 0;
      this.step = 0;
      this.saved = 0;
      this.helpUntil = 14000;
      this.moving = false;
    }
    reset() {
      this.session = null;
      this.stop();
      this.dialog = null;
    }
    stop() {
      this.keys.clear();
      this.route = [];
      this.target = null;
      this.moving = false;
    }
    sync(profile) {
      const data = profile.estate?.hub || {};
      if (this.session !== profile.save_id) {
        this.session = profile.save_id;
        this.position = VanDaoHubNavigation.walkable(this.map, data.x, data.y)
          ? { x: data.x, y: data.y }
          : { ...this.map.spawn };
        this.stop();
        this.dialog = null;
        this.saved = 0;
        this.last = 0;
      }
      this.profile = profile;
      this.avatar = data.avatar || "sword";
    }
    npcs() {
      return this.map.facilities.map((f, i) => {
        const wander =
          this.profile?.settings.hubMotion !== false &&
          ["sword", "gatherer", "herbalist"].includes(f.npc)
            ? Math.sin(this.clock * 0.45 + i) * 3
            : 0;
        return {
          ...f,
          x: f.x + wander,
          y: f.y + Math.sin(this.clock * 0.4 + i) * Math.abs(wander) * 0.25,
          direction: wander > 0 ? "east" : "west",
          moving: Math.abs(wander) > 1,
        };
      });
    }
    nearest() {
      return this.map.facilities
        .map((f) => ({
          f,
          d: Math.hypot(f.x - this.position.x, f.y - this.position.y),
        }))
        .sort((a, b) => a.d - b.d)[0];
    }
    go(id) {
      const f = this.map.facilities.find((f) => f.id === id);
      if (!f) return;
      this.keys.clear();
      this.dialog = null;
      if (Math.hypot(f.x - this.position.x, f.y - this.position.y) < 19)
        return this.talk(f);
      this.route = this.nav.route(this.position, f);
      this.target = this.route.length ? id : null;
      if (!this.route.length)
        this.hooks.notice(
          "That path is not reachable. Use the sanctuary menu.",
        );
    }
    point(p) {
      if (this.dialog) return;
      const f = this.map.facilities.find(
        (f) => Math.hypot(f.x - p.x, f.y - p.y) < 17,
      );
      if (f) return this.go(f.id);
      this.keys.clear();
      this.route = this.nav.route(this.position, p);
      this.target = null;
    }
    talk(f) {
      this.stop();
      this.dialog = { kind: "npc", id: f.id };
      this.hooks.visit(f.id);
      this.hooks.chime();
    }
    openMap() {
      this.stop();
      this.dialog = { kind: "map" };
    }
    openAvatar() {
      this.stop();
      this.dialog = { kind: "avatar" };
    }
    key(code, down) {
      if (!down) {
        this.keys.delete(code);
        return;
      }
      if (code === "Escape") {
        if (this.dialog) this.dialog = null;
        else if (this.route.length) this.stop();
        else this.openMap();
        return true;
      }
      if (code === "Tab" || code === "KeyM") {
        this.dialog ? (this.dialog = null) : this.openMap();
        return true;
      }
      if (code === "KeyE" || code === "Enter") {
        if (this.dialog?.kind === "npc") {
          const f = this.map.facilities.find((f) => f.id === this.dialog.id);
          return this.activate(f);
        }
        const near = this.nearest();
        if (near?.d < 21) this.talk(near.f);
        return true;
      }
      if (this.dialog) return false;
      if (
        [
          "KeyW",
          "KeyA",
          "KeyS",
          "KeyD",
          "ArrowUp",
          "ArrowDown",
          "ArrowLeft",
          "ArrowRight",
          "ShiftLeft",
          "ShiftRight",
        ].includes(code)
      ) {
        this.keys.add(code);
        this.route = [];
        this.target = null;
        return true;
      }
      return false;
    }
    activate(f) {
      if (f.id === "missions") {
        this.dialog = { kind: "commissions" };
        return true;
      }
      this.dialog = null;
      this.stop();
      this.persist();
      this.hooks.open(f.action);
    }
    persist() {
      this.hooks.position({ ...this.position });
      this.saved = this.clock;
    }
    update(t, active) {
      const dt = this.last
        ? Math.min(0.05, Math.max(0, (t - this.last) / 1000))
        : 0;
      this.last = t;
      if (!active) {
        this.keys.clear();
        return;
      }
      this.clock += dt;
      let dx = 0,
        dy = 0;
      const wasMoving = this.moving;
      if (!this.dialog) {
        dx =
          Number(this.keys.has("KeyD") || this.keys.has("ArrowRight")) -
          Number(this.keys.has("KeyA") || this.keys.has("ArrowLeft"));
        dy =
          Number(this.keys.has("KeyS") || this.keys.has("ArrowDown")) -
          Number(this.keys.has("KeyW") || this.keys.has("ArrowUp"));
        let speed =
          this.map.speed *
          (this.keys.has("ShiftLeft") || this.keys.has("ShiftRight")
            ? 1.45
            : 1);
        if (dx || dy) {
          const len = Math.hypot(dx, dy);
          dx = (dx / len) * speed * dt;
          dy = (dy / len) * speed * dt;
        } else if (this.route.length) {
          const point = this.route[0],
            length = Math.hypot(
              point.x - this.position.x,
              point.y - this.position.y,
            ),
            distance = Math.min(length, speed * dt);
          if (length < 0.02) {
            this.position = { ...point };
            this.route.shift();
          } else {
            dx = ((point.x - this.position.x) / length) * distance;
            dy = ((point.y - this.position.y) / length) * distance;
          }
        }
      }
      const next = this.nav.move(this.position, dx, dy);
      this.moving =
        Math.hypot(next.x - this.position.x, next.y - this.position.y) > 0.02;
      if (this.moving) {
        this.step += dt;
        this.direction =
          Math.abs(dx) > Math.abs(dy)
            ? dx > 0
              ? "east"
              : "west"
            : dy > 0
              ? "south"
              : "north";
        this.position = next;
      } else this.step = 0;
      if (
        (wasMoving && !this.moving) ||
        (this.moving && this.clock - this.saved > 1.2)
      )
        this.persist();
      if (this.target) {
        const f = this.map.facilities.find((f) => f.id === this.target);
        if (
          f &&
          Math.hypot(f.x - this.position.x, f.y - this.position.y) < 18
        ) {
          this.talk(f);
          this.persist();
        }
      }
    }
    text(
      c,
      label,
      x,
      y,
      size = 9,
      color = cream,
      align = "left",
      serif = false,
    ) {
      c.font =
        (serif ? "500 " : "500 ") +
        size +
        "px " +
        (serif ? "Georgia, serif" : "system-ui, sans-serif");
      c.textAlign = align;
      c.textBaseline = "top";
      c.fillStyle = color;
      c.fillText(String(label), x, y);
    }
    wrap(c, label, x, y, width, size = 9, color = cream, max = 4) {
      c.font = "500 " + size + "px system-ui, sans-serif";
      const words = String(label).split(/\s+/);
      let line = "",
        row = 0;
      for (const word of words) {
        if (c.measureText(line + " " + word).width > width && line) {
          this.text(c, line, x, y + row * (size + 4), size, color);
          line = word;
          row++;
          if (row >= max) return;
        } else line += (line ? " " : "") + word;
      }
      if (line && row < max)
        this.text(c, line, x, y + row * (size + 4), size, color);
    }
    panel(c, x, y, w, h, alpha = 0.91) {
      round(c, x, y, w, h, 7);
      c.fillStyle = `rgba(12,29,35,${alpha})`;
      c.fill();
      c.strokeStyle = "#c6b88270";
      c.lineWidth = 0.6;
      c.stroke();
    }
    button(c, id, label, x, y, w, h, fn, opt = {}) {
      const over =
        this.pointer &&
        this.pointer.x > x &&
        this.pointer.x < x + w &&
        this.pointer.y > y &&
        this.pointer.y < y + h;
      round(c, x, y, w, h, opt.radius || 4);
      c.fillStyle = opt.disabled
        ? "#243333c7"
        : opt.active
          ? "#576249e8"
          : over
            ? "#466157ee"
            : "#162f35e8";
      c.fill();
      c.strokeStyle = opt.active ? gold : over ? jade : "#bfb08365";
      c.lineWidth = 0.6;
      c.stroke();
      this.text(
        c,
        label,
        x + w / 2,
        y + (h - (opt.size || 8)) / 2 - 1,
        opt.size || 8,
        opt.disabled ? "#80918d" : opt.active ? gold : cream,
        "center",
      );
      this.hooks.register({
        id,
        label,
        x,
        y,
        w,
        h,
        fn,
        disabled: !!opt.disabled,
      });
    }
    cutout(c, image, item, x, y, height, alpha = 1) {
      if (!image || !item) return;
      const width = (height * item.w) / item.h;
      c.save();
      c.globalAlpha = alpha;
      c.drawImage(
        image,
        item.x,
        item.y,
        item.w,
        item.h,
        x - width / 2,
        y - height,
        width,
        height,
      );
      c.restore();
    }
    character(c, id, x, y, height, direction, moving, step) {
      const meta = this.atlas.avatars?.[id],
        image = this.assets["hub_" + id];
      c.save();
      c.fillStyle = "#12272545";
      c.beginPath();
      c.ellipse(x, y + 1, height * 0.22, 2.1, 0, 0, Math.PI * 2);
      c.fill();
      c.restore();
      if (meta && image) {
        const sequence = meta.states[direction] || meta.states.south,
          frame = sequence[moving ? 1 + (Math.floor(step * 8) % 3) : 0],
          factor = height / (meta.cell_h * 0.9);
        c.drawImage(
          image,
          frame.x,
          frame.y,
          frame.w,
          frame.h,
          x + (frame.dx - meta.cell_w / 2) * factor,
          y + (frame.dy - meta.cell_h * 0.95) * factor,
          frame.w * factor,
          frame.h * factor,
        );
      } else
        this.cutout(
          c,
          this.assets.hub_npcs,
          this.atlas.npcs?.[id],
          x,
          y,
          height,
        );
    }
    draw(c, view) {
      this.sync(view.profile);
      this.pointer = view.pointer;
      this.update(view.now, view.active);
      const t = this.clock,
        p = view.profile,
        e = p.estate,
        ambient = p.settings.hubMotion !== false;
      c.save();
      c.imageSmoothingEnabled = true;
      c.imageSmoothingQuality = "high";
      c.drawImage(this.assets.hub_scene, 0, 0, 512, 288);
      // Light pools and water reflections stay in scenery, below feet and labels.
      if (ambient) {
        for (const f of this.map.facilities) {
          const light = c.createRadialGradient(
            f.x,
            f.y - 5,
            0,
            f.x,
            f.y - 5,
            23,
          );
          light.addColorStop(0, "#ffd59d18");
          light.addColorStop(1, "#ffd59d00");
          c.fillStyle = light;
          c.fillRect(f.x - 24, f.y - 29, 48, 48);
        }
        c.save();
        c.strokeStyle = "#d0fff234";
        c.lineWidth = 0.6;
        for (let i = 0; i < 3; i++) {
          c.beginPath();
          c.ellipse(
            256,
            150,
            13 + ((t * 4 + i * 9) % 22),
            4 + ((t * 1.4 + i * 3) % 8),
            0,
            0,
            Math.PI * 2,
          );
          c.stroke();
        }
        c.restore();
        for (let i = 0; i < 18; i++) {
          const x = (i * 47 + t * (3 + (i % 3))) % 512,
            y = 55 + ((i * 29 + t * (2 + (i % 2))) % 194);
          c.save();
          c.translate(x, y);
          c.rotate(Math.sin(t * 0.6 + i));
          c.fillStyle = i % 3 ? "#ffd7df9b" : "#ffedb6a0";
          c.beginPath();
          c.ellipse(0, 0, 1.2, 0.6, 0, 0, Math.PI * 2);
          c.fill();
          c.restore();
        }
      }
      const active = e?.cosmetics?.active || [];
      if (active.includes("lantern_canopy")) {
        c.strokeStyle = "#a78551b0";
        c.lineWidth = 0.7;
        c.beginPath();
        c.moveTo(184, 58);
        c.quadraticCurveTo(256, 73, 328, 58);
        c.stroke();
        for (let i = 0; i < 7; i++)
          this.cutout(
            c,
            this.assets.hub_decor,
            this.atlas.decor?.lantern,
            190 + i * 22,
            65 + Math.sin(i * 0.5) * 4 + (ambient ? Math.sin(t + i) * 0.4 : 0),
            12,
          );
      }
      if (active.includes("jade_chimes"))
        this.cutout(
          c,
          this.assets.hub_decor,
          this.atlas.decor?.chimes,
          149,
          193 + (ambient ? Math.sin(t) * 0.5 : 0),
          16,
        );
      if (active.includes("ward_banner"))
        this.cutout(
          c,
          this.assets.hub_decor,
          this.atlas.decor?.banner,
          130,
          113,
          25,
        );
      if (this.route.length) {
        c.fillStyle = "#f3e5a47f";
        for (const point of this.route
          .filter((_, i) => i % 3 === 0)
          .slice(0, 9)) {
          c.beginPath();
          c.arc(point.x, point.y, 0.65, 0, Math.PI * 2);
          c.fill();
        }
      }
      const npcs = this.npcs(),
        actors = [
          ...npcs.map((n) => ({ ...n, player: false })),
          { id: "player", npc: this.avatar, ...this.position, player: true },
        ].sort((a, b) => a.y - b.y);
      for (const a of actors) {
        if (a.player) {
          c.save();
          c.strokeStyle = "#fff3bf9c";
          c.lineWidth = 0.65;
          c.beginPath();
          c.ellipse(a.x, a.y + 1, 7, 2.5, 0, 0, Math.PI * 2);
          c.stroke();
          c.restore();
          this.character(
            c,
            this.avatar,
            a.x,
            a.y,
            this.avatar === "gatherer" ? 20 : 23,
            this.direction,
            this.moving,
            this.step,
          );
        } else
          this.character(
            c,
            a.npc,
            a.x,
            a.y,
            a.npc === "gatherer" ? 17 : 20,
            a.direction,
            a.moving && ambient,
            t,
          );
      }
      const nearest = this.nearest();
      for (const f of this.map.facilities) {
        const near = nearest.f.id === f.id && nearest.d < 23,
          hover = Math.hypot(this.pointer.x - f.x, this.pointer.y - f.y) < 28;
        const width = Math.max(54, f.name.length * 4.2 + 12),
          ready =
            (f.id === "missions" &&
              view.data?.contracts.some(
                (q) => !q.claimed && q.progress >= q.target,
              )) ||
            (f.id === "garden" &&
              view.data?.plots.some((q) => q.crop && q.growth >= q.need));
        c.save();
        this.panel(c, f.x - width / 2, f.y + 5, width, 12, near ? 0.96 : 0.7);
        this.text(
          c,
          f.name,
          f.x,
          f.y + 7,
          6.8,
          near || ready ? gold : "#f3efdc",
          "center",
        );
        if (ready) {
          c.fillStyle = gold;
          c.beginPath();
          c.arc(f.x + width / 2 - 2, f.y + 5, 3, 0, Math.PI * 2);
          c.fill();
        }
        if (near || hover) {
          this.text(
            c,
            near ? "E · Speak" : "Click to approach",
            f.x,
            f.y - 28,
            7.5,
            cream,
            "center",
          );
        }
        c.restore();
        this.hooks.register({
          id: "hub-go-" + f.id,
          x: f.x - width / 2,
          y: f.y - 21,
          w: width,
          h: 38,
          fn: () => this.go(f.id),
          disabled: !view.active,
        });
      }
      // Floating HUD leaves the architecture visible.
      this.panel(c, 12, 8, 488, 27, 0.85);
      this.text(c, "VAN DAO", 23, 14, 14, gold, "left", true);
      this.text(c, "CELESTIAL SANCTUARY", 111, 18, 6.8, "#d7e7dd");
      this.text(c, p.stones + " STONES", 329, 17, 7.5, gold, "right");
      this.text(c, p.insight + " INSIGHT", 402, 17, 7.5, jade, "right");
      this.button(
        c,
        "settings",
        "SET",
        465,
        12,
        29,
        19,
        () => this.hooks.open("settings"),
        { size: 7 },
      );
      this.button(c, "hub-map", "MAP", 420, 12, 38, 19, () => this.openMap(), {
        size: 7,
      });
      this.panel(c, 12, 258, 488, 24, 0.88);
      const quick = [
        ["begin", "Campaign", "campaign"],
        ["estate", "Estate", "Garden"],
        ["roster", "Talents", "roster"],
        ["archive", "Bestiary", "archive"],
        ["trials", "Trials", "trials"],
        ["missions", "Missions", "missions"],
        ["saves", "Saves", "saves"],
        ["avatar", "Avatar", "avatar"],
      ];
      quick.forEach(([id, label, action], i) =>
        this.button(
          c,
          id,
          label,
          16 + i * 60,
          261,
          56,
          18,
          () => {
            this.stop();
            this.persist();
            if (action === "avatar") this.openAvatar();
            else this.hooks.open(action);
          },
          { size: 7.1 },
        ),
      );
      if (nearest.d < 23 && !this.dialog)
        this.button(
          c,
          "hub-interact",
          "E · Speak to " + nearest.f.keeper,
          172,
          235,
          168,
          18,
          () => this.talk(nearest.f),
          { size: 7.5 },
        );
      else if (this.clock < 15 && !e?.hub?.help_seen) {
        this.panel(c, 157, 236, 198, 16, 0.72);
        this.text(
          c,
          "WASD / arrows / click to move · E to speak",
          256,
          240,
          6.7,
          cream,
          "center",
        );
      }
      const tracked = view.data?.contracts.find(
        (q) => q.id === e?.hub?.tracked && !q.claimed,
      );
      if (tracked) {
        this.panel(c, 14, 42, 147, 38, 0.82);
        this.text(c, "FOLLOWING: " + tracked.name, 22, 48, 7.4, gold);
        this.text(
          c,
          tracked.progress + " / " + tracked.target + " completed",
          22,
          61,
          7.5,
          cream,
        );
        this.button(
          c,
          "hub-unpin",
          "×",
          143,
          45,
          14,
          13,
          () => this.hooks.track(null),
          { size: 9 },
        );
      }
      if (view.resume)
        this.button(
          c,
          "resume",
          "RESUME BATTLE",
          348,
          236,
          148,
          18,
          () => this.hooks.open("resume"),
          { size: 7 },
        );
      if (this.dialog) this.drawDialog(c, view);
      c.restore();
    }
    drawDialog(c, view) {
      this.hooks.clearButtons();
      c.fillStyle = "#06151892";
      c.fillRect(0, 0, 512, 288);
      const d = this.dialog;
      if (d.kind === "map") {
        this.panel(c, 88, 34, 336, 220, 0.97);
        this.text(c, "Sanctuary Directory", 106, 49, 15, gold, "left", true);
        this.text(c, "Choose a destination to walk there.", 106, 73, 8, muted);
        this.map.facilities.forEach((f, i) =>
          this.button(
            c,
            "hub-directory-" + f.id,
            f.name,
            106 + (i % 2) * 152,
            95 + Math.floor(i / 2) * 31,
            145,
            25,
            () => this.go(f.id),
            { size: 8 },
          ),
        );
        this.button(
          c,
          "hub-close",
          "Close",
          184,
          225,
          144,
          20,
          () => (this.dialog = null),
        );
        return;
      }
      if (d.kind === "avatar") {
        this.panel(c, 96, 35, 320, 218, 0.97);
        this.text(
          c,
          "Your Sanctuary Presence",
          113,
          49,
          14,
          gold,
          "left",
          true,
        );
        this.text(
          c,
          "Appearance only · battle stats stay the same",
          113,
          72,
          8,
          muted,
        );
        this.map.avatars.forEach((a, i) => {
          const x = 112 + i * 96,
            open = a.realm <= view.realm;
          this.character(c, a.id, x + 42, 160, 49, "south", true, this.clock);
          this.text(c, a.name, x + 42, 171, 7.2, cream, "center");
          this.button(
            c,
            "hub-avatar-" + a.id,
            open
              ? this.avatar === a.id
                ? "Selected"
                : "Choose"
              : "Clear Wharf III",
            x,
            189,
            88,
            22,
            () => this.hooks.avatar(a.id),
            {
              disabled: !open || view.busy,
              active: this.avatar === a.id,
              size: 7,
            },
          );
        });
        this.button(
          c,
          "hub-ambient",
          view.profile.settings.hubMotion === false
            ? "Ambient motion: OFF"
            : "Ambient motion: ON",
          112,
          222,
          192,
          20,
          () => this.hooks.motion(),
        );
        this.button(
          c,
          "hub-close",
          "Close",
          311,
          222,
          88,
          20,
          () => (this.dialog = null),
        );
        return;
      }
      const f = this.map.facilities.find((f) => f.id === d.id);
      if (!f) return;
      this.panel(c, 65, 67, 382, 178, 0.97);
      this.text(c, f.keeper, 149, 83, 15, gold, "left", true);
      this.text(c, f.title, 150, 104, 8, jade);
      this.cutout(
        c,
        this.assets.hub_npcs,
        this.atlas.npcs[f.npc],
        105,
        192,
        82,
      );
      this.wrap(c, f.greeting, 149, 124, 277, 8.5, cream, 5);
      const status =
        f.id === "garden"
          ? (view.data?.plots.filter((p) => p.crop && p.growth >= p.need)
              .length || 0) + " plots ready to harvest"
          : f.id === "missions"
            ? (view.data?.contracts.filter(
                (q) => !q.claimed && q.progress >= q.target,
              ).length || 0) + " commissions ready to claim"
            : f.id === "archive"
              ? Object.keys(view.profile.estate?.monsters || {}).length +
                " enemy records in your archive"
              : "";
      if (status) this.text(c, status, 149, 193, 7.8, jade);
      this.button(
        c,
        "hub-open-" + f.id,
        f.offer,
        149,
        216,
        199,
        21,
        () => {
          if (f.id === "missions") {
            this.dialog = { kind: "commissions" };
            return;
          }
          this.activate(f);
        },
        { size: 8 },
      );
      this.button(
        c,
        "hub-close",
        "Leave",
        356,
        216,
        74,
        21,
        () => (this.dialog = null),
      );
      return;
    }
    drawCommissions(c, view) {
      this.hooks.clearButtons();
      c.fillStyle = "#06151892";
      c.fillRect(0, 0, 512, 288);
      this.panel(c, 79, 22, 354, 242, 0.97);
      this.text(c, "Commissions of the Sect", 96, 36, 15, gold, "left", true);
      this.text(
        c,
        "Progress counts automatically. Follow one to pin it.",
        96,
        59,
        7.5,
        muted,
      );
      (view.data?.contracts || []).forEach((q, i) => {
        const y = 80 + i * 50;
        this.text(c, q.name, 96, y, 9, gold);
        this.text(
          c,
          q.progress + " / " + q.target,
          280,
          y + 1,
          7.5,
          cream,
          "right",
        );
        this.wrap(c, q.description, 96, y + 13, 187, 7.2, cream, 2);
        this.text(
          c,
          window.VanDaoEstate.reward(q.reward),
          96,
          y + 36,
          6.8,
          jade,
        );
        const ready = q.progress >= q.target,
          tracked = view.profile.estate.hub?.tracked === q.id;
        this.button(
          c,
          "hub-contract-" + q.id,
          q.claimed
            ? "Claimed"
            : ready
              ? "Claim reward"
              : tracked
                ? "Following"
                : "Take commission",
          294,
          y,
          122,
          24,
          () => (ready ? this.hooks.claim(q.id) : this.hooks.track(q.id)),
          { disabled: q.claimed || view.busy, active: tracked, size: 7.3 },
        );
      });
      this.button(
        c,
        "hub-full-missions",
        "Open Mission Ledger",
        96,
        237,
        204,
        20,
        () => {
          this.dialog = null;
          this.hooks.open("Commissions");
        },
      );
      this.button(
        c,
        "hub-close",
        "Close",
        307,
        237,
        109,
        20,
        () => (this.dialog = null),
      );
    }
    get snapshot() {
      const nearest = this.nearest();
      return {
        position: { ...this.position },
        avatar: this.avatar,
        direction: this.direction,
        moving: this.moving,
        route: this.route.map((p) => ({ ...p })),
        target: this.target,
        dialog: this.dialog ? { ...this.dialog } : null,
        nearest: { id: nearest.f.id, distance: nearest.d },
        npcs: this.npcs().map((n) => ({ id: n.id, x: n.x, y: n.y })),
        style: "HD-2D",
      };
    }
  }
  // The commission page shares the same world/modal lifecycle.
  const draw = Sanctuary.prototype.drawDialog;
  Sanctuary.prototype.drawDialog = function (c, v) {
    if (this.dialog?.kind === "commissions") return this.drawCommissions(c, v);
    return draw.call(this, c, v);
  };
  return Sanctuary;
})();
