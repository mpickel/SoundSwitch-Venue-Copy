#!/usr/bin/env python3
"""ssvenues - copy everything between SoundSwitch venues that SoundSwitch's own "+" button leaves behind.

When you duplicate a venue in SoundSwitch only the fixtures are copied. Static looks, position
presets and attribute cues stay empty and every fixture is reset to "Wash (Primary)" without groups.
This tool reads SoundSwitchVenues.bin (SoundSwitch 2.11, reverse engineered, see docs/file-format.md)
and copies that data from one venue to another.

Usage (the project file is found automatically in ~/Music/SoundSwitch/<project>.ssproj/):
  python3 ssvenues.py info                                  list venues, looks and cues
  python3 ssvenues.py fixtures "<venue>"                    list fixtures with type and groups
  python3 ssvenues.py copy "<source>" "<target>" [--write]  copy looks, positions, cues, type and groups
  python3 ssvenues.py flags "<source>" "<target>" [--write] copy only fixture type and groups
  python3 ssvenues.py set "<venue>" "<cue>" "<device>" "Attribute=Value" ... [--write]

Nothing is written without --write. Every write creates a timestamped .bak backup first.
Add --file <path> if the project file is not found automatically. Close SoundSwitch before writing.

File layout (all numbers little-endian u32, strings = u32 length incl. NUL + UTF-16LE):
  header      : magic aaaa0955, u32 3, u32 offA, u32 offB, u32 ?, u32 venue_count
  venues      : venue_count blocks, each 04000000 + GUID + 01000000 + name ...
  positions   : 02000000 00000000, then objects:
                02000000, nsub, nsub x sub(GUID, 02000000, n, n x (u32 idx, u32 1, 8 bytes)),
                01000000, name, GUID, u32 colour, u32 a
                followed by the order list (u32 n, n x u32) and 14 opaque bytes
  looklists   : u32 count; count x (GUID, 01000000, 20000000, 32 slots)   -> static looks 1-32
  attrcues    : 02000000 00000000, then objects:
                01000000, nven, nven x (GUID, 01000000, 01000000, n, n x 16 bytes), 01000000, name, GUID, colour, a
                followed by the order list and opaque cue groups
  bank2       : u32 count; count x (GUID, 02000000, 96 slots "33".."128", 128 x 25 bytes)
  fixture rec : ends with profile GUID + 6 u32: hash, mode, DMX address-1, profile hash, type, groups
                type: 2 Wash (Primary), 3 Wash (Secondary), 4 Wash (Tertiary), 11 Multi Cell (Primary),
                12 Multi Cell (Secondary), other values unknown; groups: Group1..4 (0 = none)
  tail        : 46 bytes (offA points here), table (offset, len, 0, 1) per fixture record,
                ffffffff, u32 7, "Default"

Slot = 05000000 01000000 name, 5 lists: A idx+double (12), B idx+8 (12), C idx+8 (12),
       D idx+GUID (20, position preset), E 16 bytes (attribute values)
"""
__version__ = "1.0.0"

import argparse
import glob
import datetime
import os
import re
import shutil
import struct
import subprocess
import sys

MAGIC = b"\xaa\xaa\x09\x55"


class P:
    """Small cursor over bytes."""

    def __init__(self, b, o=0):
        self.b, self.o = b, o

    def u32(self):
        v = struct.unpack_from("<I", self.b, self.o)[0]
        self.o += 4
        return v

    def raw(self, n):
        v = self.b[self.o : self.o + n]
        self.o += n
        return v

    def guid(self):
        return self.raw(16)

    def str(self):
        n = self.u32()
        s = self.b[self.o : self.o + 2 * n - 2].decode("utf-16le")
        self.o += 2 * n
        return s

    def expect(self, v, what):
        got = self.u32()
        if got != v:
            raise ValueError(f"{what}: expected {v:#x} got {got:#x} at {self.o-4:#x}")


def find_venues(b):
    out = []
    for m in re.finditer(rb"\x04\x00\x00\x00(.{16})\x01\x00\x00\x00(.{4})", b, re.S):
        n = struct.unpack("<I", m.group(2))[0]
        if not (2 <= n <= 60):
            continue
        end = m.end() + 2 * n
        if b[end - 2 : end + 4] != b"\x00\x00\x0f\x00\x00\x00":
            continue
        try:
            t = b[m.end() : end - 2].decode("utf-16le")
        except UnicodeDecodeError:
            continue
        out.append({"off": m.start(), "name": t, "guid": m.group(1)})
    return out


