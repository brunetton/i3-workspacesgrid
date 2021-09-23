# i3-workspacesgrid
A(nother) gridded workspace manager for the [i3 Window Manager](https://i3wm.org/)

As the core functionallity is working (moving to workspaces, move-container-to-workspace), all of this is not totaly user-friendly.

A graphical feedback should be added.

## Installation

  - install dependencies (`pip install -r requirements.txt`)
  - install `curl` (`apt install curl` in Debian/Ubuntu)
  - download this files to anywhere you want in your system
  - copy (or move) `i3-workspacesgrid.ini.tpl` to `i3-workspacesgrid.ini`
  - edit `i3-workspacesgrid.ini` to match your needs
  - run `i3-grid.py print-i3-conf` and follow instructions (comment given lines / copy/paste outputed lines to your i3 config file)
  - run `i3-grid.py start-server` (and keep that program running)
  - restart i3 (`$mod+Shift+r` by default)

(do not move the program files then, or run `i3-grid.py print-i3-conf` again and replace generated lines)

## TODO

  - display a nice fullscreen grid overlay showing workspaces when jumping
