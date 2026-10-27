#!/usr/bin/env python3
"""
Convert a POINTS-mode GLB (point cloud) into a small binary cloud for raylib.

Usage:
    python glb_to_cloud.py supernova_remnant.glb supernova_cloud.bin [num_points]

Output format (little endian):
    uint32  count
    count x { float x, y, z; uint8 r, g, b, a }      (16 bytes per point)

Positions are centred and scaled to fit a unit sphere, so the game's tween
scale is directly the blast radius.

Needs: numpy  (pip install numpy)
"""
import json
import struct
import sys

import numpy as np

COMPONENT = {
    5120: (np.int8, 1), 5121: (np.uint8, 1),
    5122: (np.int16, 2), 5123: (np.uint16, 2),
    5125: (np.uint32, 4), 5126: (np.float32, 4),
}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def read_glb(path):
    data = open(path, "rb").read()
    magic, _version, _length = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF":
        sys.exit("Not a binary glTF (.glb) file")
    off, doc, blob = 12, None, None
    while off < len(data):
        clen, ctype = struct.unpack_from("<II", data, off)
        off += 8
        chunk = data[off:off + clen]
        off += clen
        if ctype == 0x4E4F534A:      # 'JSON'
            doc = json.loads(chunk)
        elif ctype == 0x004E4942:    # 'BIN\0'
            blob = chunk
    if doc is None or blob is None:
        sys.exit("GLB is missing its JSON or BIN chunk")
    return doc, blob


def read_accessor(doc, blob, index):
    acc = doc["accessors"][index]
    view = doc["bufferViews"][acc["bufferView"]]
    dtype, size = COMPONENT[acc["componentType"]]
    n = NCOMP[acc["type"]]
    count = acc["count"]
    offset = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = view.get("byteStride", size * n)
    arr = np.ndarray(shape=(count, n), dtype=dtype, buffer=blob,
                     offset=offset, strides=(stride, size))
    arr = arr.astype(np.float32)
    if acc.get("normalized"):
        arr /= float(np.iinfo(dtype).max)
    return arr


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    target = int(sys.argv[3]) if len(sys.argv) > 3 else 4000

    doc, blob = read_glb(src)

    positions, colors = [], []
    for mesh in doc["meshes"]:
        for prim in mesh["primitives"]:
            if prim.get("mode", 4) != 0:        # 0 = POINTS
                continue
            attrs = prim["attributes"]
            pos = read_accessor(doc, blob, attrs["POSITION"])
            if "COLOR_0" in attrs:
                col = read_accessor(doc, blob, attrs["COLOR_0"])
                if col.shape[1] == 3:
                    col = np.hstack([col, np.ones((len(col), 1), np.float32)])
            else:
                col = np.ones((len(pos), 4), np.float32)
            positions.append(pos)
            colors.append(col)

    if not positions:
        sys.exit("No POINTS primitives found in this file")

    pos = np.vstack(positions)
    col = np.vstack(colors)
    print(f"Read {len(pos):,} points")

    # Near-black points are invisible under additive blending: drop them,
    # as long as enough points are left.
    bright = col[:, :3].max(axis=1)
    keep = bright > 0.04
    if keep.sum() >= target:
        pos, col = pos[keep], col[keep]
        print(f"Kept {len(pos):,} non-dark points")

    rng = np.random.default_rng(1234)
    if len(pos) > target:
        idx = rng.choice(len(pos), size=target, replace=False)
        pos, col = pos[idx], col[idx]

    # Centre on the bounding box and scale into the unit sphere.
    centre = (pos.min(axis=0) + pos.max(axis=0)) / 2.0
    pos = pos - centre
    radius = float(np.linalg.norm(pos, axis=1).max())
    pos = pos / max(radius, 1e-6)

    out = np.zeros(len(pos), dtype=[("p", "<f4", 3), ("c", "u1", 4)])
    out["p"] = pos
    out["c"] = np.clip(col * 255.0 + 0.5, 0, 255).astype(np.uint8)

    with open(dst, "wb") as f:
        f.write(struct.pack("<I", len(out)))
        f.write(out.tobytes())
    print(f"Wrote {len(out):,} points -> {dst} ({4 + out.nbytes:,} bytes)")


if __name__ == "__main__":
    main()
