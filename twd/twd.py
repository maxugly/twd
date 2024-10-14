import os
import argparse
import sys
import json
from importlib.metadata import version, PackageNotFoundError

TWD_DIR = os.path.join(os.path.expanduser("~"), ".twd")
CONFIG_FILE = os.path.join(TWD_DIR, 'config')

DEFAULT_CONFIG = {
    "data_file": "~/.twd/data",
    "output_behaviour": 2
}

os.makedirs(TWD_DIR, exist_ok=True)

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
            f.write("")

ensure_data_file_exists()

def get_absolute_path(path):
    return os.path.abspath(path)

def output_handler(message=None, path=None, output=True, simple_output=False, message_type=0):
    if not output:
        return

    if CONFIG["output_behaviour"] == 0:
        return

    if message_type == 1:
        print(f"1;{message}")
    elif message_type == 0:
        if simple_output and path:
            print(f"0;{path}")
        elif not simple_output and message:
            print(f"0;{message}")

def save_directory(path=None, output=True, simple_output=False):
    if path is None:
        path = os.getcwd()
    else:
        path = get_absolute_path(path)

    with open(TWD_FILE, "w") as f:
        f.write(path)

    output_handler(f"Saved TWD to {path}", path, output, simple_output)

def load_directory():
    if not os.path.exists(TWD_FILE):
        return None
    with open(TWD_FILE, "r") as f:
        return f.read().strip()

def go_to_directory(output=True, simple_output=False):
    TWD = load_directory()

    if TWD is None:
        output_handler("No TWD found", None, output, simple_output)
        return 1
    else:
        if os.path.exists(TWD):
            output_handler(f"cd {TWD}", TWD, output, simple_output, message_type=1)
            return 0
        else:
            output_handler(f"Directory does not exist: {TWD}", None, output, simple_output)
            return 1

def show_directory(output=True, simple_output=False):
    TWD = load_directory()

    if TWD is None:
        output_handler("No TWD set", None, output, simple_output)
    else:
        output_handler(f"Current TWD: {TWD}", TWD, output, simple_output)

def unset_directory(output=True, simple_output=False):
    if not os.path.exists(TWD_FILE):
        output_handler(f"No TWD file found", None, output, simple_output)
    else:
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

    parser.add_argument('-s', '--save', nargs='?', const='', help="Save the current or specified directory")
    parser.add_argument('-g', '--go', action='store_true', help="Go to the saved directory")
    parser.add_argument('-l', '--list', action='store_true', help="Show saved TWD")
    parser.add_argument('-u', '--unset', action='store_true', help="Unset the saved TWD")
    parser.add_argument('-v', '--version', action='version', version=f'TWD Version: {get_package_version()}', help='Show the current version of TWD installed')
    parser.add_argument('--shell', action='store_true', help="Output shell function for integration")
    parser.add_argument('--simple-output', action='store_true', help="Only print essential output (new directory, absolute path, etc.)")
    parser.add_argument('--no-output', action='store_true', help="Prevents the console from sending output")

    args = parser.parse_args()

    output = not args.no_output
    simple_output = args.simple_output

    if args.shell:
        print('''
        function twd() {
            output=$(python3 -m twd "$@"); 
            while IFS= read -r line; do
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

    if args.save is not None:
        save_directory(args.save if args.save else None, output, simple_output)
    elif args.go:
        return go_to_directory(output, simple_output)
    elif args.list:
        show_directory(output, simple_output)
    elif args.unset:
        unset_directory(output, simple_output)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
