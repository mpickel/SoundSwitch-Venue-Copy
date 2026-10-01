#!/usr/bin/env python3
"""SoundSwitch 2.11 `SoundSwitchVenues.bin` – Parser und Venue-Look-Kopierer (reverse engineered).

Aufbau der Datei (siehe docu/format.md):
  header      : magic aaaa0955, u32 3, u32 offA, u32 offB, u32 ?, u32 venue_count
  venues      : venue_count Blöcke, je 04000000 + GUID + 01000000 + Name ...
  positions   : 02000000 00000000, dann Objekte:
                02000000, nsub, nsub x sub(GUID, 02000000, n, n x (u32 idx, u32 1, 8 Bytes)),
                01000000, Name, GUID, u32 colour, u32 a
                danach Reihenfolge (u32 n, n x u32) und 14 opake Bytes
  looklists   : u32 count; count x (GUID, 01000000, 20000000, 32 Slots)   -> statische Looks 1-32
  attrcues    : 02000000 00000000, dann Objekte:
                01000000, nven, nven x (GUID, 01000000, 01000000, n, n x 16 Bytes), 01000000, Name, GUID, colour, a
                danach Reihenfolge (u32 n, n x u32) und opake Cue-Gruppen
  bank2       : u32 count; count x (GUID, 02000000, 96 Slots "33".."128", 128 x 25 Bytes)
  fixture-rec : endet mit Profil-GUID + 6 u32: hash, Modus, DMX-Adresse-1, Profil-Hash, Typ, Gruppen
                Typ: 2 Wash (Primary), 3 Wash (Secondary), 4 Wash (Tertiary), 11 Multi Cell (Primary),
                12 Multi Cell (Secondary), weitere Werte unbekannt; Gruppen: Group1..4 (0 = keine)
  tail        : 46 Bytes (offA zeigt hierher), Tabelle (offset, len, 0, 1) je Fixture-Datensatz,
                ffffffff, u32 7, "Default"

Slot = 05000000 01000000 Name, 5 Listen: A idx+double (12), B idx+8 (12), C idx+8 (12),
       D idx+GUID (20, Positions-Preset), E 16 Bytes (Attribut-Werte)

Aufruf:
  python3 ssvenues.py info  <SoundSwitchVenues.bin>
  python3 ssvenues.py copy  <SoundSwitchVenues.bin> "<Quell-Venue>" "<Ziel-Venue>" [--write]
  python3 ssvenues.py fixtures <SoundSwitchVenues.bin> "<Venue>"      (Geräte mit Typ und Gruppe)
  python3 ssvenues.py flags <SoundSwitchVenues.bin> "<Quell-Venue>" "<Ziel-Venue>" [--write]
                                                   (nur Geräte-Typ und Gruppen übertragen, Rest unverändert)
  python3 ssvenues.py set   <SoundSwitchVenues.bin> "<Venue>" "<Attribute-Cue>" "<Gerät>" "Attribut=Wert" ... [--write]
"""
import datetime
import os
import re
import shutil
import struct
import sys

MAGIC = b"\xaa\xaa\x09\x55"


class P:
    """Kleiner Cursor über Bytes."""

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
        if p.u32() != 2:  # jedes Objekt beginnt mit 02000000
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
    p.expect(5, "slot tag")
    p.expect(1, "slot tag2")
    name = p.str()
    lists = []
    # A: idx+double (Intensität), B: idx+8B, C: idx+8B (Farbe), D: idx+GUID (Positions-Preset), E: 16B (Attribute)
    for width in (12, 12, 12, 20, 16):
        n = p.u32()
        if n > 10000:
            raise ValueError(f"slot {name!r}: implausible list count {n:#x} at {p.o-4:#x}")
        lists.append([p.raw(width) for _ in range(n)])
    return {"name": name, "lists": lists}


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
    assert b[:4] == MAGIC, "kein SoundSwitchVenues.bin (Magic fehlt)"
    hdr = dict(zip(("ver", "offA", "offB", "x", "nven"), struct.unpack_from("<IIIII", b, 4)))
    vens = find_venues(b)
    assert len(vens) == hdr["nven"], f"Header sagt {hdr['nven']} Venues, gefunden {len(vens)}"
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


