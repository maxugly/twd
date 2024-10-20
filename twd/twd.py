import os
import argparse
import json
import hashlib
import time
import re
from importlib.metadata import version, PackageNotFoundError
from .logger import log, error
from .screen import display_select

TWD_DIR = os.path.join(os.path.expanduser("~"), ".twd")
CONFIG_FILE = os.path.join(TWD_DIR, "config")

DEFAULT_CONFIG = {
    "data_file": os.path.expanduser("~/.twd/data"),
    "output_behaviour": 2,
    "log_file": os.path.expanduser("~/.twd/log"),
    "error_file": os.path.expanduser("~/.twd/error"),
    "log_format": "[$T]: $M",
}

# os.makedirs(TWD_DIR, exist_ok=True)


def create_alias_id():
    data = str(time.time()) + str(os.urandom(16))
    return hashlib.sha256(data.encode()).hexdigest()[:12]


def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as file:
            json.dump(DEFAULT_CONFIG, file, indent=4)
        return DEFAULT_CONFIG
    else:
        with open(CONFIG_FILE, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError as e:
                error(f"Error loading config: {e}", DEFAULT_CONFIG)
                return DEFAULT_CONFIG


CONFIG = load_config()

TWD_FILE = os.path.expanduser(CONFIG.get("data_file", "~/.twd/data"))


def ensure_data_file_exists():
    if not os.path.exists(TWD_FILE):
        try:
            with open(TWD_FILE, "w") as f:
                json.dump({}, f)
        except OSError as e:
            error(f"Error creating data file: {e}", CONFIG)

    log_file = os.path.expanduser(CONFIG.get("log_file"))
    error_file = os.path.expanduser(CONFIG.get("error_file"))

    if not os.path.exists(log_file):
        try:
            with open(log_file, "w+") as f:
                f.write("")
        except OSError as e:
            error(f"Error creating log file: {e}", CONFIG)

    if not os.path.exists(error_file):
        try:
            with open(error_file, "w+") as f:
                f.write("")
        except OSError as e:
            error(f"Error creating error file: {e}", CONFIG)


ensure_data_file_exists()


def get_absolute_path(path):
    try:
        return os.path.abspath(path)
    except Exception as e:
        error(f"Error getting absolute path for {path}: {e}", CONFIG)
        raise


def validate_alias(alias):
    """Ensure the alias contains only valid characters."""
    if not re.match(r"^[\w-]+$", alias):
        error(f"Invalid alias provided: {alias}", CONFIG)
        raise ValueError(
            f"Invalid alias: '{alias}'. Aliases can only contain alphanumeric characters, dashes, and underscores."
        )
    return alias


def output_handler(
    message=None, path=None, output=True, simple_output=False, message_type=0
):
    log(f"Type: {message_type}, Msg: {message or path}", CONFIG)

    if CONFIG["output_behaviour"] == 1 or simple_output:
        print("first if")
        if path:
            with open("/tmp/twd_path", "w") as f:
                f.write(path)
            print(path)
    elif CONFIG["output_behaviour"] == 2:
        if path:
            with open("/tmp/twd_path", "w") as f:
                f.write(path)
        print(message)


def save_directory(path=None, alias=None, output=True, simple_output=False):
    if path is None:
        path = os.getcwd()
    else:
        path = get_absolute_path(path)

    if alias:
        alias = validate_alias(alias)

    try:
        with open(TWD_FILE, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        error(f"Error reading TWD file: {e}", CONFIG)
        data = {}

    alias_id = create_alias_id()
    data[alias_id] = {
        "path": path,
        "alias": alias if alias else alias_id,
        "created_at": time.time(),
    }

    try:
        with open(TWD_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except OSError as e:
        error(f"Error writing to TWD file: {e}", CONFIG)
        raise

    output_handler(
        f"Saved TWD to {path} with alias '{alias or alias_id}'",
        path,
        output,
        simple_output,
    )


def load_directory():
    if not os.path.exists(TWD_FILE):
        return None

    try:
        with open(TWD_FILE, "r") as f:
            data = json.load(f)
            if not bool(data):
                return None
            else:
                return data
    except json.JSONDecodeError as e:
        error(f"Error loading TWD file: {e}", CONFIG)
        return None


def show_main(alias=None, output=True, simple_output=False):
    dirs = load_directory()

    if dirs is None:
        output_handler("No TWD found", None, output, simple_output)
        return 1
    else:
        # use alias if provided
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
                    error(
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

        # display selection using curses if alias is not given
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
                error(f"Directory does not exists: {TWD}", CONFIG)
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
    if not os.path.exists(TWD_FILE):
        output_handler("No TWD file found", None, output, simple_output)
    else:
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
            os.remove(TWD_FILE)
        except OSError as e:
            error(f"Error deleting TWD file: {e}", CONFIG)
            raise
        output_handler("TWD File deleted and TWD unset", None, output, simple_output)


def get_package_version():
    try:
        return version("twd_m4sc0")
    except PackageNotFoundError as e:
        error(f"Package version not found: {e}", CONFIG)
        return "Unknown version"


def main():
    global TWD_FILE

    parser = argparse.ArgumentParser(
        description="Temporarily save and navigate to working directories."
    )

    # Positional arguments
    parser.add_argument("directory", nargs="?", help="Directory to save")
    parser.add_argument(
        "alias", nargs="?", help="Alias for the saved directory (optional)"
    )

    # Optional Arguments/Flags
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
        help="Show the current version of TWD installed",
    )
    parser.add_argument("-f", "--force", action="store_true", help="Force an action")
    parser.add_argument(
        "--shell", nargs="?", const="twd", help="Output shell function for integration"
    )
    parser.add_argument(
        "--simple-output",
        action="store_true",
        help="Only print essential output (new directory, absolute path, etc.)",
    )
    parser.add_argument(
        "--no-output",
        action="store_true",
        help="Prevents the console from sending output",
    )
    args = parser.parse_args()

    output = not args.no_output
    simple_output = args.simple_output

    # Shell function
    if args.shell:
        print(rf"""
        function {args.shell}() {{
            python3 -m twd "$@"
            if [[ -f /tmp/twd_path ]]; then
                cd "$(cat /tmp/twd_path)"
                /bin/rm -f /tmp/twd_path
            fi
        }}
        """)
        return 0

    directory = args.directory or args.dir
    alias = args.alias or args.ali

    if args.save:
        if not directory:
            directory = args.directory or os.getcwd()

        alias = args.alias or args.ali

        save_directory(directory, alias, output, simple_output)
    elif args.go:
        alias = args.go
        return show_main(alias, output, simple_output)
    elif args.list:
        show_directory(output, simple_output)
    elif args.unset:
        force = args.force
        unset_directory(output, simple_output, force)
    else:
        show_main(None, output, simple_output)
        return 1
