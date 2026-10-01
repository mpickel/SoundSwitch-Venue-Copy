#!/usr/bin/env python3
"""Tests für ssvenues.py gegen die echte SoundSwitchVenues.bin (nur lesend, nichts wird geschrieben).

Aufruf:  python3 -m unittest specs/test_ssvenues.py
Datei:   Umgebungsvariable SSVENUES_BIN oder ~/Music/SoundSwitch/DJ_eMPi.ssproj/SoundSwitchVenues.bin
"""
import os
import struct
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import ssvenues as S  # noqa: E402

BIN = os.environ.get("SSVENUES_BIN", os.path.expanduser("~/Music/SoundSwitch/DJ_eMPi.ssproj/SoundSwitchVenues.bin"))

FULL = 0x3FF0000000000000  # double 1.0
MAGENTA = bytes.fromhex("c204deff00000000")


def leaf_lookids(b, r, venue):
    """Name -> Look-Nummer der Blatt-Knoten (Geräte/Zellen) einer Venue."""
    return {t: lid for _, t, lid in S.tree_nodes(b, *S.tree_range(r, venue["guid"])) if lid is not None}


def slot_entries(slot, which):
    """Liste A..E eines Slots als {Nummer: Rest-Bytes}."""
    out, at = {}, 4 if which == "E" else 0  # Liste E: (1, Knoten, Attribut, Wert)
    for e in slot["lists"]["ABCDE".index(which)]:
        out[struct.unpack_from("<I", e, at)[0]] = e[at + 4 :]
    return out


@unittest.skipUnless(os.path.exists(BIN), f"{BIN} nicht vorhanden")
class CopyLooksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(BIN, "rb") as f:
            cls.b = f.read()
        cls.r = S.parse(cls.b)
        cls.byname = {v["name"]: v for v in cls.r["venues"]}

    def copy(self, src, dst):
        out, log = S.build_copy(self.b, self.r, self.byname[src], self.byname[dst])
        r2 = S.parse(out)
        return out, r2, log

    def look(self, b, r, venue, name):
        ll = next(x for x in r["looklists"] if x["key"] == self.byname[venue]["guid"])
        return next(s for s in ll["slots"] if s["name"] == name)

    def test_tree_nodes_liefern_look_nummern(self):
        ids = leaf_lookids(self.b, self.r, self.byname["Default"])
        self.assertEqual(ids["L-Maxi 02 L1"], 32)
        self.assertEqual(ids["Blazor"], 301)
        self.assertNotIn("Maxi 1 (L1 R1)", ids)  # Gruppen-Knoten haben keine Look-Nummer

    def test_dinner_default_landet_auf_richtigen_geraeten(self):
        out, r2, log = self.copy("Default", "KLS-PT")
        ids = leaf_lookids(out, r2, self.byname["KLS-PT"])
        slot = self.look(out, r2, "KLS-PT", "Dinner-Default")
        a, c = slot_entries(slot, "A"), slot_entries(slot, "C")
        for name in ("L-Maxi 02 L1", "R-Maxi 06 R1", "L-Maxi 05 L3"):
            self.assertEqual(struct.unpack("<Q", a[ids[name]])[0], FULL, name)
            self.assertEqual(c[ids[name]], MAGENTA, name)
        self.assertNotIn(ids["Thunderwash 600 UV"], a)  # in der Quelle nicht angehakt
        self.assertEqual(struct.unpack("<Q", a[ids["Blazor"]])[0], FULL)
        # keine Verweise auf Nummern, die es in der Ziel-Venue nicht gibt (alle Blätter, auch gleichnamige)
        valid = {lid for _, _, lid in S.tree_nodes(out, *S.tree_range(r2, self.byname["KLS-PT"]["guid"])) if lid is not None}
        for which in "ABCD":
            self.assertTrue(set(slot_entries(slot, which)) <= valid, f"Liste {which}: verwaiste Nummern")

    def test_liste_e_verwendet_knoten_nummern(self):
        out, r2, log = self.copy("Default", "KLS-PT")
        slot = self.look(out, r2, "KLS-PT", "Dinner-Default")
        nodes = {t: i for i, t, _ in S.tree_nodes(out, *S.tree_range(r2, self.byname["KLS-PT"]["guid"]))}
        e_nodes = set(slot_entries(slot, "E"))
        self.assertIn(nodes["Blazor"], e_nodes)
        self.assertTrue(e_nodes <= set(nodes.values()), "Liste E: verwaiste Knoten")

    def test_quelle_bleibt_unveraendert(self):
        out, r2, log = self.copy("Default", "KLS-PT")
        self.assertEqual(self.look(out, r2, "Default", "Dinner-Default"), self.look(self.b, self.r, "Default", "Dinner-Default"))

    def test_identische_venue_unveraendert_bei_gleichen_nummern(self):
        # Test ist eine unveränderte Kopie von Default: Knoten-Mapping muss vollständig sein
        m, lm, log = S.node_mapping(self.b, self.r, self.byname["Default"], self.byname["Test"])
        self.assertEqual(len(m), len(S.tree_nodes(self.b, *S.tree_range(self.r, self.byname["Default"]["guid"]))))


if __name__ == "__main__":
    unittest.main()