# ---------------------------------------------------------------- Ausgabe

def info(b, r):
    names = {v["guid"]: v["name"] for v in r["venues"]}
    print(f"Datei: {len(b)} Bytes, {r['hdr']['nven']} Venues")
    for v in r["venues"]:
        print(f"  Venue {v['name']!r}")
    print(f"\nPositions-Presets ({len(r['positions'])}):")
    for o in r["positions"]:
        keys = [names[s["key"]] for s in o["subs"] if s["key"] in names]
        print(f"  {o['name']!r:22} Venues: {keys}")
    print("\nStatische Looks (Slots 1-32) pro Venue:")
    for ll in r["looklists"]:
        nm = names.get(ll["key"])
        if nm:
            named = [s["name"] for s in ll["slots"] if not s["name"].isdigit()]
            print(f"  {nm!r:20} {len(named):2} belegt: {named}")
    print(f"\nAttribute-Cues ({len(r['attrcues'])}):")
    for o in r["attrcues"]:
        vs = {names[s["key"]]: s["n"] for s in o["subs"] if s["key"] in names}
        print(f"  {o['name']!r:26} Einträge je Venue: {vs}")
    b2 = {names[x["key"]]: sum(1 for s in x["slots"] if not s["name"].isdigit()) for x in r["bank2"] if x["key"] in names}
    print(f"\nLooks Slots 33-128 belegt: {b2}")


# ---------------------------------------------------------------- Geräte-Baum

NODE = re.compile(rb"\x03\x00\x00\x00\x02\x00\x00\x00(.{4})\x01\x00\x00\x00(.{4})", re.S)


def venue_bounds(r):
    vens = r["venues"]
    ends = [v["off"] for v in vens[1:]] + [r["pos_start"]]
    return {v["guid"]: (v["off"], e) for v, e in zip(vens, ends)}


def tree_nodes(b, lo, hi):
    """Knoten des Geräte-Baums einer Venue: 03000000 02000000 <id> 01000000 <name>, in Dateireihenfolge."""
    out = []
    for m in NODE.finditer(b, lo, hi):
        n = struct.unpack("<I", m.group(2))[0]
        if not (1 <= n <= 80):
            continue
        try:
            t = b[m.end() : m.end() + 2 * n - 2].decode("utf-16le")
        except UnicodeDecodeError:
            continue
        if t.isprintable():
            out.append((struct.unpack("<I", m.group(1))[0], t))
    return out


def tree_range(r, g):
    """Bereich des Geräte-Baums einer Venue: hinter den Geräte-Datensätzen (davor stehen Profile mit ähnlich kodierten Kanälen)."""
    lo, hi = venue_bounds(r)[g]
    ends = [a + l for a, l in r["tail"]["recs"] if lo <= a < hi]
    return (max(ends) if ends else lo), hi


ATTR = re.compile(rb"\x02\x00\x00\x00(.{4})\x01\x00\x00\x00(.{4})", re.S)


def profile_attributes(b, r, g, profile):
    """Attribute (Name -> SoundSwitch-Nummer) eines Geräteprofils in der Venue, gelesen ab dem Profilnamen bis 'Main'."""
    lo, _ = venue_bounds(r)[g]
    hi, _ = tree_range(r, g)
    start = b.find(profile.encode("utf-16le") + b"\x00\x00", lo, hi)
    if start < 0:
        raise ValueError(f"Profil {profile!r} in der Venue nicht gefunden")
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


def node_mapping(b, r, src, dst):
    """Ordnet Knoten-IDs der Quell-Venue den IDs der Ziel-Venue zu (gleicher Baum, gleiche Reihenfolge)."""
    a = tree_nodes(b, *tree_range(r, src["guid"]))
    c = tree_nodes(b, *tree_range(r, dst["guid"]))
    if [t for _, t in a] != [t for _, t in c]:
        raise ValueError(
            f"Geräte-Baum von {src['name']!r} und {dst['name']!r} unterscheidet sich "
            f"({len(a)} vs {len(c)} Knoten) – Ziel muss eine unveränderte Kopie der Quelle sein.")
    m, bad = {}, set()
    for (i, _), (j, _) in zip(a, c):
        if m.get(i, j) != j:
            bad.add(i)
        m[i] = j
    for i in bad:
        del m[i]
    return m