def parse_positions(p):
    b = p.b
    objs = []
    while True:
        start = p.o
        if p.u32() != 2:  # every object starts with 02000000
            p.o = start
            break
        nsub = p.u32()
        subs = []
        ok = True
        for _ in range(nsub):
            s0 = p.o
            g = p.guid()
            if p.u32() != 2:
                ok = False
                break
            n = p.u32()
            for _ in range(n):
                p.u32()
                if p.u32() != 1:
                    ok = False
                    break
                p.raw(8)
            if not ok:
                break
            subs.append({"key": g, "n": n, "raw": b[s0 : p.o]})
        if not ok or p.u32() != 1:
            p.o = start
            break
        tail_start = p.o - 4  # ab 01000000 Name ...
        name = p.str()
        g = p.guid()
        colour, a = p.u32(), p.u32()
        objs.append({"name": name, "guid": g, "subs": subs, "colour": colour, "a": a,
                     "off": start, "tail": b[tail_start : p.o], "end": p.o})
    n = p.u32()
    order = [p.u32() for _ in range(n)]
    return objs, order


def parse_slot(p):
    s0 = p.o
    p.expect(5, "slot tag")
    p.expect(1, "slot tag2")
    name = p.str()
    head = p.b[s0 : p.o]
    lists = []
    # A: idx+double (intensity), B: idx+8B, C: idx+8B (colour), D: idx+GUID (position preset), E: 16B (attributes)
    for width in (12, 12, 12, 20, 16):
        n = p.u32()
        if n > 10000:
            raise ValueError(f"slot {name!r}: implausible list count {n:#x} at {p.o-4:#x}")
        lists.append([p.raw(width) for _ in range(n)])
    return {"name": name, "head": head, "lists": lists}


def parse_looklists(p):
    b = p.b
    count = p.u32()
    out = []
    for _ in range(count):
        g = p.guid()
        p.expect(1, "ll tag")
        p.expect(32, "ll nslots")
        s0 = p.o
        slots = [parse_slot(p) for _ in range(32)]
        out.append({"key": g, "slots": slots, "raw": b[s0 : p.o]})
    return out


def parse_attrcues(p):
    b = p.b
    p.expect(2, "ac hdr")
    p.expect(0, "ac hdr2")
    objs = []
    while True:
        start = p.o
        if p.u32() != 1:
            p.o = start
            break
        nven = p.u32()
        if nven > 1000:
            p.o = start
            break
        subs = []
        for _ in range(nven):
            s0 = p.o
            g = p.guid()
            p.expect(1, "ac sub1")
            p.expect(1, "ac sub2")
            n = p.u32()
            p.raw(16 * n)
            subs.append({"key": g, "n": n, "raw": b[s0 : p.o]})
        p.expect(1, "ac name tag")
        tail_start = p.o - 4
        name = p.str()
        g = p.guid()
        colour, a = p.u32(), p.u32()
        objs.append({"name": name, "guid": g, "subs": subs, "colour": colour, "a": a,
                     "off": start, "tail": b[tail_start : p.o], "end": p.o})
    n = p.u32()
    order = [p.u32() for _ in range(n)]
    return objs, order


def parse_bank2(p):
    count = p.u32()
    out = []
    for _ in range(count):
        g = p.guid()
        p.expect(2, "b2 tag")
        slots = []
        while p.b[p.o : p.o + 8] == b"\x05\x00\x00\x00\x01\x00\x00\x00":
            slots.append(parse_slot(p))
        t6 = []
        while p.b[p.o : p.o + 4] == b"\x06\x00\x00\x00":
            t6.append(p.raw(25))
        if len(t6) != 128:
            raise ValueError(f"bank2 key {g.hex()}: {len(t6)} type-6 records at {p.o:#x}")
        out.append({"key": g, "slots": slots, "t6": t6})
    return out


def parse_tail(b, start):
    end = len(b)
    n = struct.unpack_from("<I", b, end - 11)[0]
    assert n == 7 and b[end - 7 :] == b"Default", "unexpected file tail"
    tbl_end = end - 11
    assert b[tbl_end - 4 : tbl_end] == b"\xff\xff\xff\xff", "missing ffffffff terminator"
    tbl_end -= 4
    o = tbl_end
    recs = []
    while o - 16 >= start:
        a, l, z, one = struct.unpack_from("<IIII", b, o - 16)
        if one != 1 or z != 0 or a >= len(b):
            break
        recs.append((a, l))
        o -= 16
    recs.reverse()
    return {"pre": b[start:o], "tbl_start": o, "recs": recs, "tbl_end": tbl_end}


