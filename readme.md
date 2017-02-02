# i3-workspacesgrid
A(n other) gridded workspace manager for the [i3 Window Manager](https://i3wm.org/)

## Beta version !

As the core functionallity is working (moving to workspaces, move-container-to-workspace), all of this is not totaly user-friendly.
Configuration may be updated soon.

## Installation

  - install [i3ipc-python](https://github.com/acrisci/i3ipc-python) (`pip install i3ipc`)
  - download this files to anywhere you want in your system
  - copy (or move) `i3-workspacesgrid.ini.tpl` to `i3-workspacesgrid.ini`
  - edit `i3-workspacesgrid.ini` to match your needs
  - run `i3-grid.py print-i3-conf` and copy/paste outputed lines to your i3 config file
  - restart i3 inplace (`$mod+Shift+r` by default)

(do not move the program then, or run `i3-grid.py print-i3-conf` again and replace generated lines)

## TODO

  - display a nice fullscreen grid overlay showing workspaces when jumping
  - remove ini file to pass all conf by arguments ? After all, this is not intended to be called manually, and all i3 conf stuff should be on i3 conf file
