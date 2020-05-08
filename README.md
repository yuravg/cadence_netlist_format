# Overview

Format Cadence Allegro Net-List (cnl - Cadence Net-List) to readable file

Output example:

```
...
+24V C7 2 L1 3 FU1 1 C19 2 Z6 1
CLK DD68 40 DD76 42
RESET X1 29 R64 1 R131 8
...
```

# Install

install release or install from source

## Install release

- download latest [release](https://github.com/yuravg/cadence_netlist_format/releases)

- install `pip install dist/cadence_netlist_format-<versoin>.whl`

## Build and install from source

- Download source

- Build

to build the Python package you need to run

`make build`

- Install

to install python package:

`make install`

or

`pip install dist/cadence_netlist_format-<versoin>.whl`

# Usage

run at the command prompt:

`cnl_format`