def parse(b):
    assert b[:4] == MAGIC, "not a SoundSwitchVenues.bin (magic number missing)"
    hdr = dict(zip(("ver", "offA", "offB", "x", "nven"), struct.unpack_from("<IIIII", b, 4)))
    vens = find_venues(b)
    assert len(vens) == hdr["nven"], f"header says {hdr['nven']} venues, found {len(vens)}"
    last = vens[-1]["off"]
    pos_start = b.find(b"\x02\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00", last)
    p = P(b, pos_start + 8)
    objs, order = parse_positions(p)
    gap = p.raw(14)
    ll_start = p.o
    looklists = parse_looklists(p)
    ll_end = p.o
    ac_objs, ac_order = parse_attrcues(p)
    ac_end = p.o
    pat = struct.pack("<I", len(looklists))
    q = p.o
    while True:
        q = b.find(pat, q)
        if q < 0:
            raise ValueError("bank2 start not found")
        if b[q + 20 : q + 32] == b"\x02\x00\x00\x00\x05\x00\x00\x00\x01\x00\x00\x00":
            break
        q += 1
    gap2 = p.raw(q - p.o)
    b2_start = p.o
    bank2 = parse_bank2(p)
    tail = parse_tail(b, p.o)
    assert hdr["offA"] == p.o, f"offA {hdr['offA']:#x} != tail start {p.o:#x}"
    assert hdr["offB"] == p.o + 30
    return {"hdr": hdr, "venues": vens, "pos_start": pos_start, "positions": objs, "order": order, "gap": gap,
            "ll_start": ll_start, "looklists": looklists, "ll_end": ll_end,
            "attrcues": ac_objs, "ac_order": ac_order, "ac_end": ac_end, "gap2": gap2,
            "b2_start": b2_start, "bank2": bank2, "b2_end": p.o, "tail": tail}


# ---------------------------------------------------------------- Output

def info(b, r):
    names = {v["guid"]: v["name"] for v in r["venues"]}
    print(f"File: {len(b)} bytes, {r['hdr']['nven']} venues")
    for v in r["venues"]:
        print(f"  Venue {v['name']!r}")
    print(f"\nPosition presets ({len(r['positions'])}):")
    for o in r["positions"]:
        keys = [names[s["key"]] for s in o["subs"] if s["key"] in names]
        print(f"  {o['name']!r:22} Venues: {keys}")
    print("\nStatic looks (slots 1-32) per venue:")
    for ll in r["looklists"]:
        nm = names.get(ll["key"])
        if nm:
            named = [s["name"] for s in ll["slots"] if not s["name"].isdigit()]
            print(f"  {nm!r:20} {len(named):2} used: {named}")
    print(f"\nAttribute cues ({len(r['attrcues'])}):")
    for o in r["attrcues"]:
        vs = {names[s["key"]]: s["n"] for s in o["subs"] if s["key"] in names}
        print(f"  {o['name']!r:26} Entries per venue: {vs}")
    b2 = {names[x["key"]]: sum(1 for s in x["slots"] if not s["name"].isdigit()) for x in r["bank2"] if x["key"] in names}
    print(f"\nLooks in slots 33-128 used: {b2}")


# ---------------------------------------------------------------- Device tree

NODE = re.compile(rb"\x03\x00\x00\x00\x02\x00\x00\x00(.{4})\x01\x00\x00\x00(.{4})", re.S)


def venue_bounds(r):
    vens = r["venues"]
    ends = [v["off"] for v in vens[1:]] + [r["pos_start"]]
    return {v["guid"]: (v["off"], e) for v, e in zip(vens, ends)}


def tree_nodes(b, lo, hi):
    """Nodes of a venue's device tree in file order: (node id, name, look number).
    Node: 03000000 02000000 <id> 01000000 <name>; devices/cells continue with <look-nr> <colour> ...;
    group nodes have no look number (None)."""
    out = []
    for m in NODE.finditer(b, lo, hi):
        n = struct.unpack("<I", m.group(2))[0]
        if not (1 <= n <= 80):
            continue
        try:
            t = b[m.end() : m.end() + 2 * n - 2].decode("utf-16le")
        except UnicodeDecodeError:
            continue
        if not t.isprintable():
            continue
        lid, colour = struct.unpack_from("<II", b, m.end() + 2 * n)
        out.append((struct.unpack("<I", m.group(1))[0], t, lid if colour >> 24 == 0xFF else None))
    return out


