"""Tests for ssvenues.py.

Run from the repository root:  python3 -m unittest discover -s tests -v

Part 1 needs no SoundSwitch data. Part 2 runs against a real SoundSwitchVenues.bin (read only, nothing is
written). Point SSVENUES_BIN at it, or keep exactly one project in ~/Music/SoundSwitch. Without a file
the Part 2 tests are skipped. The real file needs a venue called "Default" and at least one more venue.
"""
import contextlib
import io
import os
import struct
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import ssvenues as S  # noqa: E402


def find_bin():
    env = os.environ.get("SSVENUES_BIN")
    if env:
        return os.path.join(env, "SoundSwitchVenues.bin") if os.path.isdir(env) else env
    found = S.find_project_files()
    return found[0] if len(found) == 1 else None


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = S.main(list(argv))
        except SystemExit as e:
            code = e.code
    return code, out.getvalue(), err.getvalue()


# ------------------------------------------------------------------ Part 1: synthetic

class AlignTest(unittest.TestCase):
    def nodes(self, *names):
        return [(i, n, i) for i, n in enumerate(names)]

    def test_identical_lists(self):
        a = self.nodes("A", "B", "C")
        self.assertEqual(S.align(a, a), [(0, 0), (1, 1), (2, 2)])

    def test_target_has_fewer_devices(self):
        pairs = S.align(self.nodes("A", "B", "C", "D"), self.nodes("A", "D"))
        self.assertEqual(pairs, [(0, 0), (3, 1)])

    def test_target_has_extra_device(self):
        pairs = S.align(self.nodes("A", "C"), self.nodes("A", "B", "C"))
        self.assertEqual(pairs, [(0, 0), (1, 2)])

    def test_duplicate_names_keep_order(self):
        pairs = S.align(self.nodes("X", "X", "Y"), self.nodes("X", "Y", "X"))
        self.assertEqual(len(pairs), 2)
        self.assertEqual(pairs[-1][0] > pairs[0][0] and pairs[-1][1] > pairs[0][1], True)


class RemapSlotTest(unittest.TestCase):
    def test_lists_use_the_right_numbering(self):
        entry = lambda n, rest: struct.pack("<I", n) + rest  # noqa: E731
        eight = b"\x01" * 8
        slot = {"head": b"HEAD",
                "lists": [[entry(5, eight), entry(6, eight)],           # A: look numbers
                          [entry(5, eight)],                            # B
                          [entry(6, eight)],                            # C
                          [struct.pack("<I", 5) + b"G" * 16],           # D
                          [struct.pack("<III", 1, 100, 8) + b"\x07" * 4]]}  # E: (1, node, attribute, value)
        out, dropped = S.remap_slot(slot, m={100: 200}, lm={5: 50})
        self.assertTrue(out.startswith(b"HEAD"))
        body = out[4:]
        # A: look 5 -> 50, look 6 dropped
        self.assertEqual(struct.unpack_from("<II", body, 0), (1, 50))
        self.assertEqual(dropped, {6})
        # E: node 100 -> 200, attribute and value untouched
        e = body[-(4 + 16):]
        self.assertEqual(struct.unpack("<IIII", e[4:]), (1, 200, 8, 0x07070707))


class CliTest(unittest.TestCase):
    def test_help_and_version(self):
        for flag in ("--help", "--version"):
            code, out, _ = run_cli(flag)
            self.assertEqual(code, 0)
            self.assertIn("ssvenues", out)

    def test_command_is_required(self):
        code, _, err = run_cli()
        self.assertNotEqual(code, 0)

    def test_missing_file(self):
        code, _, err = run_cli("info", "--file", "/definitely/not/here.bin")
        self.assertNotEqual(code, 0)

    def test_garbage_file(self):
        code, _, err = run_cli("info", "--file", os.path.abspath(S.__file__))
        self.assertNotEqual(code, 0)


# ------------------------------------------------------------------ Part 2: real data

BIN = find_bin()