# ---------------------------------------------------------------- Geräte-Datensätze (Typ, Gruppe)

TYPE_NAMES = {2: "Wash (Primary)", 3: "Wash (Secondary)", 4: "Wash (Tertiary)",
              11: "Multi Cell (Primary)", 12: "Multi Cell (Secondary)"}


def fixture_records(b, r, g):
    """Oberste Geräte-Datensätze einer Venue. Je Datensatz: Schlüssel (Profil-GUID, Modus, DMX-1), Typ, Gruppen
    und die Datei-Offsets von Typ und Gruppen (die letzten zwei u32 des Datensatzes)."""
    lo, hi = venue_bounds(r)[g]
    recs = [(a, l) for a, l in r["tail"]["recs"] if lo <= a < hi]
    out = []
    for a, l in recs:
        if any(x < a < x + y for x, y in recs):  # Unter-Datensatz (Zelle) überspringen
            continue
        end = a + l
        guid = b[end - 40 : end - 24]
        _, mode, dmx, _, typ, grp = struct.unpack_from("<6I", b, end - 24)
        out.append({"key": (guid, mode, dmx), "dmx": dmx + 1, "type": typ, "groups": grp,
                    "off_type": end - 8, "off_groups": end - 4})
    return out


def fixtures(b, r, venue):
    recs = fixture_records(b, r, venue["guid"])
    print(f"Geräte in {venue['name']!r} ({len(recs)}):")
    for f in sorted(recs, key=lambda f: f["dmx"]):
        tn = TYPE_NAMES.get(f["type"], f"Typ {f['type']}")
        print(f"  DMX {f['dmx']:3d}  Profil {f['key'][0][3:7].hex()}  Modus {f['key'][1]}  {tn:24} Gruppen {f['groups']}")


def copy_fixture_flags(b, r, src, dst):
    """Überträgt Typ (Wash/Multi Cell ...) und Gruppen-Zuordnung je Gerät von src nach dst.
    Geräte werden über Profil-GUID, Modus und DMX-Adresse zugeordnet. Gibt (neue Bytes, Log) zurück."""
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
    log.append(f"Geräte-Typ und Gruppen: {changed} Geräte angepasst"
               + (f" (ohne Gegenstück in Quelle, DMX: {missing})" if missing else ""))
    return bytes(out), log


# ---------------------------------------------------------------- Kopieren

def remap_cue_sub(raw, newkey, m):
    """Attribute-Cue-Eintrag: GUID, 01, 01, n, n x (u32 1, u32 knoten, u32 attribut, u32 wert)."""
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


