# twd-m4sc0

`twd-m4sc0` is a command-line tool that allows you to temporarily save a working directory and easily navigate back to it. It's designed for developers and all users who frequently need to switch between directories in the terminal.

## Features

- Save the current working directory.
- Go back to the saved directory.
- List the saved directory.
- Integrates with your shell for seamless directory management.

## Installation

### Installation using `pip`:

1. Install the package from the `pypi` repository:

```bash
pip install twd-m4sc0
```

2. Add the following line to your `.bashrc` or `.zshrc` to set up the shell function:

```bash
eval $(python3 -m twd --shell)
```

3. Exit and reopen the terminal or reload using:

```bash
source ~/.bashrc
# or
source ~/.zshrc
```

## Usage

- Save a directory

```bash
twd -s [path]
```

- Go to the saved directory

```bash
twd -g
```

- List the saved directory

```bash
twd -l
```

- Unset the TWD and delete the file

```bash
twd -u
```

### Optional Parameters

#### Simple Output

Simpler output is meant to be for script or grep usage

- Example with simple-output

```bash
user:~/.config $ twd -s --simple-output
/home/user/.config
```

- Example without simple-output

```bash
user:~/.config $ twd -s
Saved TWD to /home/user/.config
```

#### No Output

No output is meant for just no output (impressive ik)

- Example with no-output

```bash
user:~/.config $ twd -s --no-output
# no output
```

- Example without no-output

```bash
user:~/.config $ twd -s
Saved TWD to /home/user/.config
```

#### Force

Forces an action

> Currently only implemented on the `-u` flag

- Example

```bash
user:~/.config $ twd -u --force
TWD File deleted and TWD unset
```

# Contribution

To set up a dev environment:

1. Clone the repo:

```bash
git clone https://github.com/m4sc0/twd
cd twd
```

2. Install the package in editable mode using `pip`:

```bash
pip install -e .
```
