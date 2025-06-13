import curses
import time
import os
from . import crud
import logging

# REMOVE any import of 'twd' or 'save_config' from twd.py here.
# We will pass the function directly.

log = logging.getLogger("log")
error_log = logging.getLogger("error")

CONFIG = None
DIRS = None
filtered_DIRS = None
search_query = ""
original_DIRS = None
save_config_function = None # NEW: Global to store the passed function


# Color pair constants
COLOR_DEFAULT = 1
COLOR_BORDER = 2
COLOR_HEADER = 3
COLOR_SELECTED = 4
COLOR_CONTROLS = 5
COLOR_ACTION = 6
COLOR_WARNING = 7
COLOR_ALIAS = 8
COLOR_ID = 9
COLOR_PATH_TEXT = 10
COLOR_PATH_SLASH = 11
COLOR_CREATED_AT = 12

def init_colors():
    """Initialize color pairs for the TUI with a candy theme."""
    curses.start_color()
    curses.use_default_colors()  # Use terminal's default background (black in dark mode)

    if curses.has_colors() and curses.COLORS >= 256:
        # 256-color palette for vibrant candy theme
        curses.init_pair(COLOR_DEFAULT, 252, -1)  # Light gray text
        curses.init_pair(COLOR_BORDER, 46, -1)    # Bright green for borders
        curses.init_pair(COLOR_HEADER, 255, -1)   # Bright white for headers
        curses.init_pair(COLOR_SELECTED, 252, 24) # Light gray on dark blue (unused but kept)
        curses.init_pair(COLOR_CONTROLS, 226, -1) # Bright yellow for controls
        curses.init_pair(COLOR_ACTION, 200, -1)   # Bright magenta for action area
        curses.init_pair(COLOR_WARNING, 196, -1)  # Bright red for warnings
        curses.init_pair(COLOR_ALIAS, 196, -1)    # Bright red for alias
        curses.init_pair(COLOR_ID, 21, -1)        # Bright blue for id
        curses.init_pair(COLOR_PATH_TEXT, 46, -1) # Bright green for path text
        curses.init_pair(COLOR_PATH_SLASH, 226, -1) # Bright yellow for slashes
        curses.init_pair(COLOR_CREATED_AT, 201, -1) # Bright magenta for created date
    else:
        # 16-color palette with bold for brightness
        curses.init_pair(COLOR_DEFAULT, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(COLOR_BORDER, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_HEADER, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(COLOR_SELECTED, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(COLOR_CONTROLS, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(COLOR_ACTION, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(COLOR_WARNING, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(COLOR_ALIAS, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(COLOR_ID, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(COLOR_PATH_TEXT, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_PATH_SLASH, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(COLOR_CREATED_AT, curses.COLOR_MAGENTA, curses.COLOR_BLACK)

def draw_hr(stdscr, y, mode=None):
    """Draw a horizontal rule with bold attribute."""
    _, max_cols = stdscr.getmaxyx()
    mode = mode if mode is not None else curses.color_pair(COLOR_BORDER) | curses.A_BOLD
    stdscr.addstr(y, 1, "─" * (max_cols - 2), mode)

def draw_path(stdscr, y, x, path, max_len, text_color, slash_color, selected=False):
    """Draw the path with different colors for text and slashes."""
    attr = curses.A_REVERSE if selected else 0
    pos = x
    for char in path:
        if pos - x >= max_len:
            break
        if char == '/':
            stdscr.addch(y, pos, char, curses.color_pair(slash_color) | attr | curses.A_BOLD)
        else:
            stdscr.addch(y, pos, char, curses.color_pair(text_color) | attr | curses.A_BOLD)
        pos += 1
    # Pad with spaces if necessary
    while pos - x < max_len:
        stdscr.addch(y, pos, ' ', curses.color_pair(text_color) | attr | curses.A_BOLD)
        pos += 1

def filter_dirs_by_search(query):
    """Filter directories based on search query."""
    global filtered_DIRS
    filtered_DIRS = (
        {k: v for k, v in DIRS.items() if query.lower() in v["alias"].lower()}
        if query
        else DIRS
    )

def display_select_screen(stdscr):
    """Display the selection screen with a candy-themed TUI."""
    global search_query, filtered_DIRS, original_DIRS, CONFIG, save_config_function # Added save_config_function
    init_colors()
    selected_entry = 0
    pre_selected_path = None
    confirm_mode = False
    action = None
    search_mode = False
    post_search_mode = False
    running = True

    # --- Load persistence for column visibility ---
    show_id_column = CONFIG.get('show_id_column', True)
    show_created_column = CONFIG.get('show_created_column', True)
    # --- End persistence loading ---

    while running:
        max_items = len(filtered_DIRS)
        stdscr.clear()

        # Border setup with bold bright colors
        height, width = stdscr.getmaxyx()
        stdscr.addstr(0, 0, "╭", curses.color_pair(COLOR_BORDER) | curses.A_BOLD)
        stdscr.addstr(0, 1, "─" * (width - 2), curses.color_pair(COLOR_BORDER) | curses.A_BOLD)
        stdscr.addstr(0, width - 1, "╮", curses.color_pair(COLOR_BORDER) | curses.A_BOLD)
        stdscr.addstr(height - 1, 0, "╰", curses.color_pair(COLOR_BORDER) | curses.A_BOLD)
        stdscr.addstr(height - 1, 1, "─" * (width - 2), curses.color_pair(COLOR_BORDER) | curses.A_BOLD)
        stdscr.addstr(height - 2, width - 1, "╯", curses.color_pair(COLOR_BORDER) | curses.A_BOLD)
        for i in range(1, height - 1):
            stdscr.addstr(i, 0, "│", curses.color_pair(COLOR_BORDER) | curses.A_BOLD)
            stdscr.addstr(i, width - 1, "│", curses.color_pair(COLOR_BORDER) | curses.A_BOLD)

        inner_height = height - 2
        inner_width = width - 2
        stdscr.addstr(1, 1, f"Current directory: {os.getcwd()}", curses.color_pair(COLOR_DEFAULT) | curses.A_BOLD)

        draw_hr(stdscr, 2)

        # Header
        if not filtered_DIRS:
            max_alias_len = 5
            max_path_len = 4
            max_id_len = 2
        else:
            max_alias_len = max(max(len(entry["alias"]) for entry in filtered_DIRS.values()), 5)
            max_path_len = max(max(len(entry["path"]) for entry in filtered_DIRS.values()), 4)
            max_id_len = max(max(len(alias_id) for alias_id in filtered_DIRS.keys()), 2)

        header_parts = []
        header_parts.append(f"{'ALIAS'.ljust(max_alias_len)}")

        if show_id_column:
            header_parts.append(f"{'ID'.ljust(max_id_len)}")

        header_parts.append(f"{'PATH'.ljust(max_path_len)}")

        if show_created_column:
            header_parts.append("CREATED AT")

        header_text = "  ".join(header_parts)
        stdscr.addstr(3, 1, header_text[:inner_width], curses.color_pair(COLOR_HEADER) | curses.A_BOLD)

        draw_hr(stdscr, 4)

        # List entries with candy-themed colors
        line_start = 5
        if not filtered_DIRS:
            stdscr.addstr(line_start, 1, "No matching directories found.", curses.color_pair(COLOR_WARNING) | curses.A_BOLD)
            selected_entry = 0
            pre_selected_path = None
        else:
            if selected_entry >= max_items:
                selected_entry = max_items - 1
            if selected_entry < 0 and max_items > 0:
                selected_entry = 0

            for entry_id, entry in enumerate(filtered_DIRS.values()):
                if line_start >= inner_height - 5:
                    break
                alias = entry["alias"].ljust(max_alias_len)
                alias_id = list(filtered_DIRS.keys())[entry_id].ljust(max_id_len)
                created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(entry["created_at"]))

                current_x = 1
                attr = curses.A_REVERSE if entry_id == selected_entry else 0

                # Alias
                stdscr.addstr(line_start, current_x, alias, curses.color_pair(COLOR_ALIAS) | attr | curses.A_BOLD)
                current_x += max_alias_len
                stdscr.addstr(line_start, current_x, "  ", curses.color_pair(COLOR_DEFAULT) | attr)
                current_x += 2

                # ID (conditionally displayed)
                if show_id_column:
                    stdscr.addstr(line_start, current_x, alias_id, curses.color_pair(COLOR_ID) | attr | curses.A_BOLD)
                    current_x += max_id_len
                    stdscr.addstr(line_start, current_x, "  ", curses.color_pair(COLOR_DEFAULT) | attr)
                    current_x += 2

                # Path
                draw_path(stdscr, line_start, current_x, entry["path"], max_path_len, COLOR_PATH_TEXT, COLOR_PATH_SLASH, selected=(entry_id == selected_entry))
                current_x += max_path_len
                stdscr.addstr(line_start, current_x, "  ", curses.color_pair(COLOR_DEFAULT) | attr)
                current_x += 2

                # Created At (conditionally displayed)
                if show_created_column:
                    stdscr.addstr(line_start, current_x, created_at, curses.color_pair(COLOR_CREATED_AT) | attr | curses.A_BOLD)

                if entry_id == selected_entry:
                    pre_selected_path = entry["path"]
                line_start += 1


        # Controls with bright colors
        controls_y = height - 5
        draw_hr(stdscr, controls_y)
        controls_text = (
            "ctrls: enter=select"
            if search_mode
            else "ctrls: ↑/k=up  ↓/j=down  enter=select  d/backspace=delete  q=exit search  s=search  n=toggle id  t=toggle created"
            if post_search_mode
            else "ctrls: ↑/k=up  ↓/j=down  enter=select  d/backspace=delete  q=quit  s=search  n=toggle id  t=toggle created"
        )
        stdscr.addstr(controls_y + 1, 1, controls_text, curses.color_pair(COLOR_CONTROLS) | curses.A_BOLD)

        # Action area
        action_area_y = height - 3
        draw_hr(stdscr, action_area_y)

        if search_mode:
            stdscr.addstr(action_area_y + 1, 1, f"Search: {search_query}", curses.color_pair(COLOR_ACTION) | curses.A_BOLD)
        elif confirm_mode and action == "delete":
            entry = filtered_DIRS[list(filtered_DIRS.keys())[selected_entry]]
            stdscr.addstr(
                action_area_y + 1,
                1,
                f"Delete entry '{entry['alias']}' ({entry['path']})? [enter/q]",
                curses.color_pair(COLOR_WARNING) | curses.A_BOLD,
            )
        elif pre_selected_path:
            stdscr.addstr(
                action_area_y + 1,
                1,
                f"Command: cd {os.path.abspath(os.path.expanduser(pre_selected_path))}",
                curses.color_pair(COLOR_ACTION) | curses.A_BOLD,
            )
        else:
            stdscr.addstr(action_area_y + 1, 1, " " * (inner_width - 2), curses.color_pair(COLOR_ACTION) | curses.A_BOLD)


        stdscr.refresh()

        # Handle key events
        key = stdscr.getch()

        # --- Handle column toggles and persistence (ONLY when NOT in search mode) ---
        if not search_mode:  # FIXED: Only handle column toggles when not searching
            if key == ord("n"):
                show_id_column = not show_id_column
                CONFIG['show_id_column'] = show_id_column # Update the global CONFIG dictionary
                if save_config_function: # Call the passed function
                    save_config_function(CONFIG)
                continue
            elif key == ord("t"):
                show_created_column = not show_created_column
                CONFIG['show_created_column'] = show_created_column # Update the global CONFIG dictionary
                if save_config_function: # Call the passed function
                    save_config_function(CONFIG)
                continue
        # --- End handle column toggles and persistence ---

        if key == ord("q") and not search_mode and not post_search_mode:
            return None

        if search_mode:
            if key == ord("\n"):
                search_mode = False
                post_search_mode = True
            elif key == curses.KEY_BACKSPACE or key == 127:
                search_query = search_query[:-1]
                filter_dirs_by_search(search_query)
            else:
                try:
                    search_query += chr(key)
                    filter_dirs_by_search(search_query)
                except ValueError:
                    pass
        elif post_search_mode:
            if key == ord("q") or key == 27:
                filtered_DIRS = original_DIRS
                post_search_mode = False
                search_query = ""
                selected_entry = 0
            elif key == curses.KEY_UP or key == ord("k"):
                if max_items > 0:
                    selected_entry = max(0, selected_entry - 1)
            elif key == curses.KEY_DOWN or key == ord("j"):
                if max_items > 0:
                    selected_entry = min(max_items - 1, selected_entry + 1)
            elif key == ord("\n"):
                if max_items > 0:
                    selected_entry_id = list(filtered_DIRS.keys())[selected_entry]
                    return filtered_DIRS[selected_entry_id]
            elif key == ord("d") or key == curses.KEY_BACKSPACE:
                if max_items > 0:
                    confirm_mode = True
                    action = "delete"
            elif key == ord("s"):
                search_mode = True
                post_search_mode = False
                selected_entry = 0
        elif confirm_mode:
            if key == ord("\n") and action == "delete":
                if max_items > 0:
                    selected_entry_id = list(filtered_DIRS.keys())[selected_entry]
                    # Pass the main CONFIG dictionary to crud functions
                    crud.delete_entry(CONFIG, crud.load_data(CONFIG), selected_entry_id)
                    # Update local filtered_DIRS after deletion
                    del filtered_DIRS[selected_entry_id]
                    if selected_entry >= len(filtered_DIRS) and len(filtered_DIRS) > 0:
                        selected_entry = len(filtered_DIRS) - 1
                    elif len(filtered_DIRS) == 0:
                        selected_entry = 0
                confirm_mode = False
            else:
                confirm_mode = False
        else: # Normal Browse mode
            if key == curses.KEY_UP or key == ord("k"):
                if max_items > 0:
                    selected_entry = (selected_entry - 1) % max_items
            elif key == curses.KEY_DOWN or key == ord("j"):
                if max_items > 0:
                    selected_entry = (selected_entry + 1) % max_items
            elif key == ord("\n"):
                if max_items > 0:
                    selected_entry_id = list(filtered_DIRS.keys())[selected_entry]
                    return filtered_DIRS[selected_entry_id]
            elif key == ord("d") or key == curses.KEY_BACKSPACE:
                if max_items > 0:
                    confirm_mode = True
                    action = "delete"
            elif key == ord("s"):
                search_mode = True
                selected_entry = 0

def display_select(config, dirs, save_config_func): # NEW: Accept save_config_func
    """Wrapper to run the TUI."""
    global CONFIG, DIRS, filtered_DIRS, search_query, original_DIRS, save_config_function
    CONFIG = config
    DIRS = dirs
    filtered_DIRS = DIRS
    original_DIRS = DIRS
    search_query = ""
    save_config_function = save_config_func # Store the passed function in the global
    return curses.wrapper(display_select_screen)
