# ssvenues - copy SoundSwitch venues completely

When you copy a venue in SoundSwitch with the **+** button, only the fixtures come along. Everything you built on top of them is gone in the copy:

- static looks
- position presets
- attribute cues
- the fixture type (every fixture is reset to "Wash (Primary)") and the group assignment

`ssvenues.py` copies all of that from one venue to another, so you can keep one venue per light rig without rebuilding anything by hand.

- **macOS only.** Tested with SoundSwitch 2.11. Other versions are untested and may not work.
- One file, no installation, no extra libraries. Needs Python 3 (already on most Macs).
- Safe by default: it shows what it would do and only changes anything when you add `--write`. A backup is made before every change.
- Everything happens on your Mac. Nothing is sent anywhere.

> **Use at your own risk.** This is a free hobby tool without any warranty (see [LICENSE](LICENSE)). It edits an undocumented file that was reverse engineered, and it was tested on one person's project only. **Make your own backup first** (step 0 below).

## Quick start

### 0. Make a backup

Quit SoundSwitch. In Finder open **Music > SoundSwitch** and copy your project folder (for example `MyProject.ssproj`) to a safe place. Projects can be large. If you are short on space, copy at least the file `SoundSwitchVenues.bin` inside it. That is the only file this tool touches.

### 1. Copy the venue in SoundSwitch

Copy the venue you want to use as a template with the **+** button and give the copy a name, for example `Club Setup`. Save and **quit SoundSwitch**. You can remove fixtures from the new venue before or after running the tool.

### 2. Download the tool

On the GitHub page click **Code > Download ZIP** and unzip it, for example on your Desktop.

### 3. Open Terminal in that folder

1. Open **Terminal** (press Cmd+Space, type "Terminal", press Enter).
2. Type `cd` followed by a space. Do not press Enter yet.
3. Drag the unzipped folder from Finder into the Terminal window and press Enter.

Check that Python is there:

```bash
python3 --version
```

If macOS offers to install the "command line developer tools", accept and run the command again afterwards.

### 4. Look at your venues

```bash
python3 ssvenues.py info
```

This lists your venues, position presets, static looks and attribute cues. Nothing is changed.

If it says **several SoundSwitch projects found**, tell it which one to use. Replace `MyProject` with the name of your project folder:

```bash
python3 ssvenues.py info --file ~/Music/SoundSwitch/MyProject.ssproj
```

Add the same `--file ...` part to every command below.

### 5. Do a dry run

Venue names are case sensitive. Put names that contain spaces in quotes.

```bash
python3 ssvenues.py copy "Default" "Club Setup"
```

You will see what would be copied and which devices exist only in one of the two venues. At the end it says **Dry run - nothing was written.**

### 6. Copy for real

Make sure SoundSwitch is closed, then run the same command with `--write`:

```bash
python3 ssvenues.py copy "Default" "Club Setup" --write
```

A backup of the project file is created next to it, for example `SoundSwitchVenues.bin.2026-10-03_101500.bak`.

### 7. Check the result in SoundSwitch

Open SoundSwitch, switch to the new venue, and check a few static looks, positions and cues. In the fixture list the type (for example "Multi Cell (Primary)") and the groups should match the source venue.

You can run the copy again at any time. It replaces the looks, positions and cues of the target venue with those of the source.

## What gets copied

| | `copy` |
|---|---|
| Static looks, slots 1-32 | yes |
| Position presets | yes |
| Attribute cues | yes |
| Fixture type (Wash, Multi Cell, ...) and groups | yes |
| Fixture colours in the device list | no |
| Looks in slots 33-128 | no |
| Anything not listed here | not examined, not copied |

Fixtures are matched by name and order in the device tree. The target may have fewer fixtures than the source. Values for fixtures that exist only in the source are skipped, and the tool tells you which. If you have several fixtures with exactly the same name, keep them in the same order as in the source venue.

## All commands

| Command | What it does |
|---|---|
| `info` | Overview of venues, position presets, static looks and attribute cues |
| `fixtures "<venue>"` | Fixtures of a venue with DMX address, type and groups |
| `copy "<source>" "<target>"` | Copy everything listed above |
| `flags "<source>" "<target>"` | Copy only fixture type and groups |
| `set "<venue>" "<cue>" "<device>" "Attribute=Value"` | Change values of one device in an attribute cue (advanced) |

Options:

| Option | Meaning |
|---|---|
| `--write` | Really change the file. Without it every command is a dry run. |
| `--file PATH` | Use this project (`.ssproj` folder or `SoundSwitchVenues.bin`) instead of the one found automatically |
| `--ignore-running` | Do not check whether SoundSwitch is running |
| `--help`, `--version` | Help and version |

### Advanced: set attribute values

```bash
python3 ssvenues.py set "Default" "Gobo Beam" "Blazor" "Gobo=10" "Gobo Rotation=60" --write
```

Values are DMX values from 0 to 255. Existing values of that device in the cue are replaced, other devices are left alone. Use `"#<node number>"` instead of a name for devices that share a name, and the SoundSwitch attribute number instead of a name (`"8=160"`) when the name is not found.

## Restoring a backup

Quit SoundSwitch. In the project folder rename the current `SoundSwitchVenues.bin` (for example to `SoundSwitchVenues.bin.broken`) and rename the backup you want, for example `SoundSwitchVenues.bin.2026-10-03_101500.bak`, to `SoundSwitchVenues.bin`. Old `.bak` files can be deleted once you are happy.

## Troubleshooting

| Message or problem | What to do |
|---|---|
| `command not found: python3` | Install Python 3 from python.org, or accept the developer tools prompt in Terminal. |
| `can't open file ... ssvenues.py` | Terminal is not in the tool's folder. Repeat step 3. |
| `several SoundSwitch projects found` | Add `--file ~/Music/SoundSwitch/MyProject.ssproj`. |
| `no SoundSwitch project found` | Your project is somewhere else. Add `--file` with its path. |
| `venue '...' not found` | Check spelling and capitalisation against the `info` output. Use quotes. |
| `SoundSwitch seems to be running` | Quit SoundSwitch completely, then run the command again. |
| `cannot read ... file format may differ` | Your SoundSwitch version writes a different format. Please open an issue. |
| `WARNING: only ... devices ... have a counterpart` | The fixture names differ between the two venues, for example because fixtures were renamed or deleted and added again in one of them. Give the fixtures the same names in both venues and run it again. |
| Looks are on the wrong fixtures | Restore the backup and open an issue with the output of `info`. |

## How it works

SoundSwitch stores all venues in one binary file, `SoundSwitchVenues.bin`. On duplication it renumbers the devices of the copy, but the looks, positions and cues refer to devices by those numbers. The tool matches the devices of both venues by name, translates the numbers, and writes the result back. The file layout is described in [docs/file-format.md](docs/file-format.md).

## Contributing

Bug reports and improvements are welcome, see [CONTRIBUTING.md](CONTRIBUTING.md). If it works (or not) with another SoundSwitch version, please let me know in an issue.

## License and disclaimer

[MIT](LICENSE). This project is not affiliated with or endorsed by the makers of SoundSwitch. SoundSwitch is a trademark of its respective owner. The file format was worked out by looking at files of the author's own installation.
