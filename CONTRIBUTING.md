# Contributing

Bug reports and pull requests are welcome. This is a hobby project, so replies may take a few days.

## Reporting a problem

Open an issue and include:

- your SoundSwitch version and macOS version
- the exact command you ran and everything it printed
- the output of `python3 ssvenues.py info` (it only contains venue, look and cue names)

Please do not attach your whole project folder. If a `SoundSwitchVenues.bin` helps to reproduce the problem, say so and we will find a way to share it.

## Development

No dependencies, only Python 3.9 or newer.

```bash
python3 -m unittest discover -s tests -v
```

Most tests need no SoundSwitch data. The tests against a real file are skipped unless you point them at one (read only, nothing is written):

```bash
SSVENUES_BIN=~/Music/SoundSwitch/YourProject.ssproj python3 -m unittest discover -s tests -v
```

Guidelines:

- Keep it a single file without third-party packages, so that beginners can just download and run it.
- Never write to the project file without a backup, and keep the dry run as the default.
- New findings about the file format go into `docs/file-format.md`.
- Add a test for every bug you fix.