def remap_pos_sub(raw, newkey, m):
    """Positions-Eintrag: GUID, 02, n, n x (u32 knoten, u32 1, 8 Bytes)."""
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
    """Erzeugt neue Dateibytes, in denen alle Look-Daten von Venue src auch für Venue dst vorhanden sind."""
    sg, dg = src["guid"], dst["guid"]
    m = node_mapping(b, r, src, dst)
    b, log = copy_fixture_flags(b, r, src, dst)  # gleiche Länge, Offsets bleiben gültig

    def fmt_drop(d):
        return f" (verwaiste Verweise in Quelle ignoriert: {sorted(set(d))})" if d else ""

    # positions
    pos = bytearray()
    for o in r["positions"]:
        subs = [s for s in o["subs"] if s["key"] != dg]
        srcsub = next((s for s in o["subs"] if s["key"] == sg), None)
        if srcsub:
            raw, n, d = remap_pos_sub(srcsub["raw"], dg, m)
            subs.append({"raw": raw})
            log.append(f"Position {o['name']!r}: {n} Werte übernommen{fmt_drop(d)}")
        pos += b"\x02\x00\x00\x00" + struct.pack("<I", len(subs))
        for s in subs:
            pos += s["raw"]
        pos += o["tail"]
    pos += struct.pack("<I", len(r["order"])) + b"".join(struct.pack("<I", x) for x in r["order"])

    # looklists
    ll = struct.pack("<I", len(r["looklists"]))
    srcll = next(x for x in r["looklists"] if x["key"] == sg)
    for x in r["looklists"]:
        raw = srcll["raw"] if x["key"] == dg else x["raw"]
        ll += x["key"] + b"\x01\x00\x00\x00\x20\x00\x00\x00" + raw
    named = [s["name"] for s in srcll["slots"] if not s["name"].isdigit()]
    log.append(f"Statische Looks: {len(named)} Slots übernommen: {named}")

    # attrcues
    ac = b"\x02\x00\x00\x00\x00\x00\x00\x00"
    for o in r["attrcues"]:
        subs = [s for s in o["subs"] if s["key"] != dg]
        srcsub = next((s for s in o["subs"] if s["key"] == sg), None)
        if srcsub:
            raw, n, d = remap_cue_sub(srcsub["raw"], dg, m)
            subs.append({"raw": raw})
            log.append(f"Attribute-Cue {o['name']!r}: {n} Werte übernommen{fmt_drop(d)}")
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
    """Setzt in einem Attribute-Cue für ein Gerät (Knoten) der Venue die angegebenen Attribut-Werte (DMX 0-255).
    Bisherige Werte dieses Geräts im Cue werden ersetzt, andere Geräte bleiben unverändert."""
    g = venue["guid"]
    tree = tree_nodes(b, *tree_range(r, g))
    if node_name.startswith("#"):  # Gerät über Knoten-Nummer, z. B. "#9"
        node = int(node_name[1:])
        hits = [t for i, t in tree if i == node]
        if len(hits) != 1:
            raise ValueError(f"Knoten {node_name} in {venue['name']!r} nicht gefunden")
        node_name = f"{hits[0]} {node_name}"
    else:
        nodes = [i for i, t in tree if t == node_name]
        if len(nodes) != 1:
            raise ValueError(f"Gerät {node_name!r} in {venue['name']!r}: {len(nodes)} Treffer, erwartet genau 1 "
                             f"(bei gleichnamigen Geräten '#Nummer' verwenden)")
        node = nodes[0]
    # Attribut-Namen nur bei Bedarf nachschlagen; Zahlen werden direkt als SoundSwitch-Attribut-Nummer genommen
    # (sicherer bei Geräten mit mehreren Kanal-Modi).
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
            raise ValueError(f"Attribut {name!r} unbekannt. Vorhanden: {list(attrs)}")
        if not 0 <= val <= 255:
            raise ValueError(f"{name}: Wert {val} außerhalb 0-255")
        ents_new.append((a, val))
    ents_new.sort()

    cues = [o for o in r["attrcues"] if o["name"] == cue_name]
    if len(cues) != 1:
        raise ValueError(f"Attribute-Cue {cue_name!r}: {len(cues)} Treffer")
    log = []
    ac = b"\x02\x00\x00\x00\x00\x00\x00\x00"
    for o in r["attrcues"]:
        subs = [s["raw"] for s in o["subs"]]
        if o is cues[0]:
            idx = next((k for k, s in enumerate(o["subs"]) if s["key"] == g), None)
            if idx is None:
                raise ValueError(f"Cue {cue_name!r} hat keinen Eintrag für Venue {venue['name']!r}")
            raw = subs[idx]
            n = struct.unpack_from("<I", raw, 24)[0]
            old = [raw[28 + 16 * k : 44 + 16 * k] for k in range(n)]
            keep = [e for e in old if struct.unpack_from("<I", e, 4)[0] != node]
            prev = {struct.unpack_from("<I", e, 8)[0]: e[12] for e in old if struct.unpack_from("<I", e, 4)[0] == node}
            add = [struct.pack("<III", 1, node, a) + bytes([v]) * 4 for a, v in ents_new]
            allents = sorted(keep + add, key=lambda e: struct.unpack_from("<II", e, 4))
            subs[idx] = raw[:24] + struct.pack("<I", len(allents)) + b"".join(allents)
            inv = {v: k for k, v in attrs.items()}
            inv.update({a: f"Attribut {a}" for a, _ in ents_new if a not in inv})
            inv.update({a: f"Attribut {a}" for a in prev if a not in inv})
            log.append(f"{cue_name} / {node_name} in {venue['name']}:")
            for a, v in ents_new:
                log.append(f"    {inv[a]:18} {str(prev.get(a, '-')):>4} -> {v}")
            for a in prev:
                if a not in dict(ents_new):
                    log.append(f"    {inv.get(a, a)!s:18} {prev[a]:>4} -> (entfernt)")
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
    while os.path.exists(bak):  # nie ein bestehendes Backup überschreiben
        bak = f"{path}.{stamp}-{n}.bak"
        n += 1
    shutil.copy2(path, bak)
    with open(path, "wb") as f:
        f.write(out)
    return bak


