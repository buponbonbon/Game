/* Original journey map and optional conversations. Decisions are saved by Python. */
window.VanDaoAdventure = (() => {
  const UI = () => VanDaoSanctuaryHUD,
    esc = (v) => UI().escape(v),
    icon = (id) => UI().icon(id);
  class Adventure {
    constructor(data, assets, art, hooks) {
      Object.assign(this, { data, assets, art, hooks });
      this.selected = data.chapters[0].id;
      this.dialog = null;
      this.signature = "";
      this.notice = null;
      this.root = document.createElement("div");
      this.root.className = "world-ui adventure-ui";
      this.root.hidden = true;
      hooks.root.appendChild(this.root);
      this.handlers = new Map();
      this.dirty = true;
      this.box = null;
      this.root.addEventListener("click", (e) => {
        const b = e.target.closest("button[data-world-id]");
        if (b && !b.disabled) {
          hooks.chime();
          this.handlers.get(b.dataset.worldId)?.();
          this.signature = "";
          document.querySelector("#game").focus({ preventScroll: true });
        }
      });
      this.resizeObserver = new ResizeObserver(() => this.layout());
      this.resizeObserver.observe(document.querySelector("#game"));
      this.layout();
    }
    layout() {
      const c = document.querySelector("#game").getBoundingClientRect(),
        p = this.root.parentElement.getBoundingClientRect();
      Object.assign(this.root.style, {
        left: c.left - p.left + "px",
        top: c.top - p.top + "px",
        width: c.width + "px",
        height: c.height + "px",
      });
      this.root.style.setProperty(
        "--world-scale",
        Math.max(0.65, Math.min(1.4, c.width / 1280)),
      );
      this.box = c;
      this.dirty = true;
    }
    reset() {
      this.dialog = null;
      this.signature = "";
      this.notice = null;
    }
    get hasModal() {
      return !!this.dialog;
    }
    open(id) {
      const c = this.data.chapters.find((c) => c.id === id);
      if (!c) return;
      this.selected = id;
      this.dialog = { kind: "chapter", id, page: 0 };
      if (this.unlocked(c)) this.hooks.act("story_seen", { chapter: id }, true);
      this.signature = "";
    }
    converse(id) {
      this.dialog = { kind: "person", id, topic: -1 };
      if (this.data.npcs.some((n) => n.id === id))
        this.hooks.act("story_met", { npc: id }, true);
      this.signature = "";
    }
    journal() {
      this.dialog = { kind: "journal" };
      this.signature = "";
    }
    observe(item) {
      this.hooks.act("story_observe", { id: item.id }, true);
      this.notice = { ...item, until: performance.now() + 6500 };
      this.signature = "";
    }
    unlocked(c) {
      const i = this.data.chapters.indexOf(c),
        p = this.hooks.profile();
      return (
        i === 0 ||
        p.completed.includes(this.data.chapters[i - 1].id) ||
        p.completed.includes(c.id)
      );
    }
    person(id) {
      return (
        this.data.npcs.find((n) => n.id === id) ||
        this.data.cultivators?.[id] ||
        this.hooks.heroes[id] || {
          id,
          name: id,
          title: "Cultivator",
          topics: [
            [
              "The roads ahead",
              "Every journey leaves something worth listening to. Speak to the travelers beside the fountain, or open the journey map to hear their requests.",
            ],
          ],
        }
      );
    }
    changedStory(n) {
      const p = this.hooks.profile(),
        choices = p.estate.story.choices;
      let text =
        n.topics?.[0]?.[1] || "The sect has room for many kinds of journeys.";
      const cleared =
        n.id === "mei" || n.id === "tao"
          ? "wharf-3"
          : n.id === "qiao"
            ? "terrace-3"
            : "tomb-3";
      const partial = {
        mei: [
          "wharf-1",
          "My brother returned with the lamp keepers. He is resting beside the ferry now. The harbor still needs the river palace bell to fall quiet before everyone can come home.",
        ],
        tao: [
          "wharf-2",
          "The bridge is holding. We found a court seal beneath the mountain mark; I have kept the wick as evidence. Now we must learn why the palace bell answers it.",
        ],
        qiao: [
          "terrace-1",
          "Clean water has reached the lower gardens. The villagers are carrying living seed over the cloud bridge. I want the upper wards to hear what they have survived.",
        ],
        ren: [
          "terrace-2",
          "The letters crossed the bridge at last. People who had stopped speaking are reading one another again. The mountain lord has not answered his packet yet.",
        ],
        suyin: [
          "tomb-1",
          "The gate opened when we restored the missing names. There are records still burning at the spirit pyres. I am keeping a place in the archive for every voice we can bring back.",
        ],
      };
      if (partial[n.id] && p.completed.includes(partial[n.id][0]))
        text = partial[n.id][1];
      if (n.id === "lin" && (p.estate.stats.harvests || 0) > 0)
        text =
          "Your first harvest has gone into the stores. That is something we can offer the next traveler before asking where they have been. Keep a little soil open for whatever they bring.";
      if (p.completed.includes(cleared) && n.after) text = n.after;
      if (n.id === "mei" && choices["wharf-1"] === "families")
        text +=
          " I kept your list of families. They asked me to thank you for remembering their names.";
      if (n.id === "qiao" && choices["terrace-1"] === "trace")
        text +=
          " The script you asked us to trace is copied in the archive now.";
      if (n.id === "suyin" && choices["tomb-1"] === "invite")
        text +=
          " I have left a blank page for everyone who chose not to speak.";
      return text;
    }
    favorProgress(f) {
      const p = this.hooks.profile();
      return f.kind === "observations"
        ? p.estate.story.observations.length
        : f.kind === "harvests"
          ? p.estate.stats.harvests || 0
          : Number(p.completed.includes("wharf-3"));
    }
    key(code) {
      if (code === "Escape") {
        if (this.dialog) {
          this.dialog = null;
          this.signature = "";
          return true;
        }
        return false;
      }
      if (!this.dialog) return false;
      if (code === "Enter" && this.dialog.kind === "chapter") {
        const c = this.data.chapters.find((c) => c.id === this.dialog.id);
        if (this.dialog.page < c.pages.length - 1) this.dialog.page++;
        this.signature = "";
        return true;
      }
      return !["Tab"].includes(code);
    }
    draw(c, view) {
      this.view = view;
      this.mode = view.scene;
      const visible =
        !view.overlay &&
        (view.scene === "campaign" ||
          !!this.dialog ||
          (this.notice &&
            performance.now() < this.notice.until &&
            view.scene === "title"));
      this.root.hidden = !visible;
      if (!visible) return;
      if (view.scene === "campaign") {
        c.save();
        c.imageSmoothingEnabled = true;
        c.drawImage(this.assets.campaign_map, 0, 0, 512, 288);
        c.fillStyle = "#071d261a";
        c.fillRect(0, 0, 512, 288);
        c.restore();
      }
      const p = this.hooks.profile();
      if (!p.estate?.story) {
        this.root.hidden = true;
        return;
      }
      const signature = JSON.stringify([
        this.mode,
        this.dialog,
        this.selected,
        p.completed,
        p.estate.story,
        p.stones,
        this.hooks.busy(),
        this.notice?.id,
        !!this.notice && performance.now() < this.notice.until,
      ]);
      if (signature !== this.signature) {
        this.signature = signature;
        this.render();
        this.dirty = true;
      }
      if (this.dirty) this.cacheButtons();
      for (const b of this.cached || [])
        this.hooks.register({
          ...b.rect,
          id: b.id,
          disabled: b.node.disabled,
          fn: () => this.handlers.get(b.id)?.(),
        });
    }
    button(id, label, cls = "world-secondary", disabled = false) {
      return `<button class="${cls}" data-world-id="${id}" ${disabled ? "disabled" : ""}>${label}</button>`;
    }
    portrait(id) {
      return `<canvas class="story-portrait" width="270" height="320" data-person="${esc(id)}"></canvas>`;
    }
    panel(title, sub, body, cls = "") {
      return `<div class="world-veil"><section class="world-panel ${cls}" role="dialog" tabindex="-1" aria-modal="true" aria-label="${esc(title)}"><header><div><small>VAN DAO · TALES OF THE THREE LANDS</small><h1>${esc(title)}</h1><p>${esc(sub)}</p></div>${this.button("story-close", icon("close"), "world-close")}</header>${body}</section></div>`;
    }
    render() {
      this.handlers.clear();
      this.handlers.set("story-close", () => (this.dialog = null));
      let html = "";
      const p = this.hooks.profile(),
        busy = this.hooks.busy();
      if (this.mode === "campaign") {
        html = `<header class="journey-header">${this.button("back", icon("arrow") + " Sanctuary")}<div><small>THE FRACTURED LEYLINES</small><h1>Roads of the Three Lands</h1></div>${this.button("journey-journal", icon("archive") + " Journey journal")}</header><div class="journey-region region-wharf">I · Lantern Wharf</div><div class="journey-region region-terrace">II · Azure Terrace</div><div class="journey-region region-tomb">III · Bone Tomb</div><svg class="journey-route" viewBox="0 0 100 100" preserveAspectRatio="none"><path d="M14 72 Q18 58 23 51 T31 28 Q38 37 43 67 Q47 60 51 43 T60 24 Q65 39 71 70 Q76 57 80 48 T89 24"/></svg>`;
        html += this.data.chapters
          .map((c, i) => {
            const done = p.completed.includes(c.id),
              open = this.unlocked(c);
            return `<button class="journey-node ${done ? "is-complete" : open ? "is-open" : "is-locked"} ${this.selected === c.id ? "is-selected" : ""}" style="left:${c.x}%;top:${c.y}%" data-world-id="stage-${c.id}" aria-label="${esc(c.title)}${open ? "" : " · locked"}"><i>${done ? icon("check") : open ? (i % 3 === 2 ? icon("trials") : (i % 3) + 1) : icon("lock")}</i><b>${esc(c.location)}</b><small>${done ? "Completed" : open ? "Hear the request" : "Road not yet open"}</small></button>`;
          })
          .join("");
        const selected = this.data.chapters.find((c) => c.id === this.selected);
        html += `<footer class="journey-overview"><div><small>${esc(selected.region.toUpperCase())} · ${esc(selected.location)}</small><h2>${esc(selected.title)}</h2><p>${esc(selected.reason)}</p></div>${this.button("journey-story", "Meet the witnesses " + icon("arrow"), "world-primary")}</footer>`;
        this.handlers.set("back", () => this.hooks.open("title"));
        this.handlers.set("journey-journal", () => this.journal());
        this.handlers.set("journey-story", () => this.open(selected.id));
        for (const c of this.data.chapters)
          this.handlers.set("stage-" + c.id, () => this.open(c.id));
      }
      const d = this.dialog;
      if (d?.kind === "chapter") {
        const c = this.data.chapters.find((c) => c.id === d.id),
          n = this.person(c.speaker),
          open = this.unlocked(c),
          done = p.completed.includes(c.id),
          choice = c.choices.find((v) => v.id === p.estate.story.choices[c.id]);
        const text = !open
          ? "This road opens after the preceding encounter. The people here will tell their story when you can reach them."
          : done && d.page === 0
            ? c.aftermath
            : c.pages[d.page];
        const choices =
          open && d.page === c.pages.length - 1
            ? `<div class="story-choices"><small>What would you say?</small>${c.choices.map((v) => this.button("story-choice-" + v.id, esc(v.label), choice?.id === v.id ? "world-primary" : "world-secondary", busy)).join("")}</div>${choice ? `<p class="story-reply">${esc(choice.response)}</p>` : ""}`
            : "";
        html += this.panel(
          c.title,
          c.location +
            " · " +
            (done ? "After the encounter" : "Before the journey"),
          `<div class="story-conversation">${this.portrait(c.speaker)}<div><small>${esc(n.title || n.role || "Cultivator")}</small><h2>${esc(n.name)}</h2><p class="story-prose">${esc(text)}</p><div class="story-pages">${c.pages.map((_, i) => this.button("story-page-" + i, String(i + 1), i === d.page ? "is-current" : "")).join("")}</div>${choices}</div></div><footer class="story-footer"><p>${icon("campaign")} ${esc(c.reason)}</p>${this.button("story-next", d.page < c.pages.length - 1 ? "Read on" : "Read again", "world-secondary", !open)}${this.button("start", done ? "Revisit encounter" : "Begin encounter", "world-primary", !open || busy)}</footer>`,
          "chapter-dialogue",
        );
        for (let i = 0; i < c.pages.length; i++)
          this.handlers.set("story-page-" + i, () => {
            if (open) d.page = i;
          });
        this.handlers.set(
          "story-next",
          () => (d.page = (d.page + 1) % c.pages.length),
        );
        this.handlers.set("start", () => {
          this.dialog = null;
          this.hooks.start(c.id);
        });
        for (const v of c.choices)
          this.handlers.set("story-choice-" + v.id, () =>
            this.hooks.act(
              "story_choice",
              { chapter: c.id, choice: v.id },
              true,
            ),
          );
      } else if (d?.kind === "person") {
        const n = this.person(d.id),
          topics = n.topics || [
            [
              "The journey",
              "We defend these roads so that people can return to their own lives. Ask the travelers about the places they call home.",
            ],
            [
              "A quiet moment",
              "A journey does not have to begin every time you pass a gate. There is room here to rest and listen.",
            ],
          ],
          favor = this.data.favors.find((f) => f.npc === n.id),
          progress = favor ? this.favorProgress(favor) : 0,
          claimed = favor && p.estate.story.favors.includes(favor.id);
        html += this.panel(
          n.name,
          n.title || n.role || "Cultivator",
          `<div class="story-conversation">${this.portrait(n.id)}<div><p class="story-prose">${esc(d.topic < 0 ? this.changedStory(n) : topics[d.topic][1])}</p><div class="story-topics">${topics.map((t, i) => this.button("person-topic-" + i, esc(t[0]), d.topic === i ? "world-primary" : "world-secondary")).join("")}${this.button("person-journal", "Read our journal", "world-secondary")}</div>${favor ? `<aside class="story-favor"><b>${esc(favor.title)}</b><p>${esc(favor.description)} ${Math.min(progress, favor.target)}/${favor.target}</p>${this.button("favor-" + favor.id, claimed ? "Keepsake received" : progress >= favor.target ? "Share the news" : "We can talk when it is done", "world-secondary", claimed || progress < favor.target || busy)}</aside>` : ""}</div></div>`,
          "person-dialogue",
        );
        for (let i = 0; i < topics.length; i++)
          this.handlers.set("person-topic-" + i, () => (d.topic = i));
        this.handlers.set("person-journal", () => this.journal());
        if (favor)
          this.handlers.set("favor-" + favor.id, () =>
            this.hooks.act("story_favor", { id: favor.id }),
          );
      } else if (d?.kind === "journal") {
        const s = p.estate.story;
        html += this.panel(
          "The Journey Journal",
          "Choices, small discoveries and people worth returning to.",
          `<div class="journey-journal"><section><h2>Witnesses and choices</h2>${
            this.data.chapters
              .filter(
                (c) => s.seen.includes(c.id) || p.completed.includes(c.id),
              )
              .map(
                (c) =>
                  `<article><h3>${esc(c.title)}</h3><p>${esc(p.completed.includes(c.id) ? c.aftermath : c.reason)}</p><small>${esc(c.choices.find((v) => v.id === s.choices[c.id])?.response || "Your answer is still unwritten.")}</small>${this.button("journal-chapter-" + c.id, "Read the conversation")}</article>`,
              )
              .join("") ||
            "<p>The first witness is waiting at the ferry landing.</p>"
          }</section><section><h2>Details along the road · ${s.observations.length}/${this.data.observations.length}</h2>${
            this.data.observations
              .filter((o) => s.observations.includes(o.id))
              .map(
                (o) =>
                  `<article><h3>${esc(o.name)}</h3><p>${esc(o.text)}</p></article>`,
              )
              .join("") ||
            "<p>Look closely at flowers, water, lamps and old stones in the sanctuary.</p>"
          }<h2>Keepsakes</h2>${this.data.favors.map((f) => `<article class="${s.favors.includes(f.id) ? "" : "journal-unfinished"}"><h3>${esc(f.title)}</h3><p>${esc(s.favors.includes(f.id) ? f.keepsake : f.description)}</p></article>`).join("")}</section></div>`,
          "journal-dialogue",
        );
        for (const c of this.data.chapters)
          this.handlers.set("journal-chapter-" + c.id, () => this.open(c.id));
      }
      if (!d && this.notice && performance.now() < this.notice.until) {
        html += `<aside class="world-discovery"><small>NOTICED ALONG THE ROAD</small><h2>${esc(this.notice.name)}</h2><p>${esc(this.notice.text)}</p>${this.button("discovery-journal", "Keep reading in the journal")}${this.button("discovery-close", icon("close"), "discovery-close")}</aside>`;
        this.handlers.set("discovery-journal", () => this.journal());
        this.handlers.set("discovery-close", () => (this.notice = null));
      }
      this.root.innerHTML = html;
      if (d)
        for (const child of this.root.children)
          child.inert = !child.classList.contains("world-veil");
      if (d)
        this.root.querySelector(".world-panel")?.focus({ preventScroll: true });
      for (const canvas of this.root.querySelectorAll("[data-person]"))
        this.drawPortrait(canvas, canvas.dataset.person);
    }
    drawPortrait(canvas, id) {
      const side = this.art.npcs?.[id],
        base = this.hooks.hubAtlas.npcs?.[id],
        frame = side || base,
        image = side ? this.assets.explore_npcs : this.assets.hub_npcs;
      if (!frame || !image) return;
      const c = canvas.getContext("2d"),
        height = canvas.height - 12,
        width = (height * frame.w) / frame.h;
      c.clearRect(0, 0, canvas.width, canvas.height);
      c.drawImage(
        image,
        frame.x,
        frame.y,
        frame.w,
        frame.h,
        (canvas.width - width) / 2,
        8,
        width,
        height,
      );
    }
    cacheButtons() {
      this.dirty = false;
      const box = this.root.getBoundingClientRect();
      this.cached = [];
      for (const node of this.root.querySelectorAll("button[data-world-id]")) {
        if (this.dialog && !node.closest(".world-veil")) continue;
        const r = node.getBoundingClientRect();
        if (r.width && r.height)
          this.cached.push({
            node,
            id: node.dataset.worldId,
            rect: {
              x: ((r.left - box.left) / box.width) * 512,
              y: ((r.top - box.top) / box.height) * 288,
              w: (r.width / box.width) * 512,
              h: (r.height / box.height) * 288,
            },
          });
      }
    }
  }
  return Adventure;
})();
