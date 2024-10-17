# Changelog for the TWD Project

All changes to this project are documented in this file starting at v1.5.3

## [v1.5.3] / 2024-10-17

### Added

- `-g` can now be used with an alias to ensure multiple TWD's are also accessible
- Introduced new log files
- Logging to said log files is supported

### Changed

- Improved overall output
- Fixed issue where all commands would create the `.twd` in the current directory, not the intended user directory
- Aliases are now validated -> can only contain chars, dashes and underscores
