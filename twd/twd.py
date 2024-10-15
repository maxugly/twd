import os
import argparse
import sys
import json
import hashlib
import time
import re
from importlib.metadata import version, PackageNotFoundError

TWD_DIR = os.path.join(os.path.expanduser("~"), ".twd")
CONFIG_FILE = os.path.join(TWD_DIR, 'config')

DEFAULT_CONFIG = {
    "data_file": "~/.twd/data",
    "output_behaviour": 2
}

os.makedirs(TWD_DIR, exist_ok=True)

def create_alias_id():
    data = str(time.time()) + str(os.urandom(16))
    return hashlib.sha256(data.encode()).hexdigest()[:12]

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as file:
            json.dump(DEFAULT_CONFIG, file, indent=4)
        return DEFAULT_CONFIG
    else:
        with open(CONFIG_FILE, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError as e:
                print(f"Error loading config: {e}")
                return DEFAULT_CONFIG

CONFIG = load_config()

TWD_FILE = os.path.expanduser(CONFIG.get("data_file", "~/.twd/data"))

def ensure_data_file_exists():
    if not os.path.exists(TWD_FILE):
        with open(TWD_FILE, 'w') as f:
            json.dump({}, f)

ensure_data_file_exists()

def get_absolute_path(path):
    return os.path.abspath(path)

def validate_alias(alias):
    """Ensure the alias contains only valid characters."""
    if not re.match(r'^[\w-]+$', alias):
        raise ValueError(f"Invalid alias: '{alias}'. Aliases can only contain alphanumeric characters, dashes, and underscores.")
    return alias

def output_handler(message=None, path=None, output=True, simple_output=False, message_type=0):
    if not output or CONFIG["output_behaviour"] == 0:
        return

    if not message and not path:
        return

    if message_type == 1:
        print(f"1;{message}")
    elif message_type == 0:
        if simple_output and path:
            print(f"0;{path}")
        elif not simple_output and message:
            print(f"0;{message}")

def save_directory(path=None, alias=None, output=True, simple_output=False):
    if path is None:
        path = os.getcwd()
    else:
        path = get_absolute_path(path)

    if alias:
        alias = validate_alias(alias)

    try:
        with open(TWD_FILE, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        data = {}

    alias_id = create_alias_id()
    data[alias_id] = {
        "path": path,
        "alias": alias if alias else alias_id,
        "created_at": time.time()
    }

    with open(TWD_FILE, 'w') as f:
        json.dump(data, f, indent=4)

    output_handler(f"Saved TWD to {path} with alias '{alias or alias_id}'", path, output, simple_output)

def load_directory():
    if not os.path.exists(TWD_FILE):
        return None
    
    with open(TWD_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return None

def go_to_directory(output=True, simple_output=False):
    dirs = load_directory()

    if not dirs:
        output_handler("No TWD found", None, output, simple_output)
        return 1
    else:
        last_alias, last_entry = list(dirs.items())[-1]
        TWD = last_entry['path']

        if os.path.exists(TWD):
            output_handler(f"cd {TWD}", TWD, output, simple_output, message_type=1)
            return 0
        else:
            output_handler(f"Directory does not exist: {TWD}", None, output, simple_output)
            return 1

def show_directory(output=True, simple_output=False):
    dirs = load_directory()

    if not dirs:
        output_handler("No TWD set", None, output, simple_output)
        return

    max_alias_len = max(len(entry['alias']) for entry in dirs.values()) if dirs else 0
    max_id_len = max(len(alias_id) for alias_id in dirs.keys()) if dirs else 0
    max_path_len = max(len(entry['path']) for entry in dirs.values()) if dirs else 0

    header = f"{'Alias'.ljust(max_alias_len)}  {'ID'.ljust(max_id_len)}  {'Path'.ljust(max_path_len)}  Created At"
    print(header)
    print("-" * len(header))

    for alias_id, entry in dirs.items():
        alias = entry['alias'].ljust(max_alias_len)
        path = entry['path'].ljust(max_path_len)
        created_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry['created_at']))
        alias_id_str = alias_id.ljust(max_id_len)
        output_handler(f"{alias}  {alias_id_str}  {path}  {created_at}", None, output, simple_output)


def unset_directory(output=True, simple_output=False, force=False):
    if not os.path.exists(TWD_FILE):
        output_handler(f"No TWD file found", None, output, simple_output)
    else:
        if not force:
            output_handler(r'''If you want to execute deleting and therefore unsetting all set TWD's, please use "--force" or "-f" and run again.
                           

This feature is to prevent accidental execution.''', None, True, False)
            return
        os.remove(TWD_FILE)
        output_handler(f"TWD File deleted and TWD unset", None, output, simple_output)

def get_package_version():
    try:
        return version("twd_m4sc0")
    except PackageNotFoundError:
        return "Unknown version"

def main():
    global TWD_FILE

    parser = argparse.ArgumentParser(description="Temporarily save and navigate to working directories.")

    # Positional arguments
    parser.add_argument('directory', nargs='?', help="Directory to save")
    parser.add_argument('alias', nargs='?', help="Alias for the saved directory (optional)")

    # Optional Arguments/Flags
    parser.add_argument('-s', '--save', action='store_true', help="Save the current or specified directory")
    parser.add_argument('-d', '--directory', help="Directory to save")
    parser.add_argument('-a', '--alias', help="Alias for the saved directory")
    parser.add_argument('-g', '--go', action='store_true', help="Go to the saved directory")
    parser.add_argument('-l', '--list', action='store_true', help="Show saved TWD")
    parser.add_argument('-u', '--unset', action='store_true', help="Unset the saved TWD")
    parser.add_argument('-v', '--version', action='version', version=f'TWD Version: {get_package_version()}', help='Show the current version of TWD installed')
    parser.add_argument('-f', '--force', action='store_true', help="Force an action")
    parser.add_argument('--shell', action='store_true', help="Output shell function for integration")
    parser.add_argument('--simple-output', action='store_true', help="Only print essential output (new directory, absolute path, etc.)")
    parser.add_argument('--no-output', action='store_true', help="Prevents the console from sending output")
    args = parser.parse_args()

    output = not args.no_output
    simple_output = args.simple_output

    if args.shell:
        print(r'''
        function twd() {
            output=$(python3 -m twd "$@");
            while IFS= read -r line; do
                if [[ -z "$line" ]]; then
                    continue;
                fi;
                type=$(echo "$line" | cut -d';' -f1);
                message=$(echo "$line" | cut -d';' -f2-);
                if [[ "$type" == "1" ]]; then
                    eval "$message";
                else
                    echo "$message";
                fi;
            done <<< "$output";
        }
        ''')
        return 0

    directory = args.directory or args.directory
    alias = args.alias or args.alias

    if args.save:
        if not directory:
            directory = args.directory or os.getcwd()

        alias = args.alias or args.alias

        save_directory(directory, alias, output, simple_output)
    elif args.go:
        return go_to_directory(output, simple_output)
    elif args.list:
        show_directory(output, simple_output)
    elif args.unset:
        force = args.force
        unset_directory(output, simple_output, force)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
