# File format: `SoundSwitchVenues.bin` (SoundSwitch 2.11)

Worked out by looking at real files, not officially documented, and incomplete. All numbers are little-endian `u32`. Strings are a `u32` character count including the terminating NUL followed by UTF-16LE. GUIDs are 16 raw bytes.

## Sections in file order

| Section | Content |
|---|---|
| Header | `aaaa0955`, `3`, `offA`, `offB`, `?`, venue count. `offA` points to the tail, `offB = offA + 30`. |
| Venues | One block per venue, starting `04000000 GUID 01000000 name 0f000000 ...` |
| Position presets | `02000000 00000000`, then per preset: `02000000`, n venue entries (`GUID 02000000 n x (node, 1, 8 bytes)`), `01000000 name GUID colour a`; then an order list and 14 bytes |
| Static looks 1-32 | `u32 count`, per venue key: `GUID 01000000 20000000` + 32 slots |
| Attribute cues | `02000000 00000000`, then per cue: `01000000`, n venue entries (`GUID 01 01 n x (1, node, attribute, value)`), `01000000 name GUID colour a`; then an order list |
| Cue groups | Folders for cues. Not decoded, copied unchanged. |
| Looks 33-128 | `u32 count`, per venue key: `GUID 02000000` + 96 slots + 128 x 25 bytes (type 6). Not handled by the tool. |
| End of a fixture record | Every top-level fixture record ends with the profile GUID plus 6 x u32: `hash, mode, DMX address - 1, profile hash, type, groups`. Type: 2 Wash (Primary), 3 Wash (Secondary), 4 Wash (Tertiary), 11 Multi Cell (Primary), 12 Multi Cell (Secondary), other values unknown. Groups: Group 1-4, 0 = none. SoundSwitch resets both when you copy a venue with "+". |
| Tail | 46 bytes, a table `(offset, length, 0, 1)` per fixture record, `ffffffff`, `u32 7`, `"Default"` |

Look slot: `05000000 01000000 name`, then five lists: A `index + double` (12 bytes, intensity), B (12 bytes), C (12 bytes, colour), D `index + GUID` (20 bytes, position preset), E (16 bytes, attribute values).

## Device numbers

Positions and attribute cues refer to **nodes of the device tree of their venue**. A node is `03000000 02000000 <node id> 01000000 <name> ...`. The tree sits in the venue block **behind** the fixture records. Before it come device profiles with similar looking channel entries that do not belong to the tree.

When SoundSwitch copies a venue it assigns new, gap-free node ids. Giving the entries the GUID of the new venue is therefore not enough. The node ids have to be translated from source to copy.

Static looks use a **second numbering** in lists A-D: the *look number* that follows the name of a leaf node in the tree (`<name> <look number> <colour ARGB> ...`). Devices and cells have one, group nodes do not. SoundSwitch assigns these numbers anew per venue as well. Example: the same device had look number 32 in one venue and 30 in its copy. List E of a slot uses node ids like the attribute cues do (`1, node, attribute, value`).

## How the tool matches devices

Source and target trees are aligned by node name using the longest common subsequence. This keeps the order of devices with identical names. Nodes without counterpart stay unmapped: their values are dropped when copying, and nodes that only exist in the target get no values. Fixture records (type, groups) are matched by profile GUID, channel mode and DMX address instead, because the order of records does not matter there.

## Confirmed by comparison

- Same device, venue and its fresh copy: node ids differ, names and order are identical.
- After copying, no look slot refers to a look number or node id that does not exist in the target.
