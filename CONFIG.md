# Config Docs

This is a little documentation to how the config file in ~/.twd/config is structured, how it works and what you can do with it.

## General Structure

The config file is located at ~/.twd/config because it's the easiest directory to write to as a newly installed program without a lot of permission. The config file location is hard-coded so if that file is moved, the program cannot read from the moved file but instead will create a new one with default values.

The config utilizes JSON for easy read/write using Python's `json` module.

## Entries

- `data_file`

Describes the location of the file that contains the saved `TWD`

Default value: `~/.twd/data`

- `output_behaviour`

Describes the programs output behaviour. Can be overwritten using optional parameters.

Possible values: 0, 1 and 2

0: No output (similar to `--no-output`)
1: Minimal/Simple output (similar to `--simple-output`)
2: Full output

Default value: `2`

- `clear_after_screen`

Describes if the screen should be cleared after exiting the TWD screen

Expects a boolean value i.e. `true` or `false`

Default value: `false`

- `log_file`

Describes where to store logs created by `TWD`

Default value: `~/.twd/log`

- `error_file`

Describes where to store errors that occured during the use of `TWD`

Default value: `~/.twd/error`

- `log_format`

Describes the way logs should be stored in the `log_file` and `error_file`

Possible parameters can be found on the [Logging Official Documentation](https://docs.python.org/3/library/logging.html#logrecord-attributes)

Default value: `%(asctime)s - %(levelname)s - %(message)s`

- `log_level`

Describes the log level to be used while logging

Possible parameters can be found on the [Logging Official Documentation](https://docs.python.org/3/library/logging.html#logging-levels)

Default value: `INFO`

- `log_max_bytes`

Describes the max amount of bytes a log file can have before log rotation hits

Default value: `5242880` = `5 MiB`

- `log_backup_count`

Describtes how many log files log rotation can have at max

Default value: `3`