def tree_range(r, g):
    """Byte range of a venue's device tree: behind the fixture records (device profiles with similar-looking channel entries come before)."""
    lo, hi = venue_bounds(r)[g]
    ends = [a + l for a, l in r["tail"]["recs"] if lo <= a < hi]
    return (max(ends) if ends else lo), hi


ATTR = re.compile(rb"\x02\x00\x00\x00(.{4})\x01\x00\x00\x00(.{4})", re.S)


def profile_attributes(b, r, g, profile):
    """Attributes (name -> SoundSwitch number) of a device profile in the venue, read from the profile name up to 'Main'."""
    lo, _ = venue_bounds(r)[g]
    hi, _ = tree_range(r, g)
    start = b.find(profile.encode("utf-16le") + b"\x00\x00", lo, hi)
    if start < 0:
        raise ValueError(f"Profile {profile!r} not found in the venue; use the attribute number instead of its name, "
                         f"e.g. 8=160")
    end = b.find("Main".encode("utf-16le") + b"\x00\x00", start, hi)
    out = {}
    for m in ATTR.finditer(b, start, end if end > 0 else hi):
        n = struct.unpack("<I", m.group(2))[0]
        if not (2 <= n <= 60):
            continue
        try:
            t = b[m.end() : m.end() + 2 * n - 2].decode("utf-16le")
        except UnicodeDecodeError:
            continue
        if t.isprintable():
            out.setdefault(t, struct.unpack("<I", m.group(1))[0])
    return out


def align(a, c):
    """Longest common subsequence of the names of two node lists; returns index pairs (i, j)."""
    n, m = len(a), len(c)
    L = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            L[i][j] = L[i + 1][j + 1] + 1 if a[i][1] == c[j][1] else max(L[i + 1][j], L[i][j + 1])
    pairs, i, j = [], 0, 0
    while i < n and j < m:
        if a[i][1] == c[j][1]:
            pairs.append((i, j))
            i, j = i + 1, j + 1
        elif L[i + 1][j] >= L[i][j + 1]:
            i += 1
        else:
            j += 1
    return pairs


def node_mapping(b, r, src, dst):
    """Map nodes of the source venue to those of the target venue (names in tree order; devices that only
    exist in one venue stay unmapped). Returns (node id map, look number map, log)."""
    a = tree_nodes(b, *tree_range(r, src["guid"]))
    c = tree_nodes(b, *tree_range(r, dst["guid"]))
    pairs = align(a, c)
    m, lm, bad = {}, {}, set()
    for i, j in pairs:
        if m.get(a[i][0], c[j][0]) != c[j][0]:
            bad.add(a[i][0])
        m[a[i][0]] = c[j][0]
        if a[i][2] is not None and c[j][2] is not None:
            lm[a[i][2]] = c[j][2]
    for i in bad:
        del m[i]
    log = []
    only_src = [a[i][1] for i in set(range(len(a))) - {i for i, _ in pairs} if a[i][2] is not None]
    only_dst = [c[j][1] for j in set(range(len(c))) - {j for _, j in pairs} if c[j][2] is not None]
    log.append(f"Device tree: matched {len(pairs)} of {len(a)} nodes")
    leaves = sum(1 for n in c if n[2] is not None)
    matched = sum(1 for _, j in pairs if c[j][2] is not None)
    if leaves and matched * 2 < leaves:
        log.append(f"WARNING: only {matched} of {leaves} devices in {dst['name']!r} have a counterpart in "
                   f"{src['name']!r}. Device names differ between the venues (renamed or re-added fixtures?). "
                   "Most looks and cues will not be copied. Check the names in SoundSwitch first.")
    if only_src:
        log.append(f"  only in {src['name']!r} (their values are skipped): {sorted(set(only_src))}")
    if only_dst:
        log.append(f"  only in {dst['name']!r} (they get no values): {sorted(set(only_dst))}")
    return m, lm, log


# ---------------------------------------------------------------- Fixture records (type, groups)

TYPE_NAMES = {2: "Wash (Primary)", 3: "Wash (Secondary)", 4: "Wash (Tertiary)",
              11: "Multi Cell (Primary)", 12: "Multi Cell (Secondary)"}