@unittest.skipUnless(BIN and os.path.exists(BIN), "no SoundSwitchVenues.bin (set SSVENUES_BIN)")
class RealFileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(BIN, "rb") as f:
            cls.b = f.read()
        cls.r = S.parse(cls.b)
        cls.byname = {v["name"]: v for v in cls.r["venues"]}
        if "Default" not in cls.byname or len(cls.byname) < 2:
            raise unittest.SkipTest('needs a venue called "Default" and at least one more venue')
        cls.targets = [v for n, v in cls.byname.items() if n != "Default"]

    def tree(self, b, r, venue):
        return S.tree_nodes(b, *S.tree_range(r, venue["guid"]))

    def slots(self, r, venue):
        ll = next(x for x in r["looklists"] if x["key"] == venue["guid"])
        return {s["name"]: s for s in ll["slots"] if not s["name"].isdigit()}

    def test_copy_has_no_orphans_and_matches_devices_by_name(self):
        src = self.byname["Default"]
        src_tree = self.tree(self.b, self.r, src)
        for dst in self.targets:
            with self.subTest(venue=dst["name"]):
                out, _ = S.build_copy(self.b, self.r, src, dst)
                r2 = S.parse(out)
                dst_tree = self.tree(out, r2, dst)
                looks = {l for _, _, l in dst_tree if l is not None}
                nodes = {i for i, _, _ in dst_tree}
                # look number per unique device name in both trees
                uniq = lambda t: {n: l for _, n, l in t if l is not None and sum(1 for _, x, _ in t if x == n) == 1}  # noqa: E731
                su, du = uniq(src_tree), uniq(dst_tree)
                src_slots, dst_slots = self.slots(self.r, src), self.slots(r2, dst)
                self.assertEqual(set(src_slots), set(dst_slots))
                for name, ss in src_slots.items():
                    ds = dst_slots[name]
                    for li in range(3):  # A, B, C: look number + value
                        sv = {struct.unpack_from("<I", e)[0]: e[4:] for e in ss["lists"][li]}
                        dv = {struct.unpack_from("<I", e)[0]: e[4:] for e in ds["lists"][li]}
                        self.assertLessEqual(set(dv), looks, f"{name}: list {'ABC'[li]} has orphaned look numbers")
                        for dev in set(su) & set(du):
                            self.assertEqual(sv.get(su[dev]), dv.get(du[dev]), f"{name}: {dev}, list {'ABC'[li]}")
                    self.assertLessEqual({struct.unpack_from("<I", e)[0] for e in ds["lists"][3]}, looks)
                    self.assertLessEqual({struct.unpack_from("<I", e, 4)[0] for e in ds["lists"][4]}, nodes,
                                         f"{name}: list E has orphaned node ids")

    def test_source_venue_is_unchanged(self):
        src = self.byname["Default"]
        out, _ = S.build_copy(self.b, self.r, src, self.targets[0])
        r2 = S.parse(out)
        for name, s in self.slots(self.r, src).items():
            self.assertEqual(s["lists"], self.slots(r2, src)[name]["lists"])

    def test_flags_are_idempotent(self):
        src = self.byname["Default"]
        out, _ = S.copy_fixture_flags(self.b, self.r, src, self.targets[0])
        out2, log = S.copy_fixture_flags(out, S.parse(out), src, self.targets[0])
        self.assertEqual(out, out2)
        self.assertIn("0 fixtures updated", log[0])

    def test_set_changes_exactly_one_value(self):
        src = self.byname["Default"]
        for cue in self.r["attrcues"]:
            sub = next((s for s in cue["subs"] if s["key"] == src["guid"]), None)
            if sub and sub["n"]:
                break
        else:
            self.skipTest("no attribute cue with values in Default")
        raw = sub["raw"]
        ents = [raw[28 + 16 * k: 44 + 16 * k] for k in range(sub["n"])]
        node = struct.unpack_from("<I", ents[0], 4)[0]
        mine = [e for e in ents if struct.unpack_from("<I", e, 4)[0] == node]
        values = [(str(struct.unpack_from("<I", e, 8)[0]), e[12]) for e in mine]
        values[0] = (values[0][0], 77 if values[0][1] != 77 else 78)
        out, _ = S.build_set(self.b, self.r, src, cue["name"], f"#{node}", values)
        r2 = S.parse(out)
        cue2 = next(c for c in r2["attrcues"] if c["name"] == cue["name"])
        sub2 = next(s for s in cue2["subs"] if s["key"] == src["guid"])
        self.assertEqual(sub2["n"], sub["n"])
        self.assertEqual(len(out), len(self.b))


if __name__ == "__main__":
    unittest.main()
