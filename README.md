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
eval $(twd --shell)
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

### Optional Parameters

#### Simple Output

Simpler output is meant to be for script usage

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
