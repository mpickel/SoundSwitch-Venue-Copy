# Changelog

## 1.0.0 - 2026-10-03

First release.

- `copy` copies static looks (slots 1-32), position presets, attribute cues, fixture type and groups from one venue to another.
- The target venue may have fewer fixtures than the source. Fixtures are matched by name and order in the device tree.
- `flags` copies only fixture type and groups, `fixtures` lists them, `set` changes single attribute values in a cue, `info` gives an overview.
- Dry run by default, timestamped backup before every write, refuses to write when it detects a running SoundSwitch.
- The project file is found automatically in `~/Music/SoundSwitch`.
- Fixed before release: static looks were copied without translating the per-venue device numbers, so values ended up on the wrong fixtures.
