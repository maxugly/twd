import os
import argparse
import sys
from importlib.metadata import version, PackageNotFoundError

TWD_FILE = os.path.join(os.path.expanduser("~"), ".twd")

def get_absolute_path(path):
    return os.path.abspath(path)

def save_directory(path=None):
    if path is None:
        path = os.getcwd()
    else:
        path = get_absolute_path(path)

    with open(TWD_FILE, "w") as f:
        f.write(path)

    print(f"Saved TWD to {path}")

def load_directory():
    if not os.path.exists(TWD_FILE):
        return None
    
    with open(TWD_FILE, "r") as f:
        return f.read().strip()

def go_to_directory():
    TWD = load_directory()
    
    if TWD is None:
        print("No TWD found")
        return 1
    else:
        if os.path.exists(TWD):
            print(f"cd {TWD}")
            return 0
        else:
            print(f"Directory does not exist: {TWD}")
            return 1

def show_directory():
    TWD = load_directory()
    
    if TWD is None:
        print("No TWD set")
    else:
        print(f"Current TWD: {TWD}")

def get_package_version():
    try:
        return version("twd_m4sc0")
    except PackageNotFoundError:
        return "Unknown version"

def main():
    parser = argparse.ArgumentParser(description="Temporarily save and navigate to working directories.")
    
    parser.add_argument('-s', '--save', nargs='?', const='', help="Save the current or specified directory")
    parser.add_argument('-g', '--go', action='store_true', help="Go to the saved directory")
    parser.add_argument('-l', '--list', action='store_true', help="Show saved TWD")
    parser.add_argument('--shell', action='store_true', help="Output shell function for integration")
    parser.add_argument('-v', '--version', action='version', version=f'TWD Version: {get_package_version()}', help='Show the current version of TWD installed')

    args = parser.parse_args()

    if args.shell:
        print('''
        function twd() {
            output=$(python3 -m twd "$@")
            if [[ "$1" == "-g" ]]; then
                eval "$output"
            else {
                echo "$output"
            fi
        }
        ''')
        return 0

    if args.save is not None:
        save_directory(args.save if args.save else None)
    elif args.go:
        return go_to_directory()
    elif args.list:
        show_directory()
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
