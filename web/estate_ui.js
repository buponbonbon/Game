/* Sect estate presentation. All inventory changes use the Python economy API. */
window.VanDaoEstate = (() => {
  let tab = "Garden",
    plot = 0,
    crop = "qi_grass",
    recipe = "spirit_tea",
    page = 0,
    shop = "Seeds";
  const tabs = [
    "Garden",
    "Alchemy",
    "Merchant",
    "Commissions",
    "Achievements",
    "Research",
    "Ledger",
  ];
  function reward(r) {
    const parts = [];
    if (r.stones) parts.push(r.stones + " stones");
    if (r.insight) parts.push(r.insight + " Insight");
    if (r.fertilizer) parts.push(r.fertilizer + " fertilizer");
    if (r.seeds)
      parts.push(
        Object.entries(r.seeds)
          .map(([k, n]) => n + " " + k.replaceAll("_", " ") + " seed")
          .join(", "),
      );
    return parts.join(" / ");
  }
  function draw(v) {
    const {
      ctx,
      C,
      rect,
      text,
      wrapped,
      panel,
      button,
      bg,
      images,
      profile: p,
      data: d,
      act,
      busy,
      header,
      start,
      back,
      botany,
      now,
      enemies,
      sprite,
    } = v;
    bg("garden", 0.28);
    rect(0, 0, 512, 25, "#101d26");
    button("back", "<", 7, 5, 20, 15, back);
    text("SECT ESTATE", 36, 9, C.gold);
    text(
      `${p.stones} STONES / ${p.insight} INSIGHT`,
      496,
      10,
      C.gold,
      0.9,
      "right",
    );
    tabs.forEach((name, i) =>
      button(
        "estate-tab-" + name,
        { Commissions: "Missions", Achievements: "Goals" }[name] || name,
        8 + i * 71,
        32,
        67,
        21,
        () => {
          tab = name;
          page = 0;
        },
        { active: tab === name },
      ),
    );
    if (!d || !p.estate) {
      text("Opening the sect ledger...", 256, 130, C.jade, 1, "center");
      return;
    }
    const e = p.estate,
      b = e.bag,
      crops = Object.fromEntries(d.crops.map((c) => [c.id, c]));
    const btn = (id, label, x, y, w, h, action, args = {}, opt = {}) =>
      button(id, label, x, y, w, h, () => act(action, args), {
        ...opt,
        disabled: busy || opt.disabled,
      });
    const badge = (label, x, y, color = C.jade) =>
      text(label, x, y, color, 0.85);
    function plantIcon(id, stage, x, y, size = 34) {
      const a = botany?.[id]?.[stage];
      if (a && images.crops)
        ctx.drawImage(images.crops, a.x, a.y, a.w, a.h, x, y, size, size);
    }
    if (tab === "Garden") {
      if (e.cosmetics.active.includes("jade_chimes")) {
        for (let i = 0; i < 5; i++) {
          let x = 28 + i * 42,
            y = 58 + Math.sin(now / 700 + i) * 3;
          rect(x, y, 2, 12, C.jade);
          rect(x - 3, y + 11, 8, 2, C.gold);
        }
      }
      d.plots.forEach((a, i) => {
        const x = 9 + (i % 3) * 80,
          y = 80 + Math.floor(i / 3) * 50,
          locked = i >= e.garden.size;
        button("plot-" + i, "", x, y, 75, 46, () => (plot = i), {
          active: plot === i,
          disabled: locked,
          fill: "#493b2de8",
        });
        if (!locked) {
          rect(x + 5, y + 5, 65, 1, "#9f8155");
          for (let n = 0; n < 4; n++)
            rect(x + 5, y + 10 + n * 8, 65, 1, "#6d563d");
        }
        if (locked) {
          text("LOCKED", x + 37, y + 17, C.dim, 0.85, "center");
          return;
        }
        if (a.crop) {
          const stage = a.growth >= a.need ? 3 : a.growth === 0 ? 1 : 2;
          plantIcon(a.crop, stage, x + 1, y - 3, 36);
          badge(
            a.growth >= a.need ? "READY" : a.growth + "/" + a.need,
            x + 33,
            y + 10,
            a.growth >= a.need ? C.gold : C.cream,
          );
          badge(
            (a.watered ? "W " : "") + (a.fertilized ? "F" : ""),
            x + 35,
            y + 25,
            C.ice,
          );
        } else {
          text("EMPTY", x + 37, y + 17, C.muted, 0.85, "center");
        }
      });
      text("W watered / F fertilized", 12, 234, C.muted, 0.8);
      btn(
        "expand",
        "PLOTS " +
          e.garden.size +
          "/9" +
          (d.expand_cost ? " +3: " + d.expand_cost : ""),
        10,
        250,
        118,
        23,
        "expand",
        {},
        { disabled: !d.expand_cost || p.stones < d.expand_cost },
      );
      btn(
        "irrigation",
        "IRRIG. " +
          e.garden.irrigation +
          "/2" +
          (d.irrigation_cost ? " : " + d.irrigation_cost : ""),
        134,
        250,
        111,
        23,
        "irrigation",
        {},
        { disabled: !d.irrigation_cost || p.stones < d.irrigation_cost },
      );
      panel(253, 62, 250, 216, C.edge, "#122730ed");
      const a = d.plots[plot],
        selected = crops[a.crop || crop];
      text("PLOT " + (plot + 1) + " / " + selected.name, 263, 72, C.gold, 1.05);
      if (!a.crop) {
        d.crops.forEach((c, i) =>
          button(
            "seed-" + c.id,
            `${c.name}  x${b.seeds[c.id] || 0}`,
            263,
            94 + i * 25,
            230,
            22,
            () => (crop = c.id),
            { active: crop === c.id },
          ),
        );
        text(
          selected.growth +
            " completed battles / base yield " +
            selected.yield_amount,
          263,
          198,
          C.cream,
          0.9,
        );
        btn(
          "plant",
          "PLANT SEED",
          263,
          218,
          230,
          23,
          "plant",
          { plot, crop },
          { disabled: !b.seeds[crop] },
        );
        text(
          "Seeds: merchant, victories & Nursery Defense.",
          263,
          251,
          C.muted,
          0.8,
        );
      } else {
        plantIcon(
          a.crop,
          a.growth >= a.need ? 3 : a.growth ? 2 : 1,
          264,
          93,
          62,
        );
        text(
          `${a.growth}/${a.need} battles / yield ${a.yield}`,
          331,
          106,
          C.jade,
          0.95,
        );
        text(
          a.growth >= a.need
            ? "READY TO HARVEST"
            : "Growing after completed battles",
          331,
          125,
          a.growth >= a.need ? C.gold : C.muted,
          0.8,
        );
        btn(
          "harvest",
          "HARVEST",
          263,
          159,
          108,
          23,
          "harvest",
          { plot },
          { disabled: a.growth < a.need },
        );
        btn(
          "water",
          a.watered ? "WATERED" : "WATER +YIELD",
          379,
          159,
          114,
          23,
          "water",
          { plot },
          { disabled: a.watered },
        );
        btn(
          "fertilize",
          a.fertilized ? "FERTILIZED" : "FERTILIZE (" + b.fertilizer + ")",
          263,
          190,
          140,
          23,
          "fertilize",
          { plot },
          { disabled: a.fertilized || !b.fertilizer },
        );
        button(
          "clear-plot",
          "CLEAR",
          410,
          190,
          83,
          23,
          () => {
            if (
              window.confirm("Clear this crop? The planted seed will be lost.")
            )
              act("clear", { plot });
          },
          { disabled: busy },
        );
        wrapped(
          "No offline timer or withering. Victory grows crops; a loss counts after half the waves and 60 seconds.",
          263,
          226,
          230,
          C.muted,
          11,
          4,
        );
      }
      button(
        "nursery",
        "NURSERY DEFENSE",
        10,
        59,
        235,
        18,
        () => start("garden-defense"),
        { disabled: busy },
      );
    } else if (tab === "Alchemy") {
      panel(9, 63, 183, 213);
      panel(201, 63, 302, 213);
      d.recipes.forEach((r, i) =>
        button(
          "recipe-" + r.id,
          r.name + " x" + (b.pills[r.id] || 0),
          18,
          74 + i * 31,
          165,
          27,
          () => (recipe = r.id),
          { active: recipe === r.id },
        ),
      );
      const r = d.recipes.find((r) => r.id === recipe),
        known = e.blueprints.includes(r.id);
      text(r.name, 213, 75, C.gold, 1.2);
      wrapped(r.description, 213, 98, 278, C.cream, 13, 5);
      text("INGREDIENTS / IN BAG", 213, 162, C.jade, 0.9);
      Object.entries(r.ingredients).forEach(([id, n], i) =>
        text(
          `${n} ${crops[id].name} / ${b.produce[id] || 0}`,
          213,
          179 + i * 14,
          (b.produce[id] || 0) >= n ? C.cream : C.red,
          0.9,
        ),
      );
      text("Brewing fee: " + r.fee + " Spirit Stones", 213, 214, C.muted, 0.85);
      btn(
        "learn",
        known ? "FORMULA KNOWN" : "RESEARCH " + r.insight_cost + " INSIGHT",
        213,
        236,
        143,
        24,
        "learn_recipe",
        { recipe: r.id },
        { disabled: known || p.insight < r.insight_cost },
      );
      btn(
        "craft",
        "BREW 1",
        363,
        236,
        128,
        24,
        "craft",
        { recipe: r.id },
        {
          disabled:
            !known ||
            p.stones < r.fee ||
            Object.entries(r.ingredients).some(
              ([k, n]) => (b.produce[k] || 0) < n,
            ),
        },
      );
      text("ONE PREPARATION PER BATTLE", 18, 180, C.gold, 0.8);
      wrapped(
        "Selected: " +
          (d.recipes.find((r) => r.id === e.equipped)?.name || "None"),
        18,
        198,
        162,
        C.jade,
        12,
        2,
      );
      btn(
        "equip",
        e.equipped === r.id ? "EQUIPPED" : "EQUIP SELECTED",
        18,
        229,
        165,
        20,
        "equip",
        { item: r.id },
        { disabled: !b.pills[r.id] || e.equipped === r.id },
      );
      btn(
        "unequip",
        "CLEAR SLOT",
        18,
        253,
        165,
        17,
        "equip",
        { item: null },
        { disabled: !e.equipped },
      );
    } else if (tab === "Merchant") {
      ["Seeds", "Produce", "Decor"].forEach((name, i) =>
        button(
          "shop-" + name,
          name,
          12 + i * 162,
          62,
          156,
          21,
          () => (shop = name),
          { active: shop === name },
        ),
      );
      if (shop === "Decor") {
        d.decorations.forEach((a, i) => {
          const x = 10 + i * 166,
            owned = e.cosmetics.owned.includes(a.id);
          panel(x, 91, 160, 181);
          text(a.name, x + 8, 102, C.gold, 1);
          text(a.place + " / cosmetic", x + 8, 122, C.jade, 0.9);
          wrapped(a.description, x + 8, 146, 144, C.cream, 13, 5);
          btn(
            "decor-" + a.id,
            owned
              ? e.cosmetics.active.includes(a.id)
                ? "DISPLAYED"
                : "DISPLAY"
              : a.price + " STONES",
            x + 8,
            238,
            144,
            23,
            owned ? "decorate" : "buy",
            { item: owned ? a.id : "decor:" + a.id },
            { disabled: !owned && p.stones < a.price },
          );
        });
      } else {
        d.crops.forEach((c, i) => {
          const y = 94 + i * 36,
            n = (shop === "Seeds" ? b.seeds : b.produce)[c.id] || 0;
          panel(10, y, 490, 32);
          plantIcon(c.id, 3, 13, y - 3, 34);
          text(c.name + " x" + n, 52, y + 7, C.cream, 0.95);
          const buying = shop === "Seeds",
            cost = buying ? c.seed_price : c.sell_price;
          text(cost + " stones each", 239, y + 8, C.gold, 0.9);
          [1, 5].forEach((qty, j) =>
            btn(
              "trade-" + c.id + qty,
              (buying ? "BUY " : "SELL ") + qty,
              338 + j * 80,
              y + 5,
              74,
              23,
              buying ? "buy" : "sell",
              { item: (buying ? "seed:" : "produce:") + c.id, quantity: qty },
              { disabled: buying ? p.stones < cost * qty : n < qty },
            ),
          );
        });
        btn(
          "buy-fert",
          "FERTILIZER +1 YIELD / BUY 1 FOR " + d.fertilizer_price,
          12,
          247,
          306,
          25,
          "buy",
          { item: "fertilizer", quantity: 1 },
          { disabled: p.stones < d.fertilizer_price },
        );
        text("Fertilizer in bag: " + b.fertilizer, 333, 254, C.jade, 0.9);
      }
    } else if (tab === "Commissions") {
      d.contracts.forEach((c, i) => {
        const x = 10 + i * 166;
        panel(x, 66, 160, 173);
        text(c.name, x + 8, 77, C.gold, 0.98);
        wrapped(c.description, x + 8, 102, 144, C.cream, 13, 4);
        text(`${c.progress} / ${c.target}`, x + 8, 158, C.jade, 1.1);
        wrapped(reward(c.reward), x + 8, 179, 144, C.muted, 11, 3);
        btn(
          "commission-" + c.id,
          c.claimed ? "CLAIMED" : "CLAIM REWARD",
          x + 8,
          209,
          144,
          22,
          "contract_claim",
          { id: c.id },
          { disabled: c.claimed || c.progress < c.target },
        );
      });
      btn(
        "rotate",
        "TAKE THREE NEW COMMISSIONS",
        10,
        248,
        270,
        26,
        "contracts_rotate",
        {},
        { disabled: !d.contracts.every((c) => c.claimed) },
      );
      wrapped(
        "Claim all three to rotate. No daily timer.",
        293,
        249,
        206,
        C.muted,
        11,
        2,
      );
    } else if (tab === "Achievements") {
      const pages = Math.ceil(d.achievements.length / 4);
      page = Math.min(page, pages - 1);
      d.achievements.slice(page * 4, page * 4 + 4).forEach((a, i) => {
        const y = 65 + i * 45;
        panel(10, y, 490, 41);
        text(a.name, 19, y + 5, C.gold, 0.95);
        text(a.progress + "/" + a.target, 246, y + 5, C.jade, 0.9);
        text(a.description, 19, y + 20, C.cream, 0.85);
        wrapped(reward(a.reward), 295, y + 5, 110, C.muted, 10, 3);
        btn(
          "achievement-" + a.id,
          a.claimed ? "CLAIMED" : "CLAIM",
          415,
          y + 9,
          75,
          24,
          "achievement_claim",
          { id: a.id },
          { disabled: a.claimed || a.progress < a.target },
        );
      });
      button(
        "achievement-prev",
        "PREVIOUS",
        10,
        251,
        120,
        24,
        () => (page = Math.max(0, page - 1)),
        { disabled: page === 0 },
      );
      text(page + 1 + " / " + pages, 256, 257, C.muted, 1, "center");
      button(
        "achievement-next",
        "NEXT",
        380,
        251,
        120,
        24,
        () => (page = Math.min(pages - 1, page + 1)),
        { disabled: page === pages - 1 },
      );
    } else if (tab === "Ledger") {
      panel(10, 64, 490, 212);
      text("SECT LEDGER / RECENT ACTIVITY", 20, 74, C.gold, 1.1);
      const rows = [...(e.journal || [])].reverse(),
        pages = Math.max(1, Math.ceil(rows.length / 5));
      page = Math.min(page, pages - 1);
      rows.slice(page * 5, page * 5 + 5).forEach((r, i) => {
        const y = 97 + i * 28;
        wrapped(r.note, 20, y, 350, C.cream, 10, 2);
        text(
          (r.stones >= 0 ? "+" : "") + r.stones + " stones",
          487,
          y,
          C.gold,
          0.85,
          "right",
        );
        if (r.insight)
          text(
            (r.insight >= 0 ? "+" : "") + r.insight + " Insight",
            487,
            y + 12,
            C.jade,
            0.75,
            "right",
          );
      });
      if (!rows.length)
        wrapped(
          "Your harvests, purchases, crafting and battle outcomes will appear here. Nothing is sent to an online service.",
          20,
          106,
          465,
          C.muted,
          14,
          4,
        );
      button(
        "ledger-prev",
        "PREV",
        20,
        246,
        94,
        22,
        () => (page = Math.max(0, page - 1)),
        { disabled: !page },
      );
      text(page + 1 + " / " + pages, 256, 252, C.muted, 0.9, "center");
      button(
        "ledger-next",
        "NEXT",
        396,
        246,
        94,
        22,
        () => (page = Math.min(pages - 1, page + 1)),
        { disabled: page === pages - 1 },
      );
    } else if (tab === "Research") {
      const c = crops[crop],
        level = e.crop_research[crop] || 0;
      panel(10, 63, 235, 213);
      text("HERBAL STUDIES", 20, 74, C.gold, 1.1);
      d.crops.forEach((c, i) =>
        button(
          "study-" + c.id,
          c.name,
          20,
          96 + i * 27,
          215,
          24,
          () => (crop = c.id),
          { active: crop === c.id },
        ),
      );
      text(c.name + " / " + level + "/2", 20, 210, C.jade);
      text(
        level === 0
          ? "Next: +1 harvest yield"
          : level === 1
            ? "Next: -1 battle, return a seed"
            : "Mastered: yield, growth & seeds",
        20,
        230,
        C.cream,
        0.85,
      );
      btn(
        "research-crop",
        level === 2 ? "MASTERED" : "STUDY " + (level + 1) + " INSIGHT",
        20,
        248,
        215,
        22,
        "crop_research",
        { crop },
        { disabled: level === 2 || p.insight < level + 1 },
      );
      panel(253, 63, 250, 213);
      text("BESTIARY FIELD RESEARCH", 263, 74, C.gold, 1.1);
      const list = Object.values(enemies),
        pages = Math.ceil(list.length / 3);
      page = Math.min(page, pages - 1);
      list.slice(page * 3, page * 3 + 3).forEach((enemy, i) => {
        const a = d.research[enemy.id],
          y = 99 + i * 45;
        sprite(enemy.id, 260, y - 8, 0.85);
        text(enemy.name, 292, y, C.cream, 0.9);
        text(a.kills + " defeats", 490, y, C.muted, 0.85, "right");
        a.thresholds.forEach((n, j) =>
          btn(
            "monster-" + enemy.id + j,
            a.claimed.includes(j) ? "DONE" : n + " KILLS",
            292 + j * 67,
            y + 15,
            62,
            20,
            "monster_claim",
            { enemy: enemy.id, tier: j },
            { disabled: a.claimed.includes(j) || a.kills < n },
          ),
        );
      });
      button(
        "study-prev",
        "PREV",
        263,
        241,
        68,
        22,
        () => (page = Math.max(0, page - 1)),
        { disabled: page === 0 },
      );
      text(page + 1 + "/" + pages, 377, 247, C.muted, 0.9, "center");
      button(
        "study-next",
        "NEXT",
        424,
        241,
        68,
        22,
        () => (page = Math.min(pages - 1, page + 1)),
        { disabled: page === pages - 1 },
      );
    }
    if (busy) text("Saving sect ledger...", 256, 279, C.gold, 0.8, "center");
  }
  return {
    draw,
    reward,
    openResearch() {
      tab = "Research";
      page = 0;
    },
    get tab() {
      return tab;
    },
  };
})();
