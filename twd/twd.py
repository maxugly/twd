import os
import argparse

TWD = None  # This will hold the temporary working directory

def get_absolute_path(path):
    return os.path.abspath(path)

def save_directory(path=None):
    global TWD
    if path is None:
        TWD = os.getcwd()
    else:
        TWD = get_absolute_path(path)
    print(f"Saved TWD to {TWD}")

def go_to_directory():
    global TWD
    if TWD is None:
        print("No TWD found")
    else:
        try:
            os.chdir(TWD)
            print(f"Changed to {TWD}")
        except FileNotFoundError:
            print(f"Directory does not exist: {TWD}")

def show_directory():
    global TWD
    if TWD is None:
        print("No TWD set")
    else:
        print(f"Current TWD: {TWD}")

def main():
    # Create the argument parser
    parser = argparse.ArgumentParser(description="Temporarily save and navigate to working directories.")
    
    # Add arguments for saving, going, and listing
    parser.add_argument('-s', '--save', nargs='?', const='', help="Save the current or specified directory")
    parser.add_argument('-g', '--go', action='store_true', help="Go to the saved directory")
    parser.add_argument('-l', '--list', action='store_true', help="Show saved TWD")
    
    # Parse the arguments
    args = parser.parse_args()

    # Handle the arguments
    if args.save is not None:
        # If no argument is provided for save, it defaults to the current directory
        save_directory(args.save if args.save else None)
    elif args.go:
        go_to_directory()
    elif args.list:
        show_directory()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
