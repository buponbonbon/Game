/* A walkable 2D Spirit Fields workyard. Every inventory change stays in estate.act. */
window.VanDaoGarden = (() => {
  const esc = (v) => VanDaoSanctuaryHUD.escape(v),
    icon = (id) => VanDaoSanctuaryHUD.icon(id);
  class Garden {
    constructor(layout, images, hubAtlas, art, crops, hooks) {
      Object.assign(this, { layout, images, hubAtlas, art, crops, hooks });
      this.targets = layout.facilities.map((f) => ({ ...f }));
      this.selected = null;
      this.seed = "qi_grass";
      this.pending = null;
      this.working = false;
      this.effects = [];
      this.signature = "";
      this.handlers = new Map();
      this.visible = false;
      this.world = new VanDaoSanctuary(layout, images, hubAtlas, {
        position: () => {},
        chime: hooks.chime,
        sound: hooks.sound,
        notice: hooks.notice,
        visit: () => {},
      });
      this.world.map = {
        ...layout,
        facilities: [...this.targets, ...this.npcs()],
      };
      this.world.zoomTarget = 1.3;
      this.world.camera.zoom = 1.3;
      this.world.explorationArt = art;
      this.world.talk = (f) => {
        this.world.stop();
        if (f.plot !== undefined) {
          this.selected = f.plot;
          if (this.pending) this.perform();
        } else hooks.converse(f.npc);
      };
      this.root = document.createElement("div");
      this.root.className = "world-ui garden-ui";
      this.root.hidden = true;
      hooks.root.appendChild(this.root);
      this.root.addEventListener("click", (e) => {
        const b = e.target.closest("button[data-garden-id]");
        if (b && !b.disabled) {
          hooks.chime();
          this.handlers.get(b.dataset.gardenId)?.();
          this.signature = "";
          document.querySelector("#game").focus({ preventScroll: true });
        }
      });
      this.resizeObserver = new ResizeObserver(() => this.resize());
      this.resizeObserver.observe(document.querySelector("#game"));
      this.resize();
    }
    resize() {
      const r = document.querySelector("#game").getBoundingClientRect(),
        p = this.root.parentElement.getBoundingClientRect();
      Object.assign(this.root.style, {
        left: r.left - p.left + "px",
        top: r.top - p.top + "px",
        width: r.width + "px",
        height: r.height + "px",
      });
      this.root.style.setProperty(
        "--world-scale",
        Math.max(0.65, Math.min(1.4, r.width / 1280)),
      );
      this.box = r;
      this.dirty = true;
    }
    reset() {
      this.world.reset();
      this.selected = null;
      this.pending = null;
      this.signature = "";
    }
    setVisible(v) {
      if (this.visible === v) return;
      if (this.visible && !v) {
        this.world.stop();
        this.pending = null;
      }
      this.visible = v;
      this.root.hidden = !v;
      this.dirty = true;
    }
    prop(c, id, x, y, h, w) {
      const f = this.art.props[id];
      if (!f) return;
      const width = w || (h * f.w) / f.h;
      c.drawImage(
        this.images.explore_props,
        f.x,
        f.y,
        f.w,
        f.h,
        x - width / 2,
        y - h,
        width,
        h,
      );
    }
    point(screen) {
      if (this.working || this.hooks.modal()) return;
      const p = this.world.screenToWorld(screen),
        bed = this.layout.plots.find(
          (b) => Math.abs(b.x - p.x) < 30 && p.y > b.y - 25 && p.y < b.y + 14,
        );
      if (bed) {
        this.select(bed.index);
        return;
      }
      const npc = this.npcs().find(
        (n) => Math.hypot(n.x - p.x, n.y - p.y) < 14,
      );
      if (npc) {
        this.world.route = this.world.nav.route(this.world.position, npc);
        this.world.target = npc.id;
        return;
      }
      this.pending = null;
      this.world.keys.clear();
      this.world.route = this.world.nav.route(this.world.position, p);
      this.world.target = null;
    }
    npcs() {
      return [
        { id: "field-lin", npc: "lin", x: 89, y: 178 },
        { id: "field-mu", npc: "herbalist", x: 400, y: 136 },
        { id: "field-yun", npc: "gatherer", x: 399, y: 217 },
      ];
    }
    select(index) {
      if (this.working) return;
      this.selected = index;
      this.pending = null;
      this.signature = "";
      const b = this.layout.plots[index];
      this.world.route = this.world.nav.route(this.world.position, b.approach);
      this.world.target = b.id;
    }
    queue(action) {
      if (this.working || this.hooks.busy() || this.selected === null) return;
      const bed = this.layout.plots[this.selected];
      this.pending = { action, plot: bed.index, crop: this.seed };
      this.world.keys.clear();
      this.world.route = this.world.nav.route(
        this.world.position,
        bed.approach,
      );
      this.world.target = bed.id;
      if (
        Math.hypot(
          this.world.position.x - bed.approach.x,
          this.world.position.y - bed.approach.y,
        ) < 18
      ) {
        this.world.stop();
        this.perform();
      }
      this.signature = "";
    }
    async perform() {
      if (!this.pending || this.working) return;
      const task = this.pending;
      this.pending = null;
      this.working = true;
      this.signature = "";
      try {
        const out = await this.hooks.act(task.action, {
          plot: task.plot,
          crop: task.crop,
        });
        if (out?.ok) {
          const kind =
            task.action === "water"
              ? "water"
              : task.action === "plant" || task.action === "harvest"
                ? "gather"
                : "inspect";
          this.world.playAction(kind, 1.1);
          this.effects.push({
            kind: task.action,
            plot: task.plot,
            at: this.world.clock,
          });
          this.hooks.sound?.(task.action);
        }
      } finally {
        this.working = false;
        this.signature = "";
      }
    }
    key(code, down) {
      if (down && code === "Escape") {
        this.pending = null;
        this.selected = null;
        this.world.stop();
        this.signature = "";
        return true;
      }
      if (down && code === "KeyE") {
        const bed = [...this.layout.plots].sort(
          (a, b) =>
            Math.hypot(
              a.approach.x - this.world.position.x,
              a.approach.y - this.world.position.y,
            ) -
            Math.hypot(
              b.approach.x - this.world.position.x,
              b.approach.y - this.world.position.y,
            ),
        )[0];
        if (
          Math.hypot(
            bed.approach.x - this.world.position.x,
            bed.approach.y - this.world.position.y,
          ) < 22
        )
          this.select(bed.index);
        else {
          const n = this.npcs().find(
            (n) =>
              Math.hypot(
                n.x - this.world.position.x,
                n.y - this.world.position.y,
              ) < 22,
          );
          if (n) this.hooks.converse(n.npc);
        }
        return true;
      }
      if (down && /^Key[WASD]$|^Arrow/.test(code)) this.pending = null;
      return this.world.key(code, down);
    }
    draw(c, view) {
      this.view = view;
      const p = view.profile,
        profile = {
          ...p,
          save_id: p.save_id + ":fields",
          estate: {
            ...p.estate,
            hub: { ...p.estate.hub, ...this.layout.spawn },
          },
        };
      this.world.sync(profile);

      this.world.externalModal = this.hooks.modal();
      this.world.update(view.now, view.active);
      const w = this.world,
        t = w.clock,
        cam = w.camera,
        ambient = p.settings.hubMotion !== false;
      c.save();
      c.imageSmoothingEnabled = true;
      c.imageSmoothingQuality = "high";
      const image = this.images.garden;
      c.drawImage(
        image,
        ((cam.x - 256 / cam.zoom) * image.naturalWidth) / 512,
        ((cam.y - 144 / cam.zoom) * image.naturalHeight) / 288,
        image.naturalWidth / cam.zoom,
        image.naturalHeight / cam.zoom,
        0,
        0,
        512,
        288,
      );
      c.translate(256, 144);
      c.scale(cam.zoom, cam.zoom);
      c.translate(-cam.x, -cam.y);
      const actors = [
        ...this.layout.plots.map((b) => ({ ...b, kind: "bed" })),
        ...this.npcs().map((n) => ({ ...n, kind: "npc" })),
        { ...w.position, kind: "player" },
      ].sort((a, b) => a.y - b.y);
      for (const a of actors) {
        if (a.kind === "bed") {
          const plot = view.data.plots[a.index],
            locked = a.index >= p.estate.garden.size;
          this.prop(
            c,
            locked ? "overgrown" : plot.watered ? "wet_bed" : "bed",
            a.x,
            a.y + 11,
            26,
            57,
          );
          if (plot.crop && !locked) {
            const stage = plot.growth >= plot.need ? 3 : plot.growth ? 2 : 1,
              frame = this.crops[plot.crop][stage],
              height = stage === 3 ? 25 : stage === 2 ? 18 : 12;
            for (let i = 0; i < 3; i++) {
              const x = a.x + (i - 1) * 14,
                y = a.y + 2 + (i % 2 ? 2 : 0),
                sway = ambient ? Math.sin(t * 1.6 + a.index + i) * 0.022 : 0;
              c.save();
              c.translate(x, y);
              c.rotate(sway);
              c.drawImage(
                this.images.crops,
                frame.x,
                frame.y,
                frame.w,
                frame.h,
                (-height * frame.w) / frame.h / 2,
                -height,
                (height * frame.w) / frame.h,
                height,
              );
              c.restore();
            }
            if (plot.growth >= plot.need && ambient) {
              for (let i = 0; i < 3; i++) {
                c.fillStyle = "#fff0a5b0";
                c.beginPath();
                c.arc(
                  a.x + Math.sin(t * 0.8 + i * 2) * 19,
                  a.y - 12 - ((t * 3 + i * 7) % 16),
                  0.55,
                  0,
                  Math.PI * 2,
                );
                c.fill();
              }
            }
          }
          if (this.selected === a.index) {
            c.strokeStyle = "#f9e3a8b0";
            c.lineWidth = 0.7;
            c.beginPath();
            c.ellipse(a.x, a.y + 2, 30, 13, 0, 0, Math.PI * 2);
            c.stroke();
          }
        } else if (a.kind === "npc") {
          w.character(
            c,
            a.npc,
            a.x,
            a.y,
            a.npc === "gatherer" ? 17 : 20,
            "south",
            false,
            0,
            false,
          );
        } else
          w.playerFrame = w.character(
            c,
            w.avatar,
            a.x,
            a.y,
            w.avatar === "gatherer" ? 19 : 22,
            w.direction,
            w.moving,
            w.step,
            true,
          );
      }
      this.prop(c, "trellis", 103, 118, 28);
      this.prop(c, "seeds", 386, 177, 16);
      this.prop(c, "harvest", 421, 179, 20);
      this.prop(c, "watering_can", 373, 182, 13);
      if (p.estate.cosmetics.active.includes("jade_chimes"))
        this.prop(c, "chime", 99, 123, 24);
      if (ambient) {
        for (let i = 0; i < 10; i++) {
          const x = 80 + ((i * 47 + t * ((i % 3) + 1)) % 340),
            y = 110 + ((i * 27 + t * 0.6) % 120);
          c.fillStyle = i % 2 ? "#ffe9ad8a" : "#f8bdce8a";
          c.beginPath();
          c.ellipse(x, y, 0.8, 0.4, Math.sin(t + i), 0, Math.PI * 2);
          c.fill();
        }
        for (let i = 0; i < 3; i++) {
          const x = 110 + i * 95 + Math.sin(t * 0.6 + i) * 18,
            y = 113 + Math.sin(t * 0.9 + i) * 10;
          c.fillStyle = "#ffe0a8b0";
          c.beginPath();
          c.ellipse(
            x,
            y,
            1.4,
            Math.abs(Math.cos(t * 8 + i)) * 0.8,
            0,
            0,
            Math.PI * 2,
          );
          c.fill();
        }
      }
      this.effects = this.effects.filter((f) => t - f.at < 1.4);
      for (const fx of this.effects) {
        const b = this.layout.plots[fx.plot],
          age = t - fx.at;
        if (fx.kind === "water") {
          c.strokeStyle = "#a4e9ffae";
          c.lineWidth = 0.7;
          c.beginPath();
          c.moveTo(w.position.x - 4, w.position.y - 12);
          c.quadraticCurveTo(b.x + 19, b.y - 22, b.x, b.y - 1);
          c.stroke();
        }
        for (let i = 0; i < 12; i++) {
          const progress = age / 1.4;
          c.fillStyle =
            fx.kind === "water"
              ? "#a6edffcf"
              : fx.kind === "harvest"
                ? "#fce299bb"
                : "#adeda8bb";
          c.beginPath();
          c.arc(
            b.x + Math.sin(i * 2.4) * progress * 20,
            b.y - Math.sin(progress * Math.PI) * 15 + (i % 3) * 2,
            0.6,
            0,
            Math.PI * 2,
          );
          c.fill();
        }
      }
      c.restore();
      this.drawHUD(view);
    }
    btn(id, text, cls = "world-secondary", disabled = false) {
      return `<button class="${cls}" data-garden-id="${id}" ${disabled ? "disabled" : ""}>${text}</button>`;
    }
    drawHUD(view) {
      if (this.root.hidden) return;
      const p = view.profile,
        data = view.data,
        busy = this.working || !!this.pending || this.hooks.busy(),
        sig = JSON.stringify([
          this.selected,
          this.seed,
          p.stones,
          p.insight,
          p.estate.garden,
          p.estate.bag,
          this.pending,
          this.working,
          this.hooks.busy(),
        ]);
      if (sig !== this.signature) {
        this.signature = sig;
        this.renderHUD(view, busy);
        this.dirty = true;
      }
      const scale = this.box.width / 512;
      for (const bed of this.layout.plots) {
        const node = this.root.querySelector(
            `[data-garden-id="plot-${bed.index}"]`,
          ),
          screen = this.world.worldToScreen({ x: bed.x, y: bed.y + 13 });
        if (node)
          node.style.transform = `translate3d(${screen.x * scale}px,${screen.y * scale}px,0) translateX(-50%)`;
      }
      if (this.dirty) this.cacheButtons();
      for (const b of this.cached || []) {
        if (b.id.startsWith("plot-")) {
          const bed = this.layout.plots[Number(b.id.slice(5))],
            s = this.world.worldToScreen({ x: bed.x, y: bed.y + 13 });
          this.hooks.register({
            ...b.rect,
            id: b.id,
            x: s.x - b.rect.w / 2,
            y: s.y,
            disabled: b.node.disabled,
            fn: () => this.handlers.get(b.id)?.(),
          });
        } else
          this.hooks.register({
            ...b.rect,
            id: b.id,
            disabled: b.node.disabled,
            fn: () => this.handlers.get(b.id)?.(),
          });
      }
    }
    renderHUD(view, busy) {
      const p = view.profile,
        e = p.estate,
        d = view.data;
      this.handlers.clear();
      const tabs = [
        "Garden",
        "Alchemy",
        "Merchant",
        "Commissions",
        "Achievements",
        "Research",
        "Ledger",
      ];
      let html = `<header class="garden-header">${this.btn("back", icon("arrow") + " Sanctuary")}<div><small>A PLACE FOR WHAT RETURNS</small><h1>Spirit Fields</h1></div><span>${icon("stone")}${p.stones} ${icon("insight")}${p.insight}</span></header><nav class="garden-tabs">${tabs.map((t) => this.btn("estate-tab-" + t, t, t === "Garden" ? "world-primary" : "world-secondary")).join("")}</nav><div class="garden-bed-labels">${this.layout.plots
        .map((b) => {
          const plot = d.plots[b.index],
            locked = b.index >= e.garden.size;
          return this.btn(
            "plot-" + b.index,
            locked
              ? "Wild bed"
              : plot.crop
                ? plot.growth >= plot.need
                  ? "Ready to harvest"
                  : esc(d.crops.find((c) => c.id === plot.crop).name)
                : "Plant here",
            "garden-bed-label " +
              (locked
                ? "is-wild"
                : plot.crop && plot.growth >= plot.need
                  ? "is-ready"
                  : ""),
            this.working,
          );
        })
        .join(
          "",
        )}</div><div class="garden-world-hint"><kbd>WASD</kbd> Walk · Click a bed · <kbd>E</kbd> Inspect<br><small>Plants grow after completed expeditions, not real time.</small></div><div class="garden-improvements">${this.btn("expand", e.garden.size < 9 ? `Cultivate 3 more beds · ${d.expand_cost} stones` : "All nine beds cultivated", "world-secondary", busy || !d.expand_cost || p.stones < d.expand_cost)}${this.btn("irrigation", d.irrigation_cost ? `Irrigation ${e.garden.irrigation}/2 · ${d.irrigation_cost} stones` : "Irrigation complete", "world-secondary", busy || !d.irrigation_cost || p.stones < d.irrigation_cost)}${this.btn("nursery", icon("garden") + " Defend the nursery", "world-secondary", busy)}</div>`;
      this.handlers.set("back", () => this.hooks.open("title"));
      for (const t of tabs)
        this.handlers.set("estate-tab-" + t, () => this.hooks.tab(t));
      for (const b of this.layout.plots)
        this.handlers.set("plot-" + b.index, () => this.select(b.index));
      this.handlers.set("expand", () => this.hooks.act("expand", {}));
      this.handlers.set("irrigation", () => this.hooks.act("irrigation", {}));
      this.handlers.set("nursery", () => this.hooks.start("garden-defense"));
      if (this.selected !== null) {
        const i = this.selected,
          plot = d.plots[i],
          locked = i >= e.garden.size,
          crop = d.crops.find((c) => c.id === (plot.crop || this.seed));
        html += `<aside class="garden-inspector"><header><small>SPIRIT FIELD · BED ${i + 1}</small>${this.btn("bed-close", icon("close"), "world-close")}</header><h2>${locked ? "An untended patch" : plot.crop ? esc(crop.name) : "A little room to grow"}</h2>${locked ? `<p>Wildflowers have kept this bed company. Cultivate the next three beds when the sect can spare ${d.expand_cost} stones.</p>` : !plot.crop ? `<p>Choose a seed, then your cultivator will walk to the soil and plant it.</p><div class="garden-seed-list">${d.crops.map((c) => this.btn("seed-" + c.id, `<canvas width="60" height="60" data-crop="${c.id}"></canvas><span>${esc(c.name)}<small>${e.bag.seeds[c.id] || 0} seeds · ${c.growth} expedition${c.growth > 1 ? "s" : ""}</small></span>`, this.seed === c.id ? "is-selected" : "", busy)).join("")}</div>${this.btn("plant", this.pending ? "Walking to the bed…" : "Plant seed", "world-primary", busy || !e.bag.seeds[this.seed])}` : `<canvas class="garden-crop-portrait" width="170" height="140" data-crop="${plot.crop}" data-stage="${plot.growth >= plot.need ? 3 : plot.growth ? 2 : 1}"></canvas><p>${plot.growth >= plot.need ? "Ready to harvest" : plot.growth + " / " + plot.need + " completed expeditions"} · Yield ${plot.yield}</p><div class="garden-care">${this.btn("water", plot.watered ? "Watered" : "Water", "world-secondary", busy || plot.watered)}${this.btn("fertilize", plot.fertilized ? "Fertilized" : "Fertilize · " + e.bag.fertilizer, "world-secondary", busy || plot.fertilized || !e.bag.fertilizer)}${this.btn("harvest", "Gather harvest", "world-primary", busy || plot.growth < plot.need)}</div><small>Water and fertilizer improve the yield. Nothing withers while you are away.</small>`}</aside>`;
        this.handlers.set("bed-close", () => {
          this.selected = null;
          this.pending = null;
        });
        for (const c of d.crops)
          this.handlers.set("seed-" + c.id, () => (this.seed = c.id));
        for (const a of ["plant", "water", "fertilize", "harvest"])
          this.handlers.set(a, () => this.queue(a));
      }
      this.root.innerHTML = html;
      for (const canvas of this.root.querySelectorAll("[data-crop]")) {
        const f =
            this.crops[canvas.dataset.crop][Number(canvas.dataset.stage ?? 3)],
          c = canvas.getContext("2d"),
          h = canvas.height - 4,
          w = (h * f.w) / f.h;
        c.drawImage(
          this.images.crops,
          f.x,
          f.y,
          f.w,
          f.h,
          (canvas.width - w) / 2,
          2,
          w,
          h,
        );
      }
    }
    cacheButtons() {
      this.dirty = false;
      const box = this.root.getBoundingClientRect();
      this.cached = [];
      for (const node of this.root.querySelectorAll("button[data-garden-id]")) {
        const r = node.getBoundingClientRect();
        if (r.width && r.height)
          this.cached.push({
            node,
            id: node.dataset.gardenId,
            rect: {
              x: ((r.left - box.left) / box.width) * 512,
              y: ((r.top - box.top) / box.height) * 288,
              w: (r.width / box.width) * 512,
              h: (r.height / box.height) * 288,
            },
          });
      }
    }
    get snapshot() {
      return {
        selected: this.selected,
        seed: this.seed,
        pending: this.pending,
        working: this.working,
        position: { ...this.world.position },
        camera: { ...this.world.camera },
        action: this.world.action?.kind || null,
        actionFrame: this.world.playerFrame,
        facing: this.world.direction,
        plots: this.layout.plots,
      };
    }
  }
  return Garden;
})();