def fixture_records(b, r, g):
    """Top-level fixture records of a venue. Per record: key (profile GUID, mode, DMX-1), type, groups
    and the file offsets of type and groups (the last two u32 of the record)."""
    lo, hi = venue_bounds(r)[g]
    recs = [(a, l) for a, l in r["tail"]["recs"] if lo <= a < hi]
    out = []
    for a, l in recs:
        if any(x < a < x + y for x, y in recs):  # skip sub-records (cells)
            continue
        end = a + l
        guid = b[end - 40 : end - 24]
        _, mode, dmx, _, typ, grp = struct.unpack_from("<6I", b, end - 24)
        out.append({"key": (guid, mode, dmx), "dmx": dmx + 1, "type": typ, "groups": grp,
                    "off_type": end - 8, "off_groups": end - 4})
    return out


def fixtures(b, r, venue):
    recs = fixture_records(b, r, venue["guid"])
    print(f"Fixtures in {venue['name']!r} ({len(recs)}):")
    for f in sorted(recs, key=lambda f: f["dmx"]):
        tn = TYPE_NAMES.get(f["type"], f"Type {f['type']}")
        print(f"  DMX {f['dmx']:3d}  profile {f['key'][0][3:7].hex()}  mode {f['key'][1]}  {tn:24} groups {f['groups']}")


def copy_fixture_flags(b, r, src, dst):
    """Copy type (Wash/Multi Cell ...) and group assignment per fixture from src to dst.
    Fixtures are matched by profile GUID, mode and DMX address. Returns (new bytes, log)."""
    out = bytearray(b)
    srcs = {}
    for f in fixture_records(b, r, src["guid"]):
        srcs.setdefault(f["key"], []).append(f)
    log, changed, missing = [], 0, []
    for f in fixture_records(b, r, dst["guid"]):
        cands = srcs.get(f["key"])
        if not cands:
            missing.append(f["dmx"])
            continue
        sf = cands.pop(0)
        if (sf["type"], sf["groups"]) != (f["type"], f["groups"]):
            struct.pack_into("<II", out, f["off_type"], sf["type"], sf["groups"])
            changed += 1
    log.append(f"Fixture type and groups: {changed} fixtures updated"
               + (f" (no counterpart in source, DMX: {missing})" if missing else ""))
    return bytes(out), log


# ---------------------------------------------------------------- Copying

def remap_cue_sub(raw, newkey, m):
    """Attribute cue entry: GUID, 01, 01, n, n x (u32 1, u32 node, u32 attribute, u32 value)."""
    n = struct.unpack_from("<I", raw, 24)[0]
    ents, dropped = [], []
    for k in range(n):
        e = raw[28 + 16 * k : 44 + 16 * k]
        node = struct.unpack_from("<I", e, 4)[0]
        if node in m:
            ents.append(e[:4] + struct.pack("<I", m[node]) + e[8:])
        else:
            dropped.append(node)
    return newkey + raw[16:24] + struct.pack("<I", len(ents)) + b"".join(ents), len(ents), dropped


def remap_slot(slot, m, lm):
    """Look slot: lists A-D (look number + value) refer to devices by look number,
    list E (1, node, attribute, value) refers to them by node id, like the attribute cues."""
    out = slot["head"]
    dropped = set()
    for li, lst in enumerate(slot["lists"]):
        mp, at = (m, 4) if li == 4 else (lm, 0)
        ents = []
        for e in lst:
            k = struct.unpack_from("<I", e, at)[0]
            if k in mp:
                ents.append(e[:at] + struct.pack("<I", mp[k]) + e[at + 4 :])
            else:
                dropped.add(k)
        out += struct.pack("<I", len(ents)) + b"".join(ents)
    return out, dropped


def remap_pos_sub(raw, newkey, m):
    """Position entry: GUID, 02, n, n x (u32 node, u32 1, 8 bytes)."""
    n = struct.unpack_from("<I", raw, 20)[0]
    ents, dropped = [], []
    for k in range(n):
        e = raw[24 + 16 * k : 40 + 16 * k]
        node = struct.unpack_from("<I", e, 0)[0]
        if node in m:
            ents.append(struct.pack("<I", m[node]) + e[4:])
        else:
            dropped.append(node)
    return newkey + raw[16:20] + struct.pack("<I", len(ents)) + b"".join(ents), len(ents), dropped


