/* Sanctuary world controller. HUD stays in screen space; only scenery follows the camera. */
window.VanDaoSanctuary = (() => {
  const clamp = (n, a, b) => Math.max(a, Math.min(b, n));
  class Sanctuary {
    constructor(map, assets, atlas, hooks) {
      Object.assign(this, { map, assets, atlas, hooks });
      this.nav = new VanDaoHubNavigation.Navigation(map);
      this.keys = new Set();
      this.position = { ...map.spawn };
      this.direction = "south";
      this.route = [];
      this.target = null;
      this.dialog = null;
      this.session = null;
      this.clock = 0;
      this.step = 0;
      this.last = 0;
      this.saved = 0;
      this.moving = false;
      this.camera = { x: map.spawn.x, y: map.spawn.y - 20, zoom: 1.85 };
      this.travel = 0;
      this.lastDirection = "south";
      this.wasActive = false;
      this.exploration = hooks.exploration;
      this.explorationArt = hooks.explorationArt;
      this.effects = [];
      this.pace = 0;
      this.action = null;
      this.ui = hooks.hudRoot
        ? new VanDaoSanctuaryHUD(this, hooks.hudRoot)
        : null;
      this.decoded = {};
      this.frameMetrics = [];
      this.prepareImages();
    }
    async prepareImages() {
      if (typeof createImageBitmap === "undefined") return;
      for (const name of ["sword", "gatherer", "herbalist", "direction_idle"]) {
        const image = this.assets["hub_" + name];
        if (!image) continue;
        try {
          this.decoded[name] = await createImageBitmap(image, {
            resizeWidth: Math.min(1536, image.naturalWidth),
            resizeQuality: "high",
          });
        } catch {}
      }
    }
    reset() {
      this.session = null;
      this.stop();
      this.dialog = null;
      this.ui?.invalidate();
    }
    stop() {
      this.keys.clear();
      this.route = [];
      this.target = null;
      this.moving = false;
      this.pace = 0;
      this.action = null;
      this.coast = null;
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
        this.camera.x = this.position.x;
        this.camera.y = this.position.y - 20;
      }
      this.profile = profile;
      this.avatar = data.avatar || "sword";
    }
    interactionTargets() {
      if (
        this._targetFacilities === this.map.facilities &&
        this._targetExploration === this.exploration &&
        this._targets
      )
        return this._targets;
      this._targetFacilities = this.map.facilities;
      this._targetExploration = this.exploration;
      this._targets = [
        ...this.map.facilities,
        ...(this.exploration?.npcs || []).map((n) => ({
          ...n,
          id: "person-" + n.id,
          npc: n.id,
          keeper: n.name,
          name: n.name,
          kind: "visitor",
        })),
        ...(this.exploration?.observations || []).map((o) => ({
          ...o,
          id: "detail-" + o.id,
          observation: o.id,
          keeper: "",
          kind: "prop",
        })),
      ];
      return this._targets;
    }
    nearest() {
      let best = null;
      for (const f of this.interactionTargets()) {
        const d = Math.hypot(f.x - this.position.x, f.y - this.position.y);
        if (!best || d < best.d) best = { f, d };
      }
      return best;
    }
    npcs() {
      return this.interactionTargets()
        .filter((f) => f.kind !== "prop")
        .map((f, i) => ({
          ...f,
          direction: "south",
          moving: false,
          phase: this.clock * 0.4 + i,
        }));
    }
    go(id) {
      const f = this.interactionTargets().find((f) => f.id === id);
      if (!f) return;
      this.keys.clear();
      this.dialog = null;
      this.coast = null;
      if (Math.hypot(f.x - this.position.x, f.y - this.position.y) < 19)
        return this.talk(f);
      this.route = this.nav.route(this.position, f);
      this.target = this.route.length ? id : null;
      if (!this.route.length)
        this.hooks.notice("Choose a reachable path on the sanctuary map.");
    }
    point(screen) {
      if (this.dialog) return;
      const p = this.screenToWorld(screen),
        f = this.interactionTargets().find(
          (f) =>
            Math.hypot(f.x - p.x, f.y - p.y) < (f.kind === "prop" ? 8 : 12),
        );
      if (f) return this.go(f.id);
      this.keys.clear();
      this.coast = null;
      this.route = this.nav.route(this.position, p);
      this.target = null;
    }
    talk(f) {
      this.stop();
      this.persist();
      if (f.kind === "visitor") {
        this.playAction("greet", 0.85);
        this.hooks.converse?.(f.npc);
        return;
      }
      if (f.kind === "prop") {
        this.playAction("inspect", 1.1);
        this.effects.push({
          id: f.observation,
          x: f.x,
          y: f.y,
          at: this.clock,
          kind: f.kind,
        });
        this.hooks.sound?.(
          f.kind === "prop"
            ? this.exploration.observations.find((o) => o.id === f.observation)
                ?.kind || "leaf"
            : "leaf",
        );
        this.hooks.observe?.(
          this.exploration.observations.find((o) => o.id === f.observation),
        );
        return;
      }
      this.playAction("greet", 0.85);
      this.dialog = { kind: "npc", id: f.id };
      this.hooks.visit(f.id);
      this.hooks.chime();
    }
    openMap() {
      this.stop();
      this.persist();
      this.dialog = { kind: "map" };
    }
    openAvatar() {
      this.stop();
      this.persist();
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
      if (code === "Tab" && this.dialog) return false;
      if (code === "Tab" || code === "KeyM") {
        this.dialog ? (this.dialog = null) : this.openMap();
        return true;
      }
      if (code === "KeyE" || code === "Enter") {
        if (this.dialog?.kind === "npc")
          this.activate(
            this.map.facilities.find((f) => f.id === this.dialog.id),
          );
        else if (!this.dialog) {
          const near = this.nearest();
          if (near.d < 21) this.talk(near.f);
        }
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
      if (!f) return;
      if (f.id === "missions") {
        this.dialog = { kind: "commissions" };
        return true;
      }
      this.stop();
      this.persist();
      this.dialog = null;
      this.hooks.open(f.action);
    }
    persist() {
      this.hooks.position({ ...this.position });
      this.saved = this.clock;
    }
    playAction(kind, duration = 1) {
      this.stop();
      this.action = { kind, at: this.clock, duration };
      this.direction = "southwest";
    }
    setZoom(value) {
      this.zoomTarget = clamp(value, 1.45, 2.4);
    }
    screenToWorld(p) {
      return {
        x: (p.x - 256) / this.camera.zoom + this.camera.x,
        y: (p.y - 144) / this.camera.zoom + this.camera.y,
      };
    }
    worldToScreen(p) {
      return {
        x: (p.x - this.camera.x) * this.camera.zoom + 256,
        y: (p.y - this.camera.y) * this.camera.zoom + 144,
      };
    }
    update(t, active) {
      const dt =
        this.last && this.wasActive
          ? clamp((t - this.last) / 1000, 0, 0.08)
          : 0;
      this.last = t;
      this.wasActive = active;
      if (!active) {
        this.keys.clear();
        return;
      }
      this.clock += dt;
      const before = { ...this.position },
        wasMoving = this.moving;
      if (this.action && this.clock - this.action.at >= this.action.duration)
        this.action = null;
      if (!this.dialog && !this.externalModal && !this.action) {
        let dx =
          Number(this.keys.has("KeyD") || this.keys.has("ArrowRight")) -
          Number(this.keys.has("KeyA") || this.keys.has("ArrowLeft"));
        let dy =
          Number(this.keys.has("KeyS") || this.keys.has("ArrowDown")) -
          Number(this.keys.has("KeyW") || this.keys.has("ArrowUp"));
        const desiredSpeed =
          (dx || dy || this.route.length ? 42 : 0) *
          (this.keys.has("ShiftLeft") || this.keys.has("ShiftRight") ? 1.5 : 1);
        this.pace += (desiredSpeed - this.pace) * (1 - Math.exp(-dt * 14));
        const speed = this.pace;
        if (dx || dy) {
          const length = Math.hypot(dx, dy);
          this.coast = { x: dx / length, y: dy / length };
          this.position = this.nav.move(
            this.position,
            (dx / length) * speed * dt,
            (dy / length) * speed * dt,
          );
        } else if (!this.route.length && this.coast && this.pace > 1) {
          this.position = this.nav.move(
            this.position,
            this.coast.x * speed * dt,
            this.coast.y * speed * dt,
          );
        } else {
          if (this.route.length) this.coast = null;
          // Consume the whole frame's distance across waypoints: no one-frame stop at grid nodes.
          let budget = speed * dt,
            guard = 0;
          while (this.route.length && budget > 0.0001 && guard++ < 40) {
            const to = this.route[0],
              len = Math.hypot(to.x - this.position.x, to.y - this.position.y);
            if (len < 0.001) {
              this.position = { ...to };
              this.route.shift();
              continue;
            }
            const amount = Math.min(len, budget),
              next = this.nav.move(
                this.position,
                ((to.x - this.position.x) / len) * amount,
                ((to.y - this.position.y) / len) * amount,
              );
            const moved = Math.hypot(
              next.x - this.position.x,
              next.y - this.position.y,
            );
            this.position = next;
            budget -= amount;
            if (moved < amount * 0.2) break;
            if (amount >= len - 0.001) {
              this.position = { ...to };
              this.route.shift();
            }
          }
        }
      }
      const dx = this.position.x - before.x,
        dy = this.position.y - before.y,
        distance = Math.hypot(dx, dy);
      this.moving = distance > 0.0001;
      if (this.moving) {
        this.travel += distance;
        this.step = this.travel / 24;
        const angle = Math.atan2(dy, dx),
          directions = [
            "east",
            "southeast",
            "south",
            "southwest",
            "west",
            "northwest",
            "north",
            "northeast",
          ];
        this.direction =
          directions[(Math.round(angle / (Math.PI / 4)) + 8) % 8];
        const oldStep = Math.floor((this.travel - distance) / 12),
          newStep = Math.floor(this.travel / 12);
        if (newStep !== oldStep) {
          this.hooks.sound?.("foot");
          this.effects.push({
            kind: "foot",
            x: this.position.x,
            y: this.position.y,
            at: this.clock,
          });
        }
      }
      if (
        (wasMoving && !this.moving) ||
        (this.moving && this.clock - this.saved > 6)
      )
        this.persist();
      if (this.target) {
        const f = this.interactionTargets().find((f) => f.id === this.target);
        if (Math.hypot(f.x - this.position.x, f.y - this.position.y) < 18)
          this.talk(f);
      }
      const z = this.zoomTarget || 1.85,
        smooth = 1 - Math.exp(-dt * 8);
      this.camera.zoom += (z - this.camera.zoom) * smooth;
      const halfW = 256 / this.camera.zoom,
        halfH = 144 / this.camera.zoom;
      const desired = {
        x: clamp(this.position.x, halfW, 512 - halfW),
        y: clamp(this.position.y - 15, halfH, 288 - halfH),
      };
      this.camera.x += (desired.x - this.camera.x) * smooth;
      this.camera.y += (desired.y - this.camera.y) * smooth;
      this.camera.x = clamp(this.camera.x, halfW, 512 - halfW);
      this.camera.y = clamp(this.camera.y, halfH, 288 - halfH);
    }
    cutout(c, image, item, x, y, height) {
      if (!image || !item) return;
      const w = (height * item.w) / item.h;
      c.drawImage(
        image,
        item.x,
        item.y,
        item.w,
        item.h,
        x - w / 2,
        y - height,
        w,
        height,
      );
    }
    character(c, id, x, y, height, direction, moving, phase, player = false) {
      const walk = this.atlas.avatars?.[id],
        action = player && this.action && this.explorationArt?.actions?.[id];
      const meta = action
        ? this.explorationArt.actions[id]
        : !moving && walk?.idle
          ? walk.idle
          : walk;
      const key = meta?.source || (!moving && walk?.idle ? "idle_" + id : id);
      const image = action
        ? this.assets.explore_actions
        : this.decoded[key] || this.assets["hub_" + key];
      c.fillStyle = "#10252135";
      c.beginPath();
      c.ellipse(x, y + 0.6, height * 0.19, 1.5, 0, 0, Math.PI * 2);
      c.fill();
      if (!meta || !image) {
        const f = this.explorationArt?.npcs?.[id] || this.atlas.npcs[id];
        this.cutout(
          c,
          this.explorationArt?.npcs?.[id]
            ? this.assets.explore_npcs
            : this.assets.hub_npcs,
          f,
          x,
          y,
          height,
        );
        return -1;
      }
      const facing = meta.states[direction]
        ? direction
        : direction.includes("north")
          ? "north"
          : direction.includes("south")
            ? "south"
            : direction;
      const seq = action
        ? meta.states[this.action.kind] || meta.states.inspect
        : meta.states[facing] || meta.states.south;
      const progress = action
          ? Math.max(
              0,
              Math.min(
                0.999,
                (this.clock - this.action.at) / this.action.duration,
              ),
            )
          : 0,
        index = action
          ? Math.floor(progress * seq.length)
          : moving
            ? Math.floor(phase * seq.length) % seq.length
            : 0,
        f = seq[index];
      const source = f.source ? this.assets["hub_" + f.source] : image,
        scale =
          height / (f.body_height || meta.body_height || meta.cell_h * 0.86),
        ratio = source.width / (f.source_width || meta.width),
        ax = f.anchor_x ?? f.w / 2,
        ay = f.anchor_y ?? f.h;
      c.save();
      c.translate(x, y);
      if (player && !action && moving)
        c.rotate(
          Math.sin(phase * Math.PI * 2) * 0.008 + (this.pace > 48 ? 0.012 : 0),
        );
      if (!moving && !action && this.profile?.settings.hubMotion !== false)
        c.scale(1, 1 + Math.sin(this.clock * 1.7) * 0.003);
      c.drawImage(
        source,
        f.x * ratio,
        f.y * ratio,
        f.w * ratio,
        f.h * ratio,
        -ax * scale,
        -ay * scale,
        f.w * scale,
        f.h * scale,
      );
      c.restore();
      if (this.renderedFrames)
        this.renderedFrames[id + ":" + direction] = index;
      return moving || action ? index : -1;
    }
    drawProp(c, o, t, ambient) {
      if (["stone", "letter"].includes(o.kind) || o.id === "lotus") return;
      if (o.kind === "lantern") {
        this.cutout(
          c,
          this.assets.hub_decor,
          this.atlas.decor.lantern,
          o.x,
          o.y,
          10,
        );
        return;
      }
      if (o.kind === "crane") {
        c.save();
        c.translate(o.x, o.y - 5);
        c.rotate(ambient ? Math.sin(t * 0.7) * 0.08 : 0);
        c.fillStyle = "#ffefd2";
        c.beginPath();
        c.moveTo(-5, 0);
        c.lineTo(0, -2);
        c.lineTo(5, 0);
        c.lineTo(0, 2);
        c.closePath();
        c.fill();
        c.strokeStyle = "#c4ad83";
        c.lineWidth = 0.3;
        c.beginPath();
        c.moveTo(-5, 0);
        c.lineTo(0, 1);
        c.lineTo(5, 0);
        c.stroke();
        c.restore();
        return;
      }

      const f = this.explorationArt?.props?.[o.prop];
      if (!f) return;
      const distance = Math.hypot(o.x - this.position.x, o.y - this.position.y),
        react = Math.max(0, 1 - distance / 22);
      const recent = this.effects.find((f) => f.id === o.id && t - f.at < 1.8);
      const sway = ambient
        ? Math.sin(t * 1.5 + o.x) * 0.012 +
          Math.sin(t * 7) * react * 0.12 +
          (recent ? Math.sin((t - recent.at) * 9) * 0.09 : 0)
        : 0;
      const h =
          o.kind === "grass"
            ? 10
            : o.kind === "flower"
              ? 13
              : o.kind === "water"
                ? 10
                : 12,
        w = (h * f.w) / f.h;
      c.save();
      c.translate(o.x, o.y);
      c.rotate(sway);
      c.drawImage(
        this.assets.explore_props,
        f.x,
        f.y,
        f.w,
        f.h,
        -w / 2,
        -h,
        w,
        h,
      );
      c.restore();
    }
    draw(c, view) {
      const started = performance.now();
      this.sync(view.profile);
      this.update(view.now, view.active);
      this.renderedFrames = {};
      this.pointer = view.pointer;
      const camera = this.camera,
        t = this.clock,
        ambient = view.profile.settings.hubMotion !== false;
      c.save();
      c.imageSmoothingEnabled = true;
      c.imageSmoothingQuality = "high";
      // Source crop rather than a full-image rescale: preserve detail in the close camera.
      const image = this.assets.hub_scene,
        sx = ((camera.x - 256 / camera.zoom) * image.naturalWidth) / 512,
        sy = ((camera.y - 144 / camera.zoom) * image.naturalHeight) / 288;
      c.drawImage(
        image,
        sx,
        sy,
        image.naturalWidth / camera.zoom,
        image.naturalHeight / camera.zoom,
        0,
        0,
        512,
        288,
      );
      c.translate(256, 144);
      c.scale(camera.zoom, camera.zoom);
      c.translate(-camera.x, -camera.y);
      if (ambient) {
        c.strokeStyle = "#dcfff344";
        c.lineWidth = 0.35;
        for (let i = 0; i < 3; i++) {
          c.beginPath();
          c.ellipse(
            256,
            150,
            14 + ((t * 2 + i * 7) % 18),
            4 + ((t * 0.5 + i * 2) % 5),
            0,
            0,
            Math.PI * 2,
          );
          c.stroke();
        }
        for (let i = 0; i < 16; i++) {
          const x = (i * 47 + t * (1 + (i % 3))) % 512,
            y = 66 + ((i * 27 + t * 0.8) % 186);
          c.fillStyle = i % 3 ? "#ffd9e6aa" : "#fff1bbaa";
          c.beginPath();
          c.ellipse(x, y, 0.7, 0.4, Math.sin(t + i), 0, Math.PI * 2);
          c.fill();
        }
      }
      const owned = view.profile.estate?.cosmetics?.active || [];
      if (owned.includes("lantern_canopy"))
        for (let i = 0; i < 7; i++)
          this.cutout(
            c,
            this.assets.hub_decor,
            this.atlas.decor.lantern,
            190 + i * 22,
            65 + Math.sin(i * 0.5) * 4,
            12,
          );
      if (owned.includes("jade_chimes"))
        this.cutout(
          c,
          this.assets.hub_decor,
          this.atlas.decor.chimes,
          149,
          193,
          16,
        );
      if (owned.includes("ward_banner"))
        this.cutout(
          c,
          this.assets.hub_decor,
          this.atlas.decor.banner,
          130,
          113,
          25,
        );
      if (this.route.length) {
        const end = this.route.at(-1);
        c.strokeStyle = "#fff0bba0";
        c.lineWidth = 0.5;
        c.beginPath();
        c.ellipse(end.x, end.y, 3.5, 1.2, 0, 0, Math.PI * 2);
        c.stroke();
      }
      const actors = [
        ...this.npcs().map((n) => ({ ...n, player: false })),
        ...(this.exploration?.observations || []).map((o) => ({
          ...o,
          propActor: true,
        })),
        { id: "player", npc: this.avatar, ...this.position, player: true },
      ].sort((a, b) => a.y - b.y);
      for (const a of actors) {
        if (a.propActor) {
          this.drawProp(c, a, t, ambient);
          continue;
        }
        if (a.player) {
          c.strokeStyle = "#fff4b780";
          c.lineWidth = 0.35;
          c.beginPath();
          c.ellipse(a.x, a.y, 5.5, 1.7, 0, 0, Math.PI * 2);
          c.stroke();
        }
        const frame = this.character(
          c,
          a.npc,
          a.x,
          a.y,
          a.player
            ? this.avatar === "gatherer"
              ? 19
              : 22
            : a.npc === "gatherer"
              ? 16
              : 18,
          a.player ? this.direction : a.direction,
          a.player ? this.moving : a.moving,
          a.player ? this.step : a.phase,
          a.player,
        );
        if (a.player) this.playerFrame = frame;
      }
      this.effects = this.effects.filter((f) => t - f.at < 1.8);
      if (ambient)
        for (const fx of this.effects) {
          const age = t - fx.at;
          c.globalAlpha = Math.max(
            0,
            1 - age / (fx.kind === "foot" ? 0.5 : 1.8),
          );
          if (fx.kind === "foot") {
            c.strokeStyle = "#d5bd8a70";
            c.lineWidth = 0.4;
            c.beginPath();
            c.ellipse(fx.x, fx.y, 1 + age * 4, 0.5 + age, 0, 0, Math.PI * 2);
            c.stroke();
          } else {
            for (let i = 0; i < 8; i++) {
              c.fillStyle =
                fx.id === "lotus" || fx.id === "spring" ? "#b7f4f5" : "#f8c9d6";
              c.beginPath();
              c.ellipse(
                fx.x + Math.cos(i * 2.1 + age) * age * 11,
                fx.y - age * 8 + Math.sin(i * 2.1) * age * 4,
                0.6,
                0.35,
                age,
                0,
                Math.PI * 2,
              );
              c.fill();
            }
          }
        }
      c.globalAlpha = 1;
      c.restore();
      this.ui?.draw({ ...view, active: view.active && !view.hideHUD });
      if (view.active) this.frameMetrics.push(performance.now() - started);
      if (this.frameMetrics.length > 180) this.frameMetrics.shift();
    }
    setVisible(visible) {
      this.ui?.setVisible(visible);
      if (!visible) this.wasActive = false;
    }
    get snapshot() {
      const near = this.nearest();
      return {
        position: { ...this.position },
        avatar: this.avatar,
        direction: this.direction,
        moving: this.moving,
        route: this.route.map((p) => ({ ...p })),
        target: this.target,
        dialog: this.dialog ? { ...this.dialog } : null,
        nearest: { id: near.f.id, distance: near.d },
        npcs: this.npcs().map((n) => ({ id: n.id, x: n.x, y: n.y })),
        camera: { ...this.camera },
        renderedFrames: { ...this.renderedFrames },
        playerFrame: this.playerFrame,
        action: this.action ? { ...this.action } : null,
        facings: Object.keys(this.atlas.avatars?.[this.avatar]?.states || {}),
        walkFrames: this.atlas.avatars?.[this.avatar]?.states.south.length || 0,
        renderMs: this.frameMetrics.length
          ? this.frameMetrics.reduce((a, b) => a + b, 0) /
            this.frameMetrics.length
          : 0,
        style: "HD-2D",
      };
    }
  }
  return Sanctuary;
})();
