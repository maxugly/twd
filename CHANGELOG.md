# Changelog for the TWD Project

All changes to this project are documented in this file starting at v1.5.3

## v2.0.0 / 2024-10- ##

### Added

- Introduced bash UI for selection process
- `twd -g` can be used with an alias to skip the selection process. That alias can be either the set alias of the TWD entry or the UUID of the entry. Both can be partially entered
- In the UI the user can search for a TWD by using the search function

### Changed

- Fixed shell function for better handling of outputs
- The path that will be `cd` to is now temporarily saved into `/tmp/twd_path`
- `twd` will directly open the selection process
- `twd -g` can be used with an alias for `.sh` scripts or other similar automations or if the user doesn't want to open the UI

---

## v1.5.4 / 2024-10-17

### Added

- Custom command for the whole project

---

## [v1.5.3] / 2024-10-17

### Added

- `-g` can now be used with an alias to ensure multiple TWD's are also accessible
- Introduced new log files
- Logging to said log files is supported

### Changed

- Improved overall output
- Fixed issue where all commands would create the `.twd` in the current directory, not the intended user directory
- Aliases are now validated -> can only contain chars, dashes and underscores