def build_copy(b, r, src, dst):
    """Build new file bytes in which all look data of venue src also exists for venue dst."""
    sg, dg = src["guid"], dst["guid"]
    m, lm, log = node_mapping(b, r, src, dst)
    b, flog = copy_fixture_flags(b, r, src, dst)  # same length, offsets stay valid
    log += flog

    def fmt_drop(d):
        return f" (ignored orphaned references in source: {sorted(set(d))})" if d else ""

    # positions
    pos = bytearray()
    for o in r["positions"]:
        subs = [s for s in o["subs"] if s["key"] != dg]
        srcsub = next((s for s in o["subs"] if s["key"] == sg), None)
        if srcsub:
            raw, n, d = remap_pos_sub(srcsub["raw"], dg, m)
            subs.append({"raw": raw})
            log.append(f"Position {o['name']!r}: copied {n} values{fmt_drop(d)}")
        pos += b"\x02\x00\x00\x00" + struct.pack("<I", len(subs))
        for s in subs:
            pos += s["raw"]
        pos += o["tail"]
    pos += struct.pack("<I", len(r["order"])) + b"".join(struct.pack("<I", x) for x in r["order"])

    # looklists
    ll = struct.pack("<I", len(r["looklists"]))
    srcll = next(x for x in r["looklists"] if x["key"] == sg)
    newraw, named = b"", []
    for s in srcll["slots"]:
        raw, d = remap_slot(s, m, lm)
        newraw += raw
        if not s["name"].isdigit():
            named.append(s["name"])
    for x in r["looklists"]:
        raw = newraw if x["key"] == dg else x["raw"]
        ll += x["key"] + b"\x01\x00\x00\x00\x20\x00\x00\x00" + raw
    log.append(f"Static looks: copied {len(named)} slots: {named}")

    # attrcues
    ac = b"\x02\x00\x00\x00\x00\x00\x00\x00"
    for o in r["attrcues"]:
        subs = [s for s in o["subs"] if s["key"] != dg]
        srcsub = next((s for s in o["subs"] if s["key"] == sg), None)
        if srcsub:
            raw, n, d = remap_cue_sub(srcsub["raw"], dg, m)
            subs.append({"raw": raw})
            log.append(f"Attribute cue {o['name']!r}: copied {n} values{fmt_drop(d)}")
        ac += b"\x01\x00\x00\x00" + struct.pack("<I", len(subs))
        for s in subs:
            ac += s["raw"]
        ac += o["tail"]
    ac += struct.pack("<I", len(r["ac_order"])) + b"".join(struct.pack("<I", x) for x in r["ac_order"])

    out = bytearray(b[: r["pos_start"] + 8]) + pos + r["gap"] + ll + ac + r["gap2"] + b[r["b2_start"] :]
    delta = len(out) - len(b)
    struct.pack_into("<II", out, 8, r["hdr"]["offA"] + delta, r["hdr"]["offB"] + delta)
    return bytes(out), log


