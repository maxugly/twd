
# twd-m4sc0

`twd-m4sc0` is a command-line tool that allows you to temporarily save a working directory and easily navigate back to it. It's designed for developers and users who frequently need to switch between directories in the terminal.

> All Versions `< v1.5` are considered deprecated and should not be used anymore because of the `config` file that was introduced in that version. This file is incompatible with newer versions and might cause issues or break the program. 

## Features

- Save the current or specified working directory.
- Go back to a saved directory using an optional alias.
- List all saved directories with metadata.
- Unset and delete saved directories.
- Integrates with your shell for seamless directory management.
- Some options can be configured using the `config` file. For more information please visit the [Config](CONFIG.md) documentation.

## Installation

### Installation using `pip`:

1. Install the package from the `pypi` repository:

```bash
pip install twd-m4sc0
```

2. Add the following line to your `.bashrc` or `.zshrc` to set up the shell function:

> Since 1.5.4 you can also set a different command for the `twd` program by replacing `[alias]` in the following code by your custom alias

```bash
eval $(python3 -m twd --shell [alias])
```

3. Exit and reopen the terminal or reload using:

```bash
source ~/.bashrc
# or
source ~/.zshrc
```

## Usage

### Save a directory

- Save the current directory or a specified directory:

```bash
twd -s [path] [alias]
```

If no path is specified, the current directory is saved. The alias is optional, and if not provided, an auto-generated ID will be used.

### Go to a saved directory

- Navigate to a saved directory using an optional alias:

```bash
twd -g [alias]
```

If no alias is provided, the most recently saved directory will be used. If an alias is provided, it will navigate to the directory associated with that alias.

### List saved directories

- Display a list of all saved directories:

```bash
twd -l
```

### Unset the TWD and delete the data file

- Unset and delete the saved directories:

```bash
twd -u
```

You can force this action using the `--force` flag to avoid accidental execution.

```bash
twd -u --force
```

### Optional Parameters

#### Simple Output

For cleaner, minimal output intended for scripting or piping.

- Example with `--simple-output`:

```bash
twd -s --simple-output
/home/user/.config
```

- Example without `--simple-output`:

```bash
Saved TWD to /home/user/.config
```

#### No Output

Suppresses all output (including confirmation messages).

- Example with `--no-output`:

```bash
twd -s --no-output
# No output
```

#### Force

Use the `--force` flag to force certain actions, such as when unsetting directories with the `-u` flag.

- Example:

```bash
twd -u --force
TWD File deleted and TWD unset
```

## Contribution

To set up a development environment:

1. Clone the repository:

```bash
git clone https://github.com/m4sc0/twd
cd twd
```

2. Install the package in editable mode using `pip`:

```bash
pip install -e .
```

3. Make your changes, and contribute!
