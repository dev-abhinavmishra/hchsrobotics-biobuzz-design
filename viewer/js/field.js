// field.js — BIOBUZZ field context (inches, field center = origin, top of tiles = y0)
import * as THREE from 'three';
import { M } from './materials.js';
import * as P from './parts.js';

const sh = o => { o.traverse(m => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } }); return o; };

export function buildField() {
  const field = new THREE.Group();
  field.name = 'field';
  const refs = { hives: [], flowers: [], pickups: [] };
  const T = 144; // field size

  // ---- foam tiles: 6×6 of 24" ----
  const tileGeo = new THREE.BoxGeometry(23.8, 0.6, 23.8);
  for (let i = 0; i < 6; i++) for (let j = 0; j < 6; j++) {
    const t = new THREE.Mesh(tileGeo, (i + j) % 2 ? M.tile : M.tileAlt);
    t.position.set(-60 + i * 24, -0.3, -60 + j * 24);
    t.receiveShadow = true;
    field.add(t);
  }

  // ---- perimeter walls: aluminum frame + clear polycarbonate panels ----
  // kick rail + top cap in aluminum, clear panel between, posts every 24"
  const mkWall = (len) => {
    const w = new THREE.Group();
    const kick = new THREE.Mesh(new THREE.BoxGeometry(len, 3.0, 0.9), M.wallAlu);
    kick.position.y = 1.5;
    const panel = new THREE.Mesh(new THREE.BoxGeometry(len, 7.6, 0.3), M.wallPanel);
    panel.position.y = 6.9; panel.castShadow = false;
    const cap = new THREE.Mesh(new THREE.BoxGeometry(len, 1.1, 1.0), M.wallAlu);
    cap.position.y = 11.3;
    w.add(kick, panel, cap);
    const nPost = Math.round(len / 24);
    for (let i = 0; i <= nPost; i++) {
      const post = new THREE.Mesh(new THREE.BoxGeometry(0.9, 12.0, 0.9), M.wallAlu);
      post.position.set(-len / 2 + (i / nPost) * len, 6.0, 0);
      w.add(post);
    }
    sh(w);
    return w;
  };
  for (const [pos, ry] of [
    [[0, 0, -T / 2 - 0.6], 0], [[0, 0, T / 2 + 0.6], 0],
    [[-T / 2 - 0.6, 0, 0], Math.PI / 2], [[T / 2 + 0.6, 0, 0], Math.PI / 2],
  ]) {
    const w = mkWall(T + 2);
    w.position.set(...pos); w.rotation.y = ry;
    field.add(w);
  }
  // corner posts
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
    const cp = new THREE.Mesh(new THREE.BoxGeometry(1.6, 12.6, 1.6), M.hiveFrame);
    cp.position.set(sx * (T / 2 + 0.6), 6.3, sz * (T / 2 + 0.6));
    cp.castShadow = true;
    field.add(cp);
  }
  // wall AprilTags — inside faces, two per alliance end
  const wallTag = (x, z, ry, seed) => {
    const t = P.tagPlate(3.3, seed);
    t.position.set(x, 6.4, z); t.rotation.y = ry;
    field.add(t);
  };
  wallTag(-36, -T / 2 + 0.06, 0, 11);
  wallTag(36, -T / 2 + 0.06, 0, 23);
  wallTag(-36, T / 2 - 0.06, Math.PI, 37);
  wallTag(36, T / 2 - 0.06, Math.PI, 42);
  wallTag(-T / 2 + 0.06, 0, Math.PI / 2, 55);
  wallTag(T / 2 - 0.06, 0, -Math.PI / 2, 61);

  // ---- LOADING ZONE tape rectangles (alliance parking) ----
  for (const s of [-1, 1]) {
    const zone = new THREE.Mesh(new THREE.PlaneGeometry(44, 20), M.tapeWhite);
    zone.rotation.x = -Math.PI / 2;
    zone.position.set(s * 40, 0.02, 62);
    zone.receiveShadow = true;
    field.add(zone);
    // alliance-colored inner border
    const border = new THREE.Mesh(new THREE.PlaneGeometry(42.5, 18.5), s < 0 ? M.tapeRed : M.tapeBlue);
    border.rotation.x = -Math.PI / 2;
    border.position.set(s * 40, 0.025, 62);
    field.add(border);
    const inner = new THREE.Mesh(new THREE.PlaneGeometry(40.5, 16.5), M.tileAlt);
    inner.rotation.x = -Math.PI / 2;
    inner.position.set(s * 40, 0.03, 62);
    field.add(inner);
  }

  // center line + alliance approach tape in front of each hive cell
  const mkTape = (w, d, x, z, mat) => {
    const t = new THREE.Mesh(new THREE.PlaneGeometry(w, d), mat);
    t.rotation.x = -Math.PI / 2;
    t.position.set(x, 0.025, z);
    t.receiveShadow = true;
    field.add(t);
  };
  mkTape(138, 1.4, 0, 0, M.tapeWhite);
  mkTape(20, 2.2, -9, -32, M.tapeRed);    // red hive approach line
  mkTape(20, 2.2, 9, -32, M.tapeBlue);    // blue hive approach line
  for (const s of [-1, 1]) {              // loading-zone corner ticks
    mkTape(8, 1.4, s * 58, 44, M.tapeWhite);
    mkTape(1.4, 8, s * 62, 48, M.tapeWhite);
  }

  // ---- HIVE structure (center): frame + 2 bi-stable pivoting hives ----
  const hiveFrame = new THREE.Group();
  // outer gantry: posts at the Z extremes + top beam + floor rail
  for (const s of [-1, 1]) {
    const post = new THREE.Mesh(new THREE.BoxGeometry(1.6, 22, 1.6), M.hiveFrame);
    post.position.set(0, 11, s * 28); post.castShadow = true;
    hiveFrame.add(post);
  }
  const beam = new THREE.Mesh(new THREE.BoxGeometry(1.8, 1.8, 58), M.hiveFrame);
  beam.position.y = 21.5; beam.castShadow = true;
  hiveFrame.add(beam);
  const base = new THREE.Mesh(new THREE.BoxGeometry(6, 1.2, 58), M.hiveFrame);
  base.position.y = 0.6; base.castShadow = true;
  hiveFrame.add(base);
  // pivot axle beam along X at cell-axle height, on its own legs
  const axleBeam = new THREE.Mesh(new THREE.BoxGeometry(20, 1.2, 1.2), M.hiveFrame);
  axleBeam.position.set(0, 14, 0); axleBeam.castShadow = true;
  hiveFrame.add(axleBeam);
  // axle end caps
  for (const s of [-1, 1]) {
    const capEnd = new THREE.Mesh(new THREE.CylinderGeometry(0.8, 0.8, 0.5, 14).rotateZ(Math.PI / 2), M.darkSteel);
    capEnd.position.set(s * 10.2, 14, 0);
    hiveFrame.add(capEnd);
  }
  for (const s of [-1, 1]) {
    const leg = new THREE.Mesh(new THREE.BoxGeometry(1.2, 14, 1.2), M.hiveFrame);
    leg.position.set(s * 9.5, 7, 0); leg.castShadow = true;
    hiveFrame.add(leg);
  }
  field.add(hiveFrame);

  // each hive: pivot arm along Z rotating about the X axle beam, cells on ±Z arm ends.
  // cells ~16x12x22 in. with a ~14x20 in. top mouth (~508x356 mm opening, ~305 mm deep).
  // red hive at x=-9, blue at x=+9, pivot y=14
  const mkCell = (mat, seed) => {
    const c = new THREE.Group();
    const box = new THREE.Mesh(new THREE.BoxGeometry(16, 12, 22), mat);
    box.castShadow = true;
    c.add(box);
    // mesh screen insets on the ±X faces — real cells are screened, not solid
    for (const s of [-1, 1]) {
      const scr = new THREE.Mesh(new THREE.BoxGeometry(0.15, 9.4, 18.5), M.hiveScreen);
      scr.position.x = s * 8.06;
      c.add(scr);
      // screen frame rails
      for (const fz of [-9.6, 9.6]) {
        const fr = new THREE.Mesh(new THREE.BoxGeometry(0.3, 10.6, 0.9), M.hiveFrame);
        fr.position.set(s * 8.08, 0, fz);
        c.add(fr);
      }
      for (const fy of [-5.0, 5.0]) {
        const fr = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.9, 19.4), M.hiveFrame);
        fr.position.set(s * 8.08, fy, 0);
        c.add(fr);
      }
    }
    // open mouth + rolled rim
    const mouth = new THREE.Mesh(new THREE.BoxGeometry(14, 0.5, 20), M.holeDark);
    mouth.position.y = 6; c.add(mouth);
    const rimG = new THREE.BoxGeometry(15.6, 0.6, 1.1), rimG2 = new THREE.BoxGeometry(1.1, 0.6, 21.6);
    for (const [g2, px, pz] of [[rimG, 0, -10.55], [rimG, 0, 10.55], [rimG2, -7.75, 0], [rimG2, 7.75, 0]]) {
      const r = new THREE.Mesh(g2, M.hiveFrame);
      r.position.set(px, 6.2, pz); r.castShadow = true;
      c.add(r);
    }
    // AprilTag on the underside — textured card, faces down
    const tag = P.tagPlate(3.3, seed);
    tag.rotation.x = Math.PI / 2;
    tag.position.y = -6.1;
    c.add(tag);
    return c;
  };
  for (const [x, mat, name, seed] of [[-9, M.hiveRed, 'red', 101], [9, M.hiveBlue, 'blue', 202]]) {
    const pivot = new THREE.Group();
    pivot.position.set(x, 14, 0);
    const arm = new THREE.Mesh(new THREE.BoxGeometry(1.1, 1.1, 34), M.hiveFrame);
    arm.castShadow = true;
    pivot.add(arm);
    // pivot bearing blocks on the static axle beam
    for (const s of [-1, 1]) {
      const pb = new THREE.Mesh(new THREE.BoxGeometry(1.5, 1.5, 1.0), M.darkSteel);
      pb.position.set(x, 14, s * 0.9); pb.castShadow = true;
      hiveFrame.add(pb);
    }
    for (const s of [-1, 1]) {
      const cell = mkCell(mat, seed + s + 2);
      cell.position.set(0, 0, s * 15);
      pivot.add(cell);
      if (s < 0) {
        // three alliance NECTAR staged in the up-facing cell
        const nmat = name === 'red' ? M.nectarRed : M.nectarBlue;
        for (const [bx, bz] of [[-3, -3.5], [3, -3.5], [0, 4]]) {
          const nb = P.ball(1.8, nmat);
          nb.position.set(bx, -3.9, bz);
          cell.add(nb);
        }
      }
    }
    pivot.rotation.x = 0.12; // bi-stable resting tilt
    hiveFrame.add(pivot);
    refs.hives.push({ pivot, name });
  }

  // ---- FLOWERS ×4 on walls ----
  const mkFlower = () => {
    const f = new THREE.Group();
    const R = 3.4; // pipe square half-dist
    for (const [dx, dz] of [[-R, -R], [R, -R], [-R, R], [R, R]]) {
      const pipe = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 22, 14), M.flowerPipe);
      pipe.position.set(dx, 11, dz); pipe.castShadow = true;
      f.add(pipe);
      // segment collars where pipe sections join
      for (const cy of [4.2, 13.0, 21.5]) {
        const col = new THREE.Mesh(new THREE.CylinderGeometry(0.58, 0.58, 0.5, 14), M.hiveFrame);
        col.position.set(dx, cy, dz);
        f.add(col);
      }
    }
    // molded rings: bottom (holding), middle (pollen passes), top mouth ~4 in. dia at ~21.5 in.
    const ringGeo = (() => {
      const s = new THREE.Shape();
      s.absarc(0, 0, 4.8, 0, Math.PI * 2);
      const h = new THREE.Path(); h.absarc(0, 0, 2.0, 0, Math.PI * 2, true); s.holes.push(h);
      return new THREE.ExtrudeGeometry(s, { depth: 0.7, bevelEnabled: false }).rotateX(-Math.PI / 2);
    })();
    for (const y of [4.2, 13.0, 21.5]) {
      const r = new THREE.Mesh(ringGeo, M.flowerRing);
      r.position.y = y; r.castShadow = true;
      f.add(r);
    }
    // flower throat — dark tube inside the mouth so it reads as an opening
    const throat = new THREE.Mesh(new THREE.CylinderGeometry(1.98, 1.98, 3.4, 20, 1, true), M.holeDark);
    throat.position.y = 20.4;
    f.add(throat);
    // petal collar — 6 upturned petals around the top ring
    const petalGeo = new THREE.SphereGeometry(1.9, 12, 8);
    petalGeo.scale(1.15, 0.22, 0.75);
    for (let i = 0; i < 6; i++) {
      const a = (i / 6) * Math.PI * 2;
      const petal = new THREE.Mesh(petalGeo, M.flowerRing);
      petal.position.set(Math.cos(a) * 4.1, 22.4, Math.sin(a) * 4.1);
      petal.rotation.y = -a;
      petal.rotation.x = -0.38; // tips curl up
      petal.castShadow = true;
      f.add(petal);
    }
    // leaf pairs on the pipes
    const leafGeo = new THREE.SphereGeometry(1.5, 10, 8);
    leafGeo.scale(1.35, 0.14, 0.6);
    for (const [px, py, pz, ry] of [[-R - 0.7, 8.5, 0, 0.5], [R + 0.7, 9.5, 0, -0.4],
      [0, 15.5, -R - 0.7, Math.PI / 2 + 0.4], [0, 16.5, R + 0.7, Math.PI / 2 - 0.5]]) {
      const leaf = new THREE.Mesh(leafGeo, M.flowerLeaf);
      leaf.position.set(px, py, pz); leaf.rotation.y = ry; leaf.rotation.z = 0.3;
      leaf.castShadow = true;
      f.add(leaf);
    }
    // base block
    const pot = new THREE.Mesh(new THREE.BoxGeometry(8.6, 1.6, 8.6), M.hiveFrame);
    pot.position.y = 0.8; pot.castShadow = pot.receiveShadow = true;
    f.add(pot);
    // top backstop scoop
    const scoop = new THREE.Mesh(new THREE.BoxGeometry(9.8, 3.0, 0.5), M.flowerRing);
    scoop.position.set(0, 24.4, -4.6); scoop.castShadow = true;
    f.add(scoop);
    // staged pollen in bottom ring — four per FLOWER
    for (let i = 0; i < 4; i++) {
      const b = P.ball(1.4, M.pollen);
      b.position.set((i % 2 ? 1.45 : -1.45), 5.3, (i < 2 ? -1.45 : 1.45));
      f.add(b);
    }
    return f;
  };
  for (const [x, z, ry] of [[-64, -64, 0], [64, -64, 0], [-64, 64, 0], [64, 64, 0]]) {
    const fl = mkFlower();
    fl.position.set(x, 0, z);
    fl.rotation.y = ry;
    field.add(fl);
    refs.flowers.push(fl);
  }

  // ---- staged scoring elements ----
  // floor pollen: 2 sets of 4
  for (const [cx, cz] of [[-30, 20], [30, -20]]) {
    for (let i = 0; i < 4; i++) {
      const b = P.ball(1.4, M.pollen);
      b.position.set(cx + (i % 2) * 3.2, 1.4, cz + Math.floor(i / 2) * 3.2);
      field.add(b);
      refs.pickups.push(b);
    }
  }
  // nectar in alliance areas + up cells
  for (const s of [-1, 1]) {
    for (let i = 0; i < 5; i++) {
      const b = P.ball(1.8, s < 0 ? M.nectarRed : M.nectarBlue);
      b.position.set(s * (52 + (i % 3) * 3.8), 1.8, -30 + Math.floor(i / 3) * 4);
      field.add(b);
      refs.pickups.push(b);
    }
  }

  refs.upCellRed = v3(-9, 21.7, -14.2);   // approx up-facing red cell mouth
  refs.upCellBlue = v3(9, 21.7, -14.2);
  return { field, refs };
}

function v3(x, y, z) { return new THREE.Vector3(x, y, z); }