def build_set(b, r, venue, cue_name, node_name, values, profile=None):
    """Set the given attribute values (DMX 0-255) for one device (node) of the venue in an attribute cue.
    Existing values of that device in the cue are replaced, other devices stay untouched."""
    g = venue["guid"]
    tree = tree_nodes(b, *tree_range(r, g))
    if node_name.startswith("#"):  # device by node number, e.g. "#9"
        node = int(node_name[1:])
        hits = [t for i, t, _ in tree if i == node]
        if len(hits) != 1:
            raise ValueError(f"Node {node_name} not found in {venue['name']!r}")
        profile = profile or hits[0]
        node_name = f"{hits[0]} {node_name}"
    else:
        nodes = [i for i, t, _ in tree if t == node_name]
        if len(nodes) != 1:
            raise ValueError(f"Device {node_name!r} in {venue['name']!r}: {len(nodes)} matches, expected exactly 1 "
                             f"(for devices with the same name use '#number')")
        node = nodes[0]
    # Look up attribute names only when needed; plain numbers are taken directly as SoundSwitch attribute
    # numbers (safer for devices with several channel modes).
    attrs = {}
    if any(not name.isdigit() for name, _ in values):
        attrs = profile_attributes(b, r, g, profile or node_name)
    ents_new = []
    for name, val in values:
        if name.isdigit():
            a = int(name)
        elif name in attrs:
            a = attrs[name]
        else:
            raise ValueError(f"Unknown attribute {name!r}. Available: {list(attrs)}")
        if not 0 <= val <= 255:
            raise ValueError(f"{name}: value {val} outside 0-255")
        ents_new.append((a, val))
    ents_new.sort()

    cues = [o for o in r["attrcues"] if o["name"] == cue_name]
    if len(cues) != 1:
        raise ValueError(f"Attribute cue {cue_name!r}: {len(cues)} matches, expected exactly 1")
    log = []
    ac = b"\x02\x00\x00\x00\x00\x00\x00\x00"
    for o in r["attrcues"]:
        subs = [s["raw"] for s in o["subs"]]
        if o is cues[0]:
            idx = next((k for k, s in enumerate(o["subs"]) if s["key"] == g), None)
            if idx is None:
                raise ValueError(f"Cue {cue_name!r} has no entry for venue {venue['name']!r}")
            raw = subs[idx]
            n = struct.unpack_from("<I", raw, 24)[0]
            old = [raw[28 + 16 * k : 44 + 16 * k] for k in range(n)]
            keep = [e for e in old if struct.unpack_from("<I", e, 4)[0] != node]
            prev = {struct.unpack_from("<I", e, 8)[0]: e[12] for e in old if struct.unpack_from("<I", e, 4)[0] == node}
            add = [struct.pack("<III", 1, node, a) + bytes([v]) * 4 for a, v in ents_new]
            allents = sorted(keep + add, key=lambda e: struct.unpack_from("<II", e, 4))
            subs[idx] = raw[:24] + struct.pack("<I", len(allents)) + b"".join(allents)
            inv = {v: k for k, v in attrs.items()}
            inv.update({a: f"Attribute {a}" for a, _ in ents_new if a not in inv})
            inv.update({a: f"Attribute {a}" for a in prev if a not in inv})
            log.append(f"{cue_name} / {node_name} in {venue['name']}:")
            for a, v in ents_new:
                log.append(f"    {inv[a]:18} {str(prev.get(a, '-')):>4} -> {v}")
            for a in prev:
                if a not in dict(ents_new):
                    log.append(f"    {inv.get(a, a)!s:18} {prev[a]:>4} -> (removed)")
        ac += b"\x01\x00\x00\x00" + struct.pack("<I", len(subs)) + b"".join(subs) + o["tail"]
    ac += struct.pack("<I", len(r["ac_order"])) + b"".join(struct.pack("<I", x) for x in r["ac_order"])
    out = bytearray(b[: r["ll_end"]]) + ac + r["gap2"] + b[r["b2_start"] :]
    delta = len(out) - len(b)
    struct.pack_into("<II", out, 8, r["hdr"]["offA"] + delta, r["hdr"]["offB"] + delta)
    return bytes(out), log


def write_with_backup(path, out):
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    bak = f"{path}.{stamp}.bak"
    n = 2
    while os.path.exists(bak):  # never overwrite an existing backup
        bak = f"{path}.{stamp}-{n}.bak"
        n += 1
    shutil.copy2(path, bak)
    with open(path, "wb") as f:
        f.write(out)
    return bak


def find_project_files():
    """SoundSwitchVenues.bin files of all projects in the default macOS location."""
    return sorted(glob.glob(os.path.expanduser("~/Music/SoundSwitch/*.ssproj/SoundSwitchVenues.bin")))


def resolve_file(arg):
    """Path given with --file, or the single project found in ~/Music/SoundSwitch."""
    if arg:
        path = os.path.expanduser(arg)
        if os.path.isdir(path):  # allow pointing at the .ssproj folder
            path = os.path.join(path, "SoundSwitchVenues.bin")
        if not os.path.isfile(path):
            raise SystemExit(f"error: file not found: {path}")
        return path
    found = find_project_files()
    if len(found) == 1:
        print(f"Using {found[0]}\n")
        return found[0]
    if not found:
        raise SystemExit("error: no SoundSwitch project found in ~/Music/SoundSwitch.\n"
                         "       Pass the file explicitly: --file /path/to/YourProject.ssproj/SoundSwitchVenues.bin")
    raise SystemExit("error: several SoundSwitch projects found, choose one with --file:\n  " + "\n  ".join(found))


def soundswitch_running():
    """True if a process with 'soundswitch' in its name is running (checked with pgrep, macOS/Linux)."""
    try:
        res = subprocess.run(["pgrep", "-il", "soundswitch"], capture_output=True, text=True)
    except OSError:
        return False
    return bool(res.stdout.strip())


