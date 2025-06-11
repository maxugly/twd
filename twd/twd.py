import os
import argparse
import json
import time
import re
import logging
import tempfile
from importlib.metadata import version, PackageNotFoundError
from .logger import initialize_logging
from .screen import display_select
from . import crud

log = logging.getLogger("log")
error_log = logging.getLogger("error")

TWD_DIR = os.path.join(os.path.expanduser("~"), ".twd")
CONFIG_FILE = os.path.join(TWD_DIR, "config")

DEFAULT_CONFIG = {
    "data_file": os.path.expanduser("~/.twd/data"),
    "output_behaviour": 2,
    "clear_after_screen": False,
    "log_file": os.path.expanduser("~/.twd/log"),
    "error_file": os.path.expanduser("~/.twd/error"),
    "log_format": "%(asctime)s - %(levelname)s - %(message)s",
    "log_level": "INFO",
    "log_max_bytes": 5 * 1024 * 1024,  # 5 MB log rotation
    "log_backup_count": 3,
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        os.makedirs(TWD_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w") as file:
            json.dump(DEFAULT_CONFIG, file, indent=4)
        return DEFAULT_CONFIG
    else:
        with open(CONFIG_FILE, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError as e:
                error_log.error(f"Error loading config: {e}")
                return DEFAULT_CONFIG


CONFIG = load_config()
initialize_logging(CONFIG)

crud.ensure_data_file_exists(CONFIG)


def ensure_log_error_files():
    """Ensure that log and error files exist based on configuration settings."""
    log_file = os.path.expanduser(CONFIG.get("log_file"))
    error_file = os.path.expanduser(CONFIG.get("error_file"))

    if not os.path.exists(log_file):
        try:
            with open(log_file, "w+") as f:
                f.write("")
        except OSError as e:
            error_log.error(f"Error creating log file: {e}")

    if not os.path.exists(error_file):
        try:
            with open(error_file, "w+") as f:
                f.write("")
        except OSError as e:
            error_log.error(f"Error creating error file: {e}")


ensure_log_error_files()


def get_temp_file_path(suffix):
    """Get a portable temporary file path."""
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, f"twd_{suffix}")


def get_absolute_path(path):
    try:
        return os.path.abspath(path)
    except Exception as e:
        error_log.error(f"Error getting absolute path for {path}: {e}")
        raise


def validate_alias(alias):
    """Ensure the alias contains only valid characters."""
    if not re.match(r"^[\w-]+$", alias):
        error_log.error(f"Invalid alias provided: {alias}")
        raise ValueError(
            f"Invalid alias: '{alias}'. Aliases can only contain alphanumeric characters, dashes, and underscores."
        )
    return alias


def output_handler(
    message=None, path=None, output=True, simple_output=False, message_type=0
):
    log.info(message or path)

    if CONFIG["output_behaviour"] == 1 or simple_output:
        if path:
            twd_path_file = get_temp_file_path("path")
            with open(twd_path_file, "w") as f:
                f.write(path)
            if CONFIG["clear_after_screen"]:
                twd_clear_file = get_temp_file_path("clear")
                with open(twd_clear_file, "w") as f:
                    f.write(path)
            if output:
                print(path)
    elif CONFIG["output_behaviour"] == 2:
        if path:
            twd_path_file = get_temp_file_path("path")
            with open(twd_path_file, "w") as f:
                f.write(path)
            if CONFIG["clear_after_screen"]:
                twd_clear_file = get_temp_file_path("clear")
                with open(twd_clear_file, "w") as f:
                    f.write(path)
        if output:
            print(message)


def save_directory(path=None, alias=None, output=True, simple_output=False):
    if path is None:
        path = os.getcwd()
    else:
        path = get_absolute_path(path)

    if alias:
        alias = validate_alias(alias)

    data = crud.load_data(CONFIG)
    alias_id = crud.create_entry(CONFIG, data, path, alias)

    output_handler(
        f"Saved TWD to {path} with alias '{alias or alias_id}'",
        path,
        output,
        simple_output,
    )


def load_directory():
    data = crud.load_data(CONFIG)
    return data if data else None


def show_main(alias=None, output=True, simple_output=False):
    dirs = load_directory()
    if dirs is None:
        output_handler("No TWD found", None, output, simple_output)
        return 1
    else:
        if alias:
            matched_dirs = []

            for entry_id, entry in dirs.items():
                if (
                    "alias" in entry
                    and entry["alias"]
                    and entry["alias"].startswith(alias)
                ):
                    entry["id"] = entry_id
                    matched_dirs.append(entry)
                elif entry_id.startswith(alias):
                    entry["id"] = entry_id
                    matched_dirs.append(entry)

            if len(matched_dirs) == 1:
                TWD = matched_dirs[0]["path"]
                if os.path.exists(TWD):
                    output_handler(
                        f"cd {TWD}", TWD, output, simple_output, message_type=1
                    )
                    return 0
                else:
                    error_log.error(f"Directory does not exist: {TWD}")
                    output_handler(
                        f"Directory does not exist: {TWD}", None, output, simple_output
                    )
                    return 1
            elif len(matched_dirs) > 1:
                output_handler(
                    f"Multiple TWDs match for '{alias}':", None, output, simple_output
                )
                for match in matched_dirs:
                    output_handler(
                        f"{match['alias']}  {match['id']}  {match['path']}",
                        None,
                        output,
                        simple_output,
                    )
                return 1
            else:
                output_handler("No TWD with alias found", None, output, simple_output)
                return 1

        selected_dir = display_select(CONFIG, dirs)
        if selected_dir is None:
            output_handler("No TWD selected", None, output, simple_output)
            return 0
        else:
            TWD = selected_dir["path"]
            if os.path.exists(TWD):
                output_handler(f"cd {TWD}", TWD, output, simple_output, message_type=1)
                return 0
            else:
                error_log.error(f"Directory does not exist: {TWD}")
                output_handler(
                    f"Directory does not exist: {TWD}", None, output, simple_output
                )
                return 1


def show_directory(output=True, simple_output=False):
    dirs = load_directory()
    if not dirs:
        output_handler("No TWD set", None, output, simple_output)
        return

    max_alias_len = max(len(entry["alias"]) for entry in dirs.values()) if dirs else 0
    max_id_len = max(len(alias_id) for alias_id in dirs.keys()) if dirs else 0
    max_path_len = max(len(entry["path"]) for entry in dirs.values()) if dirs else 0

    header = f"{'Alias'.ljust(max_alias_len)}  {'ID'.ljust(max_id_len)}  {'Path'.ljust(max_path_len)}  Created At"
    print(header)
    print("-" * len(header))

    for alias_id, entry in dirs.items():
        alias = entry["alias"].ljust(max_alias_len)
        path = entry["path"].ljust(max_path_len)
        created_at = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(entry["created_at"])
        )
        alias_id_str = alias_id.ljust(max_id_len)
        output_handler(
            f"{alias}  {alias_id_str}  {path}  {created_at}",
            None,
            output,
            simple_output,
        )


def unset_directory(output=True, simple_output=False, force=False):
    if not force:
        output_handler(
            r"""If you want to execute deleting and therefore unsetting all set TWD's, please use "--force" or "-f" and run again.

This feature is to prevent accidental execution.""",
            None,
            True,
            False,
        )
        return
    try:
        crud.delete_data_file(CONFIG)
    except OSError as e:
        error_log.error(f"Error deleting TWD file: {e}")
        raise
    output_handler("TWD File deleted and TWD unset", None, output, simple_output)


def setup(alias):
    bashrc_path = os.path.expanduser("~/.bashrc")
    alias = "twd" if not alias else alias
    temp_dir = tempfile.gettempdir()
    with open(bashrc_path, "a") as file:
        file.write(f"\neval $(python3 -m twd --shell {alias})\n")
    print("Please execute the following command to activate TWD:")
    print("")
    print(f"source {bashrc_path}")


def get_package_version():
    try:
        return version("twd_m4sc0")
    except PackageNotFoundError as e:
        error_log.error(f"Package version not found: {e}")
        return "Unknown version"


def main():
    parser = argparse.ArgumentParser(
        description="Temporarily save and navigate to working directories."
    )

    parser.add_argument(
        "--setup", nargs="?", const="twd", help="Automatic setup in the .bashrc file"
    )

    parser.add_argument("directory", nargs="?", help="Directory to save")
    parser.add_argument(
        "alias", nargs="?", help="Alias for the saved directory (optional)"
    )
    parser.add_argument(
        "-s",
        "--save",
        action="store_true",
        help="Save the current or specified directory",
    )
    parser.add_argument("-d", "--dir", nargs="?", help="Directory to save")
    parser.add_argument("-a", "--ali", nargs="?", help="Alias for the saved directory")
    parser.add_argument(
        "-g", "--go", nargs="?", const=" ", help="Go to the saved directory"
    )
    parser.add_argument("-l", "--list", action="store_true", help="Show saved TWD")
    parser.add_argument(
        "-u", "--unset", action="store_true", help="Unset the saved TWD"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"TWD Version: v{get_package_version()}",
    )
    parser.add_argument("-f", "--force", action="store_true", help="Force an action")
    parser.add_argument(
        "--shell", nargs="?", const="twd", help="Output shell function for integration"
    )
    parser.add_argument(
        "--simple-output", action="store_true", help="Only print essential output"
    )
    parser.add_argument(
        "--no-output",
        action="store_true",
        help="Prevents the console from sending output",
    )

    args = parser.parse_args()
    output = not args.no_output
    simple_output = args.simple_output

    if args.shell:
        temp_dir = tempfile.gettempdir()
        twd_path_file = os.path.join(temp_dir, "twd_path")
        twd_clear_file = os.path.join(temp_dir, "twd_clear")
        print(rf"""function {args.shell}() {{
            python3 -m twd "$@";
            if [ -f {twd_path_file} ]; then
                cd "$(cat {twd_path_file})";
                /bin/rm -f {twd_path_file};
            fi;
            if [ -f {twd_clear_file} ]; then
                clear;
                /bin/rm -f {twd_clear_file};
            fi;
        }}""")
        return 0

    if args.setup:
        setup(args.setup)
        return 0

    directory = args.directory or args.dir
    alias = args.alias or args.ali

    if args.save:
        save_directory(directory, alias, output, simple_output)
    elif args.go:
        show_main(alias, output, simple_output)
    elif args.list:
        show_directory(output, simple_output)
    elif args.unset:
        unset_directory(output, simple_output, force=args.force)
    else:
        show_main(None, output, simple_output)


if __name__ == "__main__":
    main()