def main(argv):
    if len(argv) >= 3 and argv[1] == "set":
        # set <datei> <venue> <cue> <gerät> Attribut=Wert ... [--write]
        path = argv[2]
        args = [a for a in argv[3:] if a != "--write"]
        if len(args) < 4:
            print(__doc__)
            return 2
        venue_name, cue_name, node_name, pairs = args[0], args[1], args[2], args[3:]
        b = open(path, "rb").read()
        r = parse(b)
        venue = next((v for v in r["venues"] if v["name"] == venue_name), None)
        if venue is None:
            print(f"Venue {venue_name!r} nicht gefunden.")
            return 1
        values = []
        for pr in pairs:
            k, _, v = pr.rpartition("=")
            values.append((k, int(v)))
        out, log = build_set(b, r, venue, cue_name, node_name, values)
        print("\n".join(log))
        parse(out)
        print(f"Ergebnis: {len(out)} Bytes ({len(out)-len(b):+d}), Prüf-Parse OK")
        if "--write" not in argv:
            print("Trockenlauf – nichts geschrieben.")
            return 0
        print(f"Geschrieben. Backup: {write_with_backup(path, out)}")
        return 0
    if len(argv) < 3 or argv[1] not in ("info", "copy", "fixtures", "flags"):
        print(__doc__)
        return 2
    path = argv[2]
    b = open(path, "rb").read()
    r = parse(b)
    if argv[1] == "info":
        info(b, r)
        return 0
    if argv[1] == "fixtures":
        venue = next((v for v in r["venues"] if len(argv) > 3 and v["name"] == argv[3]), None)
        if venue is None:
            print(f"Venue nicht gefunden. Vorhanden: {[v['name'] for v in r['venues']]}")
            return 1
        fixtures(b, r, venue)
        return 0
    if len(argv) < 5:
        print(__doc__)
        return 2
    byname = {v["name"]: v for v in r["venues"]}
    for n in (argv[3], argv[4]):
        if n not in byname:
            print(f"Venue {n!r} nicht gefunden. Vorhanden: {list(byname)}")
            return 1
    src, dst = byname[argv[3]], byname[argv[4]]
    if src is dst:
        print("Quelle und Ziel sind gleich.")
        return 1
    if argv[1] == "flags":
        out, log = copy_fixture_flags(b, r, src, dst)
        print(f"Übertrage Geräte-Typ und Gruppen von {src['name']!r} nach {dst['name']!r}:")
    else:
        out, log = build_copy(b, r, src, dst)
        print(f"Kopiere Looks von {src['name']!r} nach {dst['name']!r}:")
    for l in log:
        print("  " + l)
    r2 = parse(out)  # muss sauber parsen
    print(f"Ergebnis: {len(out)} Bytes ({len(out)-len(b):+d}), Prüf-Parse OK")
    if "--write" not in argv:
        print("Trockenlauf – nichts geschrieben. Mit --write wird die Datei geändert (Backup wird angelegt).")
        return 0
    print(f"Geschrieben. Backup: {write_with_backup(path, out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
