# Config Docs

This is a little documentation to how the config file in ~/.twd/config is structured, how it works and what you can do with it.

## General Structure

The config file is located at ~/.twd/config because it's the easiest directory to write to as a newly installed program without a lot of permission. The config file location is hard-coded so if that file is moved, the program cannot read from the moved file but instead will create a new one with default values.

The config utilizes JSON for easy read/write using Python's `json` module.

## Entries

- `data_file`

Describes the location of the file that contains the saved `TWD`

Default value: "~/.twd/data"

- `output_behaviour`

Describes the programs output behaviour. Can be overwritten using optional parameters.

Possible values: 0, 1 and 2

0: No output (similar to `--no-output`)
1: Minimal/Simple output (similar to `--simple-output`)
2: Full output

Default value: 2
