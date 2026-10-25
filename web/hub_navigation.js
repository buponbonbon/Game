/* Shared sanctuary geometry, deterministic routes and collision-safe movement. */
(function (root) {
  function polygon(x, y, points) {
    let inside = false;
    for (let i = 0, j = points.length - 1; i < points.length; j = i++) {
      const [ax, ay] = points[i],
        [bx, by] = points[j];
      if (ay > y !== by > y && x < ((bx - ax) * (y - ay)) / (by - ay) + ax)
        inside = !inside;
    }
    return inside;
  }
  function walkable(map, x, y, r = 3) {
    if (
      !Number.isFinite(x) ||
      !Number.isFinite(y) ||
      x <= 5 ||
      x >= 507 ||
      y <= 74 ||
      y >= 251
    )
      return false;
    for (const [dx, dy] of [
      [0, 0],
      [r, 0],
      [-r, 0],
      [0, r],
      [0, -r],
    ])
      if (!map.walkways.some((p) => polygon(x + dx, y + dy, p))) return false;
    const f = map.fountain;
    if (((x - f.x) / (f.rx + r)) ** 2 + ((y - f.y) / (f.ry + r)) ** 2 < 1)
      return false;
    return !map.blockers.some(
      (b) =>
        x > b.x - r && x < b.x + b.w + r && y > b.y - r && y < b.y + b.h + r,
    );
  }
  class Navigation {
    constructor(map) {
      this.map = map;
      this.cell = map.cell || 8;
      this.nodes = new Map();
      for (let y = 4; y < 288; y += this.cell)
        for (let x = 4; x < 512; x += this.cell)
          if (walkable(map, x, y)) this.nodes.set(x + "," + y, { x, y });
    }
    nearest(x, y, maxDistance = Infinity) {
      let best = null,
        dist = maxDistance ** 2;
      for (const node of this.nodes.values()) {
        const d = (node.x - x) ** 2 + (node.y - y) ** 2;
        if (d < dist) {
          dist = d;
          best = node;
        }
      }
      return best;
    }
    clear(from, to) {
      const n = Math.max(
        1,
        Math.ceil(Math.hypot(to.x - from.x, to.y - from.y)),
      );
      for (let i = 1; i <= n; i++)
        if (
          !walkable(
            this.map,
            from.x + ((to.x - from.x) * i) / n,
            from.y + ((to.y - from.y) * i) / n,
          )
        )
          return false;
      return true;
    }
    route(from, to) {
      const start = this.nearest(from.x, from.y),
        goal = this.nearest(to.x, to.y, 40);
      if (!start || !goal) return [];
      const key = (p) => p.x + "," + p.y,
        s = key(start),
        g = key(goal),
        open = [s],
        cost = new Map([[s, 0]]),
        parent = new Map(),
        closed = new Set();
      while (open.length) {
        open.sort((a, b) => {
          const aa = this.nodes.get(a),
            bb = this.nodes.get(b);
          return (
            cost.get(a) +
            Math.abs(aa.x - goal.x) +
            Math.abs(aa.y - goal.y) -
            cost.get(b) -
            Math.abs(bb.x - goal.x) -
            Math.abs(bb.y - goal.y)
          );
        });
        const current = open.shift();
        if (current === g) {
          const result = [];
          let k = g;
          while (k !== s) {
            result.unshift(this.nodes.get(k));
            k = parent.get(k);
          }
          result.unshift(start);
          return result;
        }
        if (closed.has(current)) continue;
        closed.add(current);
        const p = this.nodes.get(current);
        for (const [dx, dy] of [
          [this.cell, 0],
          [-this.cell, 0],
          [0, this.cell],
          [0, -this.cell],
        ]) {
          const n = p.x + dx + "," + (p.y + dy);
          if (!this.nodes.has(n) || closed.has(n)) continue;
          // Check the edge as well as the nodes: no tunneling across narrow gaps.
          if (!this.clear(p, { x: p.x + dx, y: p.y + dy })) continue;
          const next = cost.get(current) + this.cell;
          if (!cost.has(n) || next < cost.get(n)) {
            cost.set(n, next);
            parent.set(n, current);
            open.push(n);
          }
        }
      }
      return [];
    }
    move(position, dx, dy) {
      let x = position.x,
        y = position.y;
      const count = Math.max(1, Math.ceil(Math.hypot(dx, dy) / 1.4));
      for (let i = 0; i < count; i++) {
        if (walkable(this.map, x + dx / count, y)) x += dx / count;
        if (walkable(this.map, x, y + dy / count)) y += dy / count;
      }
      return { x, y };
    }
  }
  root.VanDaoHubNavigation = { polygon, walkable, Navigation };
})(typeof window === "undefined" ? globalThis : window);
