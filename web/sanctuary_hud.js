/* Screen-space sanctuary interface: semantic buttons, illustrated map and stable HUD. */
window.VanDaoSanctuaryHUD = (() => {
  const paths = {
    stone:
      '<path fill="#85e8d0" d="m12 2 7 5 2 9-9 7L3 16l2-9Z"/><path fill="#d6fff0" d="m12 2-2 10-5-5Z"/><path fill="#3bafaf" d="m10 12 11 4-9 7Z"/><path fill="none" stroke="#eafffa" d="m5 7 5 5 9-5M10 12l2 11"/>',
    insight:
      '<path fill="#e7bd65" d="m12 1 3 7 8 4-8 3-3 8-3-8-8-3 8-4Z"/><path fill="#fff4bc" d="m12 5 2 5 5 2-5 2-2 5-2-5-5-2 5-2Z"/>',
    campaign:
      '<path d="M3 20h18M5 20V9h14v11M3 9l9-6 9 6M9 20v-6h6v6M10 7h4"/>',
    training:
      '<path d="m4 20 5-5M7 18l-2-2m4-1 9-12 3 3-12 9m3-1 7 7m-2-4 3-3M5 3l5 6"/>',
    archive:
      '<path d="M12 5v16m0-16C8 2 5 3 2 4v15c4-2 7-1 10 2 3-3 6-4 10-2V4c-3-1-6-2-10 1ZM5 8l4 1m-4 3 4 1m6-4 4-1m-4 5 4-1"/>',
    alchemy:
      '<path d="M7 7h10l3 7c2 6-2 8-8 8s-10-2-8-8Zm-2 3h14M9 7V3m6 4V3M8 3h8m-9 14h10m-6-4v6m-6 2-1 2m13-2 1 2"/>',
    garden:
      '<path d="M12 22V9m0 7C4 17 2 12 3 8c6-1 10 2 9 8Zm0-5c-1-7 2-10 8-9 1 6-2 10-8 9ZM4 22h16"/>',
    merchant:
      '<path d="M3 9h18l-2-6H5Zm1 0v12h16V9M2 9v3c0 3 4 3 5 0 1 3 4 3 5 0 1 3 4 3 5 0 1 3 5 3 5 0V9M9 21v-6h6v6"/>',
    missions: '<path d="M7 4H4v18h16V4h-3M8 2h8v5H8Zm0 10 2 2 5-5m-7 9h8"/>',
    trials:
      '<path d="M5 22V9a7 7 0 0 1 14 0v13M2 22h20M9 22V10a3 3 0 0 1 6 0v12m-3-12 1 3 3 1-3 1-1 3-1-3-3-1 3-1Z"/>',
    map: '<path d="m2 5 6-3 8 3 6-3v17l-6 3-8-3-6 3Zm6-3v17m8-14v17M4 8l2-1m5 3 2 1m5-2 2-1"/>',
    settings:
      '<path d="m9 2-.5 3-3 2-3-.5-1 4 2.5 1.5v3L2 17l2 3 3-1 3 1 .5 2h4l.5-2 3-1 2 1 2-3-2-2v-3l2-2-1-4-3 .5-3-2L15 2Zm3 6a4 4 0 1 1 0 8 4 4 0 0 1 0-8Z"/>',
    saves: '<path d="M4 2h13l4 4v16H3V2Zm3 0v7h10V2M7 22v-9h10v9m-6-17h3"/>',
    avatar:
      '<circle cx="12" cy="7" r="4"/><path d="M4 22v-4a8 8 0 0 1 16 0v4M8 3l-2 3m10-3 2 3"/>',
    close: '<path d="m6 6 12 12M18 6 6 18"/>',
    arrow: '<path d="M4 12h16m-6-6 6 6-6 6"/>',
    plus: '<path d="M12 4v16M4 12h16"/>',
    minus: '<path d="M4 12h16"/>',
    pin: '<path d="m7 3 10 0-1 6 4 5H4l4-5Zm5 11v9"/>',
    check: '<path d="m4 12 5 5L21 5"/>',
  };
  const icon = (id) =>
    '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">' +
    (paths[id] || paths.insight) +
    "</svg>";
  const esc = (v) =>
    String(v ?? "").replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  const facilityIcon = (id) =>
    ({ roster: "training", estate: "garden", begin: "campaign" })[id] || id;
  class HUD {
    constructor(world, container) {
      this.world = world;
      this.handlers = new Map();
      this.cache = [];
      this.dirty = true;
      this.visible = false;
      this.signature = "";
      this.modalKey = "";
      this.selected = "campaign";
      this.root = document.createElement("div");
      this.root.id = "sanctuary-hud";
      this.root.className = "sanctuary-hud";
      this.root.hidden = true;
      this.root.innerHTML = `<div class="hub-top-left"><button class="hub-profile" data-hub-id="avatar"><canvas width="112" height="112" class="hub-portrait"></canvas><span><b>VAN DAO</b><small>Celestial Sanctuary</small></span><span class="hub-profile-arrow">⌄</span></button><div class="hub-area-name">THE IMMORTAL SECT <span>Peaceful grounds</span></div></div>
    <div class="hub-top-right"><div class="hub-wallet"><div class="hub-currency" title="Spirit Stones · earned through battles, commissions and trading">${icon("stone")}<span><small>Spirit Stones</small><strong data-value="stones">0</strong></span></div><div class="hub-currency" title="Insight · used for talents and research">${icon("insight")}<span><small>Insight</small><strong data-value="insight">0</strong></span></div></div><button class="hub-settings hub-square" data-hub-id="settings" title="Settings" aria-label="Settings">${icon("settings")}</button></div>
    <button class="hub-minimap" data-hub-id="hub-map" aria-label="Open sanctuary map"><span class="hub-minimap-image"><i class="hub-map-player"></i><i class="hub-map-view"></i></span><span>${icon("map")} Sanctuary Map <kbd>M</kbd></span></button>
    <div class="hub-world-labels"></div><aside class="hub-quest" hidden></aside>
    <div class="hub-controls"><span><kbd>W A S D</kbd> Move</span><span><kbd>Shift</kbd> Run</span><span><kbd>E</kbd> Talk</span></div>
    <div class="hub-zoom"><button data-hub-id="hub-zoom-out" aria-label="Zoom out">${icon("minus")}</button><span data-value="zoom">1.85×</span><button data-hub-id="hub-zoom-in" aria-label="Zoom in">${icon("plus")}</button></div>
    <div class="hub-interaction" hidden></div><nav class="hub-dock" aria-label="Sect facilities"></nav><div class="hub-resume"></div><div class="hub-modal-layer" hidden></div>`;
      container.appendChild(this.root);
      const dock = [
        ["begin", "Campaign", "campaign"],
        ["estate", "Garden", "Garden"],
        ["alchemy", "Alchemy", "Alchemy"],
        ["roster", "Talents", "roster"],
        ["archive", "Archive", "archive"],
        ["merchant", "Market", "Merchant"],
        ["missions", "Missions", "missions"],
        ["trials", "Trials", "trials"],
        ["saves", "Chronicles", "saves"],
      ];
      this.root.querySelector(".hub-dock").innerHTML = dock
        .map(
          ([id, label]) =>
            `<button class="hub-dock-button ${id === "begin" ? "hub-featured" : ""}" data-hub-id="${id}"><span class="hub-dock-icon">${icon(facilityIcon(id === "alchemy" ? "alchemy" : id === "merchant" ? "merchant" : id))}</span><span>${label}</span></button>`,
        )
        .join("");
      for (const [id, , action] of dock)
        this.handlers.set(id, () => this.open(action));
      this.handlers.set("settings", () => this.open("settings"));
      this.handlers.set("avatar", () => world.openAvatar());
      this.handlers.set("hub-map", () => world.openMap());
      this.handlers.set("hub-zoom-out", () =>
        world.setZoom((world.zoomTarget || world.camera.zoom) - 0.2),
      );
      this.handlers.set("hub-zoom-in", () =>
        world.setZoom((world.zoomTarget || world.camera.zoom) + 0.2),
      );
      this.labels = new Map();
      for (const f of world.map.facilities) {
        const b = document.createElement("button");
        b.className = "hub-world-label";
        b.dataset.hubId = "hub-go-" + f.id;
        b.innerHTML = `${icon(f.id)}<span>${esc(f.name)}</span>`;
        b.title = f.keeper;
        b.setAttribute("aria-label", f.name + " — speak to " + f.keeper);
        this.root.querySelector(".hub-world-labels").appendChild(b);
        this.labels.set(f.id, b);
        this.handlers.set(b.dataset.hubId, () => world.go(f.id));
      }
      this.root.addEventListener("pointerdown", (e) => {
        if (e.target.closest("button,input,.hub-modal")) {
          e.stopPropagation();
          world.hooks.chime();
        }
      });
      this.root.addEventListener("click", (e) => {
        const b = e.target.closest("button[data-hub-id]");
        if (b && !b.disabled) {
          if (!e.detail) world.hooks.chime();
          this.handlers.get(b.dataset.hubId)?.();
          this.dirty = true;
          document.querySelector("#game").focus({ preventScroll: true });
        }
      });
      this.root.addEventListener("keydown", (e) => {
        if (
          [
            "ArrowUp",
            "ArrowDown",
            "ArrowLeft",
            "ArrowRight",
            "KeyW",
            "KeyA",
            "KeyS",
            "KeyD",
          ].includes(e.code) &&
          e.target.closest("button")
        )
          e.preventDefault();
      });
      this.resizeObserver = new ResizeObserver(() => {
        this.layout();
        this.dirty = true;
      });
      this.resizeObserver.observe(document.querySelector("#game"));
      this.layout();
      this.loadIconArt();
    }
    loadIconArt() {
      const atlas = this.world.atlas,
        source = atlas.sources?.icons;
      if (!source || !atlas.icons) return;
      const image = new Image();
      image.onload = () => {
        const paint = (node, id) => {
          const f = atlas.icons[id];
          if (!node || !f) return;
          node.style.backgroundImage = 'url("/assets/hub/icons.png")';
          node.style.backgroundSize =
            (source.width / f.w) * 100 +
            "% " +
            (source.height / f.h) * 100 +
            "%";
          node.style.backgroundPosition =
            (f.x / (source.width - f.w)) * 100 +
            "% " +
            (f.y / (source.height - f.h)) * 100 +
            "%";
          node.classList.add("hub-painted");
        };
        for (const button of this.root.querySelectorAll(".hub-dock-button"))
          paint(
            button.querySelector(".hub-dock-icon"),
            facilityIcon(button.dataset.hubId),
          );
        for (const [index, id] of ["stone", "insight"].entries()) {
          const container = this.root.querySelectorAll(".hub-currency")[index],
            art = document.createElement("i");
          art.className = "hub-currency-art";
          art.setAttribute("aria-hidden", "true");
          container.prepend(art);
          paint(art, id);
        }
        this.root.classList.add("hub-has-art");
        this.dirty = true;
      };
      image.src = "/assets/hub/icons.png";
    }
    layout() {
      const canvas = document.querySelector("#game"),
        box = canvas.getBoundingClientRect(),
        parent = this.root.parentElement.getBoundingClientRect();
      Object.assign(this.root.style, {
        left: box.left - parent.left + "px",
        top: box.top - parent.top + "px",
        width: box.width + "px",
        height: box.height + "px",
      });
      this.root.style.setProperty(
        "--ui-scale",
        Math.max(0.68, Math.min(1.4, box.width / 1280)),
      );
      this.box = box;
      this.dirty = true;
    }
    setVisible(value) {
      if (this.visible !== value) {
        this.visible = value;
        this.root.hidden = !value;
        if (value) {
          this.layout();
          this.dirty = true;
        } else this.modalKey = "";
      }
    }
    invalidate() {
      this.signature = "";
      this.modalKey = "";
      this.dirty = true;
    }
    open(action) {
      this.world.stop();
      this.world.persist();
      this.world.dialog = null;
      this.world.hooks.open(action);
    }
    draw(view) {
      this.setVisible(view.active);
      if (!view.active) return;
      this.view = view;
      const w = this.world,
        p = view.profile,
        e = p.estate,
        near = w.nearest();
      const signature = JSON.stringify([
        p.stones,
        p.insight,
        e?.hub?.avatar,
        e?.hub?.tracked,
        view.data?.contracts,
        view.resume,
      ]);
      if (signature !== this.signature) {
        this.signature = signature;
        this.root.querySelector('[data-value="stones"]').textContent =
          p.stones.toLocaleString();
        this.root.querySelector('[data-value="insight"]').textContent =
          p.insight.toLocaleString();
        this.drawPortrait();
        this.updateQuest();
        const resume = this.root.querySelector(".hub-resume");
        resume.innerHTML = view.resume
          ? `<button data-hub-id="resume">${icon("campaign")} Resume battle</button>`
          : "";
        this.handlers.set("resume", () => this.open("resume"));
        this.dirty = true;
      }
      const scale = this.box.width / 512;
      for (const f of w.map.facilities) {
        const node = this.labels.get(f.id),
          screen = w.worldToScreen({ x: f.x, y: f.y + 7 });
        const show =
          !w.dialog &&
          screen.x > 22 &&
          screen.x < 490 &&
          screen.y > 58 &&
          screen.y < 239 &&
          Math.hypot(f.x - w.position.x, f.y - w.position.y) < 95;
        node.style.transform = `translate3d(${screen.x * scale}px,${screen.y * scale}px,0) translate(-50%,0)`;
        node.classList.toggle("is-visible", show);
        node.classList.toggle("is-near", near.f.id === f.id && near.d < 23);
        node.tabIndex = show ? 0 : -1;
      }
      const mapPlayer = this.root.querySelector(".hub-map-player"),
        mapView = this.root.querySelector(".hub-map-view");
      mapPlayer.style.left = (w.position.x / 512) * 100 + "%";
      mapPlayer.style.top = (w.position.y / 288) * 100 + "%";
      mapView.style.left =
        ((w.camera.x - 256 / w.camera.zoom) / 512) * 100 + "%";
      mapView.style.top =
        ((w.camera.y - 144 / w.camera.zoom) / 288) * 100 + "%";
      mapView.style.width = 100 / w.camera.zoom + "%";
      mapView.style.height = 100 / w.camera.zoom + "%";
      this.root.querySelector('[data-value="zoom"]').textContent =
        w.camera.zoom.toFixed(2) + "×";
      const interaction = this.root.querySelector(".hub-interaction"),
        interactKey = !w.dialog && near.d < 21 ? near.f.id : "";
      if (this.interactKey !== interactKey) {
        this.interactKey = interactKey;
        interaction.hidden = !interactKey;
        interaction.innerHTML = interactKey
          ? `<button data-hub-id="hub-interact"><kbd>E</kbd><span><small>${esc(near.f.name)}</small><b>Speak to ${esc(near.f.keeper)}</b></span>${icon("arrow")}</button>`
          : "";
        this.handlers.set("hub-interact", () => w.talk(near.f));
        this.dirty = true;
      }
      const modalKey = JSON.stringify([
        w.dialog,
        p.settings.hubMotion,
        e?.hub?.avatar,
        p.completed,
        view.busy,
        view.data?.contracts,
      ]);
      if (modalKey !== this.modalKey) {
        this.modalKey = modalKey;
        this.renderModal();
        this.dirty = true;
      }
      if (this.dirty) this.cacheButtons();
      for (const b of this.cache) {
        if (b.node.classList.contains("hub-world-label")) {
          if (!b.node.classList.contains("is-visible")) continue;
          const f = w.map.facilities.find((f) => "hub-go-" + f.id === b.id),
            s = w.worldToScreen({ x: f.x, y: f.y + 7 });
          this.world.hooks.register({
            ...b.rect,
            id: b.id,
            x: s.x - b.rect.w / 2,
            y: s.y,
            fn: () => this.handlers.get(b.id)?.(),
            disabled: false,
          });
        } else
          this.world.hooks.register({
            ...b.rect,
            id: b.id,
            fn: () => this.handlers.get(b.id)?.(),
            disabled: b.node.disabled,
          });
      }
    }
    drawPortrait() {
      const c = this.root.querySelector(".hub-portrait").getContext("2d"),
        f = this.world.atlas.npcs[this.world.avatar];
      c.clearRect(0, 0, 112, 112);
      if (f) {
        const scale = 160 / f.h;
        c.drawImage(
          this.world.assets.hub_npcs,
          f.x,
          f.y,
          f.w,
          f.h,
          56 - (f.w * scale) / 2,
          2,
          f.w * scale,
          f.h * scale,
        );
      }
    }
    updateQuest() {
      const q = this.view.data?.contracts.find(
          (q) => q.id === this.view.profile.estate.hub?.tracked && !q.claimed,
        ),
        box = this.root.querySelector(".hub-quest");
      box.hidden = !q;
      if (!q) return;
      box.innerHTML = `<div class="hub-quest-heading">${icon("missions")} SECT COMMISSION<button data-hub-id="hub-unpin" title="Unpin">${icon("close")}</button></div><b>${esc(q.name)}</b><p>${esc(q.description)}</p><div class="hub-progress"><i style="width:${Math.min(100, (q.progress / q.target) * 100)}%"></i></div><small>${q.progress} / ${q.target}</small>`;
      this.handlers.set("hub-unpin", () => this.world.hooks.track(null));
    }
    cacheButtons() {
      this.dirty = false;
      const box = this.root.getBoundingClientRect(),
        modal = !!this.world.dialog;
      this.cache = [];
      for (const node of this.root.querySelectorAll("button[data-hub-id]")) {
        if (modal && !node.closest(".hub-modal-layer")) continue;
        if (node.closest("[hidden]")) continue;
        const r = node.getBoundingClientRect();
        if (!r.width || !r.height) continue;
        this.cache.push({
          node,
          id: node.dataset.hubId,
          rect: {
            x: ((r.left - box.left) / box.width) * 512,
            y: ((r.top - box.top) / box.height) * 288,
            w: (r.width / box.width) * 512,
            h: (r.height / box.height) * 288,
          },
        });
      }
    }
    shell(title, subtitle, content, kind = "") {
      return `<section class="hub-modal ${kind}" role="dialog" aria-modal="true" aria-label="${esc(title)}"><header><div><small>VAN DAO · IMMORTAL SECT</small><h1>${title}</h1><p>${subtitle}</p></div><button class="hub-square" data-hub-id="hub-close" aria-label="Close">${icon("close")}</button></header>${content}</section>`;
    }
    renderModal() {
      const layer = this.root.querySelector(".hub-modal-layer"),
        w = this.world,
        d = w.dialog,
        v = this.view;
      layer.hidden = !d;
      for (const child of this.root.children)
        child.inert = !!d && child !== layer;
      this.handlers.set("hub-close", () => {
        w.dialog = null;
      });
      if (!d) {
        layer.innerHTML = "";
        return;
      }
      if (d.kind === "map") {
        const selected =
          w.map.facilities.find((f) => f.id === this.selected) ||
          w.map.facilities[0];
        layer.innerHTML = this.shell(
          "Sanctuary Map",
          "Choose a landmark, then travel there or open its facilities.",
          `<div class="hub-cartography"><img src="/assets/hub/cartography.png" alt="Illustrated sanctuary map with the Grand Hall, lotus fountain, garden, market and connected paths" draggable="false">${w.map.facilities.map((f) => `<button class="hub-map-landmark ${f.id === selected.id ? "is-selected" : ""}" style="left:${(f.x / 512) * 100}%;top:${(f.y / 288) * 100}%" data-hub-id="hub-directory-${f.id}" title="${esc(f.name)}" aria-label="Select ${esc(f.name)}"><span>${icon(f.id)}</span><b>${esc(f.name)}</b></button>`).join("")}<i class="hub-full-map-player" style="left:${(w.position.x / 512) * 100}%;top:${(w.position.y / 288) * 100}%" title="You are here"></i><span class="hub-map-legend"><i></i> You are here</span></div><footer class="hub-map-footer"><div>${icon(selected.id)}<span><b>${esc(selected.name)}</b><small>${esc(selected.keeper)} · ${esc(selected.title)}</small></span></div><button class="hub-secondary" data-hub-id="hub-direct-${selected.id}">Open facility</button><button class="hub-primary" data-hub-id="hub-walk-${selected.id}">${icon("arrow")} Travel here</button></footer>`,
          "hub-map-modal",
        );
        for (const f of w.map.facilities) {
          this.handlers.set("hub-directory-" + f.id, () => {
            this.selected = f.id;
            this.modalKey = "";
          });
          this.handlers.set("hub-walk-" + f.id, () => w.go(f.id));
          this.handlers.set("hub-direct-" + f.id, () => this.open(f.action));
        }
      } else if (d.kind === "avatar") {
        layer.innerHTML = this.shell(
          "Your Sanctuary Presence",
          "Choose how you explore the sect. Appearance does not change battle stats.",
          `<div class="hub-avatar-grid">${w.map.avatars
            .map((a) => {
              const open = a.realm <= v.realm;
              return `<article class="${a.id === w.avatar ? "is-selected" : ""} ${open ? "" : "is-locked"}"><canvas data-avatar="${a.id}" width="180" height="210"></canvas><b>${esc(a.name)}</b><button class="${a.id === w.avatar ? "hub-secondary" : "hub-primary"}" data-hub-id="hub-avatar-${a.id}" ${!open || v.busy ? "disabled" : ""}>${!open ? "Clear Wharf III" : a.id === w.avatar ? "Selected" : "Choose appearance"}</button></article>`;
            })
            .join(
              "",
            )}</div><footer><button class="hub-secondary" data-hub-id="hub-ambient">Ambient motion: ${v.profile.settings.hubMotion === false ? "Off" : "On"}</button><span class="hub-modal-note">Camera motion follows your character.</span></footer>`,
          "hub-avatar-modal",
        );
        for (const a of w.map.avatars) {
          this.handlers.set("hub-avatar-" + a.id, () => w.hooks.avatar(a.id));
          const canvas = layer.querySelector(`[data-avatar="${a.id}"]`),
            c = canvas.getContext("2d");
          w.cutout(c, w.assets.hub_npcs, w.atlas.npcs[a.id], 90, 200, 180);
        }
        this.handlers.set("hub-ambient", () => w.hooks.motion());
      } else if (d.kind === "commissions") {
        layer.innerHTML = this.shell(
          "Commissions of the Sect",
          "Follow a commission to keep it in view. All eligible progress counts automatically.",
          `<div class="hub-commission-list">${(v.data?.contracts || [])
            .map((q) => {
              const ready = q.progress >= q.target,
                tracked = v.profile.estate.hub?.tracked === q.id;
              return `<article><div class="hub-commission-symbol">${icon(q.claimed ? "check" : "missions")}</div><div><h2>${esc(q.name)}</h2><p>${esc(q.description)}</p><div class="hub-progress"><i style="width:${Math.min(100, (q.progress / q.target) * 100)}%"></i></div><small>${q.progress} / ${q.target} · Reward: ${esc(VanDaoEstate.reward(q.reward))}</small></div><button data-hub-id="hub-contract-${q.id}" class="${ready && !q.claimed ? "hub-primary" : "hub-secondary"}" ${q.claimed || v.busy ? "disabled" : ""}>${q.claimed ? "Claimed" : ready ? "Claim reward" : tracked ? "Following" : "Follow quest"}</button></article>`;
            })
            .join(
              "",
            )}</div><footer><button class="hub-secondary" data-hub-id="hub-full-missions">Open mission ledger</button></footer>`,
          "hub-commission-modal",
        );
        for (const q of v.data?.contracts || [])
          this.handlers.set("hub-contract-" + q.id, () =>
            q.progress >= q.target ? w.hooks.claim(q.id) : w.hooks.track(q.id),
          );
        this.handlers.set("hub-full-missions", () => this.open("Commissions"));
      } else {
        const f = w.map.facilities.find((f) => f.id === d.id);
        if (!f) return;
        layer.innerHTML = this.shell(
          esc(f.name),
          "",
          `<div class="hub-conversation"><canvas width="280" height="340" class="hub-npc-portrait"></canvas><div><small>${esc(f.title)}</small><h2>${esc(f.keeper)}</h2><p>${esc(f.greeting)}</p><button class="hub-primary" data-hub-id="hub-open-${f.id}">${esc(f.offer)}${icon("arrow")}</button><span class="hub-modal-note"><kbd>Enter</kbd> Continue · <kbd>Esc</kbd> Leave</span></div></div>`,
          "hub-conversation-modal",
        );
        const c = layer.querySelector("canvas").getContext("2d");
        w.cutout(c, w.assets.hub_npcs, w.atlas.npcs[f.npc], 140, 325, 300);
        this.handlers.set("hub-open-" + f.id, () => w.activate(f));
      }
    }
  }
  return HUD;
})();