def find_venue(r, name):
    venue = next((v for v in r["venues"] if v["name"] == name), None)
    if venue is None:
        raise SystemExit(f"error: venue {name!r} not found. Available: {[v['name'] for v in r['venues']]}\n"
                         "       (names are case sensitive; put names with spaces in quotes)")
    return venue


def finish(path, b, out, args):
    """Validate the result, then either stop (dry run) or write it with a backup."""
    parse(out)  # the result must parse cleanly
    print(f"Result: {len(out)} bytes ({len(out) - len(b):+d}), validation parse OK")
    if not args.write:
        print("Dry run - nothing was written. Add --write to apply the change (a backup is made first).")
        return 0
    if soundswitch_running() and not args.ignore_running:
        raise SystemExit("error: SoundSwitch seems to be running. Quit it first (it would overwrite the change),\n"
                         "       or pass --ignore-running if you are sure it is not.")
    print(f"Written. Backup: {write_with_backup(path, out)}")
    return 0


def build_parser():
    ap = argparse.ArgumentParser(
        prog="ssvenues.py",
        description="Copy static looks, positions, attribute cues and fixture type/groups between SoundSwitch venues.",
        epilog="Nothing is written unless you add --write. See README.md for a step-by-step guide.")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-f", "--file", metavar="PATH",
                        help="SoundSwitchVenues.bin or its .ssproj folder (default: found in ~/Music/SoundSwitch)")
    writer = argparse.ArgumentParser(add_help=False)
    writer.add_argument("--write", action="store_true", help="really change the file (default: dry run)")
    writer.add_argument("--ignore-running", action="store_true", help="skip the check whether SoundSwitch is running")
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="COMMAND")
    sub.add_parser("info", parents=[common], help="list venues, position presets, static looks and attribute cues")
    p = sub.add_parser("fixtures", parents=[common], help="list the fixtures of a venue with type and groups")
    p.add_argument("venue")
    for name, text in (("copy", "copy looks, positions, attribute cues, fixture type and groups"),
                       ("flags", "copy only fixture type and groups")):
        p = sub.add_parser(name, parents=[common, writer], help=text)
        p.add_argument("source", help="venue to copy from")
        p.add_argument("target", help="venue to copy to")
    p = sub.add_parser("set", parents=[common, writer], help="set attribute values of one device in an attribute cue")
    p.add_argument("venue")
    p.add_argument("cue", help="name of the attribute cue")
    p.add_argument("device", help="device name, or #<node number> for devices with identical names")
    p.add_argument("values", nargs="+", metavar="ATTRIBUTE=VALUE", help="e.g. Gobo=195 (DMX value 0-255)")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    path = resolve_file(args.file)
    with open(path, "rb") as fh:
        b = fh.read()
    try:
        r = parse(b)
    except (AssertionError, ValueError, struct.error, IndexError, StopIteration) as e:
        raise SystemExit(f"error: cannot read {path} ({e}).\n"
                         "       This tool was tested with SoundSwitch 2.11 only; the file format may differ in your version.")
    if args.cmd == "info":
        info(b, r)
        return 0
    if args.cmd == "fixtures":
        fixtures(b, r, find_venue(r, args.venue))
        return 0
    try:
        if args.cmd == "set":
            venue = find_venue(r, args.venue)
            values = []
            for pr in args.values:
                k, sep, v = pr.rpartition("=")
                if not sep or not v.lstrip("-").isdigit():
                    raise SystemExit(f"error: {pr!r} is not of the form Attribute=Value (value is a number)")
                values.append((k, int(v)))
            out, log = build_set(b, r, venue, args.cue, args.device, values)
        else:
            src, dst = find_venue(r, args.source), find_venue(r, args.target)
            if src is dst:
                raise SystemExit("error: source and target are the same venue.")
            if args.cmd == "flags":
                out, log = copy_fixture_flags(b, r, src, dst)
                print(f"Copying fixture type and groups from {src['name']!r} to {dst['name']!r}:")
            else:
                out, log = build_copy(b, r, src, dst)
                print(f"Copying looks from {src['name']!r} to {dst['name']!r}:")
    except ValueError as e:
        raise SystemExit(f"error: {e}")
    for line in log:
        print(line if args.cmd == "set" else "  " + line)
    return finish(path, b, out, args)


if __name__ == "__main__":
    sys.exit(main())
