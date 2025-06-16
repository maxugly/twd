import curses
import time
import os
from . import crud
import logging

log = logging.getLogger("log")
error_log = logging.getLogger("error")

CONFIG = None
DIRS = None
filtered_DIRS = None
search_query = ""
original_DIRS = None

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
COLOR_SIZE_READOUT = 13  # Bright orange for size readout

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
        curses.init_pair(COLOR_SIZE_READOUT, 208, -1) # Bright orange for size readout
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
        curses.init_pair(COLOR_SIZE_READOUT, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Fallback to yellow

def shorten_path(path, mode):
    """Shorten path based on the selected mode.
    
    Args:
        path: The full path string
        mode: 0 = full, 1 = medium, 2 = short
    
    Returns:
        Shortened path string
    """
    if mode == 0 or not path:
        return path
    
    # Split path into segments
    segments = [seg for seg in path.split('/') if seg]  # Remove empty segments
    
    if len(segments) <= 2:
        return path  # Too short to meaningfully shorten
    
    if mode == 1:  # Medium: keep first 2 and last 2 segments
        if len(segments) <= 4:
            return path
        return '/' + '/'.join(segments[:2]) + '/.../' + '/'.join(segments[-2:])
    
    elif mode == 2:  # Short: keep first 1 and last 1 segment
        if len(segments) <= 2:
            return path
        return '/' + segments[0] + '/.../' + segments[-1]
    
    return path

def draw_hr(stdscr, y, mode=None):
    """Draw a horizontal rule with bold attribute."""
    _, max_cols = stdscr.getmaxyx()
    mode = mode if mode is not None else curses.color_pair(COLOR_BORDER) | curses.A_BOLD
    try:
        stdscr.addstr(y, 1, "─" * (max_cols - 2), mode)
    except curses.error:
        pass  # Ignore errors if the line is too long

def draw_path(stdscr, y, x, path, max_len, text_color, slash_color, selected=False):
    """Draw the path with different colors for text and slashes."""
    _, max_cols = stdscr.getmaxyx()
    attr = curses.A_REVERSE if selected else 0
    pos = x
    # Limit max_len to fit within terminal width
    max_len = min(max_len, max_cols - x - 1)
    for char in path:
        if pos - x >= max_len or pos >= max_cols - 1:
            break
        try:
            if char == '/':
                stdscr.addch(y, pos, char, curses.color_pair(slash_color) | attr | curses.A_BOLD)
            else:
                stdscr.addch(y, pos, char, curses.color_pair(text_color) | attr | curses.A_BOLD)
        except curses.error:
            break  # Stop if we hit a boundary
        pos += 1
    # Pad with spaces if necessary
    while pos - x < max_len and pos < max_cols - 1:
        try:
            stdscr.addch(y, pos, ' ', curses.color_pair(text_color) | attr | curses.A_BOLD)
        except curses.error:
            break
        pos += 1

def filter_dirs_by_search(query):
    """Filter directories based on search query."""
    global filtered_DIRS
    filtered_DIRS = (
        {k: v for k, v in DIRS.items() if query.lower() in v["alias"].lower()}
        if query
        else DIRS
    )

def sort_entries(entries_dict, criteria, descending):
    """Sort entries based on the specified criteria and order."""
    items = list(entries_dict.items())
    
    if criteria == "alias":
        items.sort(key=lambda x: x[1]["alias"].lower(), reverse=descending)
    elif criteria == "id":
        items.sort(key=lambda x: x[0], reverse=descending)
    elif criteria == "path":
        items.sort(key=lambda x: x[1]["path"].lower(), reverse=descending)
    elif criteria == "created":
        items.sort(key=lambda x: x[1]["created_at"], reverse=descending)
    
    return {k: v for k, v in items}

def display_select_screen(stdscr, save_config_func=None):
    """Display the selection screen with a candy-themed TUI."""
    global search_query, filtered_DIRS, original_DIRS
    init_colors()
    # Enable mouse events
    curses.mousemask(curses.BUTTON1_PRESSED)  # Detect left-click
    # Enable resize detection
    curses.resizeterm(*stdscr.getmaxyx())
    stdscr.keypad(True)  # Enable keypad for special keys like KEY_RESIZE
    selected_entry = 0
    pre_selected_path = None
    confirm_mode = False
    action = None
    search_mode = False
    post_search_mode = False
    running = True
    last_resize_time = 0  # Track last resize time for debouncing

    # State variables for column visibility, initialized from CONFIG
    show_id_column = CONFIG.get("show_id_column", True)
    show_created_column = CONFIG.get("show_created_column", True)
    path_display_mode = CONFIG.get("path_display_mode", 0)  # 0=full, 1=medium, 2=short
    
    # Sorting state variables
    sort_criteria = CONFIG.get("sort_criteria", "alias")
    sort_descending = CONFIG.get("sort_descending", False)

    # Sort entries initially
    filtered_DIRS = sort_entries(filtered_DIRS, sort_criteria, sort_descending)

    while running:
        max_items = len(filtered_DIRS)
        stdscr.clear()

        # Border setup with bold bright colors
        height, width = stdscr.getmaxyx()
        try:
            stdscr.addstr(0, 0, "╭", curses.color_pair(COLOR_BORDER) | curses.A_BOLD)
            stdscr.addstr(0, 1, "─" * (width - 2), curses.color_pair(COLOR_BORDER) | curses.A_BOLD)
            stdscr.addstr(0, width - 1, "╮", curses.color_pair(COLOR_BORDER) | curses.A_BOLD)
            stdscr.addstr(height - 1, 0, "╰", curses.color_pair(COLOR_BORDER) | curses.A_BOLD)
            stdscr.addstr(height - 1, 1, "─" * (width - 2), curses.color_pair(COLOR_BORDER) | curses.A_BOLD)
            stdscr.addstr(height - 2, width - 1, "╯", curses.color_pair(COLOR_BORDER) | curses.A_BOLD)
            for i in range(1, height - 1):
                stdscr.addstr(i, 0, "│", curses.color_pair(COLOR_BORDER) | curses.A_BOLD)
                stdscr.addstr(i, width - 1, "│", curses.color_pair(COLOR_BORDER) | curses.A_BOLD)
        except curses.error:
            pass  # Ignore boundary errors

        inner_height = height - 2
        inner_width = width - 2

        # Display current directory and size readout on the same line
        dir_text = f"Current directory: {os.getcwd()}"
        size_text = f"{width}x{height}"
        size_x = width - len(size_text) - 1
        dir_max_len = size_x - 2  # Reserve space for size text and buffer
        try:
            stdscr.addstr(1, 1, dir_text[:dir_max_len], curses.color_pair(COLOR_DEFAULT) | curses.A_BOLD)
            stdscr.addstr(1, size_x, size_text, curses.color_pair(COLOR_SIZE_READOUT) | curses.A_BOLD)
        except curses.error:
            pass

        draw_hr(stdscr, 2)

        # Handle empty filtered_DIRS before calculating max lengths
        if not filtered_DIRS:
            max_alias_len = 5  # Default minimum length
            max_path_len = 4  # Default minimum length
            max_id_len = 2    # Default minimum length
            # Display a message when no results are found
            no_results_msg = "No matching directories found."
            try:
                stdscr.addstr(5, 1, no_results_msg[:inner_width - 1], curses.color_pair(COLOR_WARNING) | curses.A_BOLD)
            except curses.error:
                pass
            # Ensure selected_entry is reset to prevent index errors
            selected_entry = -1  # Indicate nothing is selected
        else:
            max_alias_len = max(max(len(entry["alias"]) for entry in filtered_DIRS.values()), 5)
            max_id_len = max(max(len(alias_id) for alias_id in filtered_DIRS.keys()), 2)
            # Calculate max_path_len based on shortened paths
            shortened_paths = [shorten_path(entry["path"], path_display_mode) for entry in filtered_DIRS.values()]
            max_path_len = max(max(len(path) for path in shortened_paths), 4)
            max_path_len = min(max_path_len, inner_width - max_alias_len - max_id_len - 10)  # Adjust for other columns and padding
            # Ensure selected_entry is within bounds if items were removed
            selected_entry = selected_entry % max_items if max_items > 0 else 0
            if selected_entry == -1 and max_items > 0:
                selected_entry = 0

        # Header
        header_parts = []
        current_header_len = 0

        header_parts.append(f"{'ALIAS'.ljust(max_alias_len)}")
        current_header_len += max_alias_len + 2  # +2 for padding

        if show_id_column:
            header_parts.append(f"{'ID'.ljust(max_id_len)}")
            current_header_len += max_id_len + 2  # +2 for padding

        # Add path display mode indicator to header
        path_modes = ["PATH", "PATH (MED)", "PATH (SHORT)"]
        path_header = path_modes[path_display_mode].ljust(max_path_len)
        header_parts.append(path_header)
        current_header_len += max_path_len + 2  # +2 for padding

        if show_created_column:
            header_parts.append("CREATED AT")

        header_text = "  ".join(header_parts)  # Join with 2 spaces padding
        try:
            stdscr.addstr(3, 1, header_text[:inner_width - 1], curses.color_pair(COLOR_HEADER) | curses.A_BOLD)
        except curses.error:
            pass

        draw_hr(stdscr, 4)

        # List entries with candy-themed colors
        line_start = 5
        entry_rows = {}  # Map row numbers to entry indices for mouse clicks
        if filtered_DIRS:  # Only draw entries if there are any
            for entry_id, entry in enumerate(filtered_DIRS.values()):
                if line_start >= inner_height - 6:  # Adjusted for two-line controls
                    break
                alias = entry["alias"].ljust(max_alias_len)
                alias_id = list(filtered_DIRS.keys())[entry_id].ljust(max_id_len)
                created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(entry["created_at"]))

                current_x = 1
                attr = curses.A_REVERSE if entry_id == selected_entry else 0

                # Alias
                try:
                    stdscr.addstr(line_start, current_x, alias[:inner_width - current_x], curses.color_pair(COLOR_ALIAS) | attr | curses.A_BOLD)
                except curses.error:
                    pass
                current_x += max_alias_len
                try:
                    stdscr.addstr(line_start, current_x, "  ", curses.color_pair(COLOR_DEFAULT) | attr)
                except curses.error:
                    pass
                current_x += 2

                # ID (conditionally displayed)
                if show_id_column:
                    try:
                        stdscr.addstr(line_start, current_x, alias_id[:inner_width - current_x], curses.color_pair(COLOR_ID) | attr | curses.A_BOLD)
                    except curses.error:
                        pass
                    current_x += max_id_len
                    try:
                        stdscr.addstr(line_start, current_x, "  ", curses.color_pair(COLOR_DEFAULT) | attr)
                    except curses.error:
                        pass
                    current_x += 2

                # Path (shortened based on display mode)
                shortened_path = shorten_path(entry["path"], path_display_mode)
                try:
                    draw_path(stdscr, line_start, current_x, shortened_path, max_path_len, COLOR_PATH_TEXT, COLOR_PATH_SLASH, selected=(entry_id == selected_entry))
                except curses.error:
                    pass
                current_x += max_path_len
                try:
                    stdscr.addstr(line_start, current_x, "  ", curses.color_pair(COLOR_DEFAULT) | attr)
                except curses.error:
                    pass
                current_x += 2

                # Created At (conditionally displayed)
                if show_created_column:
                    try:
                        stdscr.addstr(line_start, current_x, created_at[:inner_width - current_x], curses.color_pair(COLOR_CREATED_AT) | attr | curses.A_BOLD)
                    except curses.error:
                        pass

                if entry_id == selected_entry:
                    pre_selected_path = entry["path"]
                # Store the row for mouse click detection
                entry_rows[line_start] = entry_id
                line_start += 1
        else:
            pre_selected_path = None  # No path to pre-select if list is empty

        # Controls with bright colors, split into two lines
        controls_y = height - 7  # Adjusted for three lines
        draw_hr(stdscr, controls_y)
        
        # Sorting status line
        sort_indicator = "↓" if sort_descending else "↑"
        sort_text = f"Sort: {sort_criteria} {sort_indicator} | Path: {path_modes[path_display_mode]} | Cols: "
        sort_text += "id " if show_id_column else ""
        sort_text += "created" if show_created_column else ""
        try:
            stdscr.addstr(controls_y + 1, 1, sort_text[:inner_width - 1], curses.color_pair(COLOR_CONTROLS) | curses.A_BOLD)
        except curses.error:
            pass
        
        if search_mode:
            controls_text = "ctrls: enter=select"
            try:
                stdscr.addstr(controls_y + 2, 1, controls_text[:inner_width - 1], curses.color_pair(COLOR_CONTROLS) | curses.A_BOLD)
            except curses.error:
                pass
            toggle_key_positions = {}  # No toggle keys in search mode
        else:
            controls_text = (
                "ctrls: ↑/k=up  ↓/j=down  enter/click=select  d/backspace=delete\n"
                "q=quit  s=search  n=toggle id  t=toggle created  p=toggle path  o=cycle sort  l=toggle order"
                if not post_search_mode
                else "ctrls: ↑/k=up  ↓/j=down  enter/click=select  d/backspace=delete\n"
                     "q=exit search  s=search  n=toggle id  t=toggle created  p=toggle path  o=cycle sort  l=toggle order"
            )
            # Split controls text into lines and render each
            controls_lines = controls_text.split("\n")
            toggle_key_positions = {}  # Map key to (y, x) for clickable toggles
            for i, line in enumerate(controls_lines):
                try:
                    stdscr.addstr(controls_y + 2 + i, 1, line[:inner_width - 1], curses.color_pair(COLOR_CONTROLS) | curses.A_BOLD)
                except curses.error:
                    pass
                # Track positions of 'n', 't', 'p', 'o', and 'l' for clickable toggles
                for key in ['n', 't', 'p', 'o', 'l']:
                    if key in line:
                        x_pos = line.index(key) + 1  # +1 for x=1 starting position
                        toggle_key_positions[key] = (controls_y + 2 + i, x_pos)

        # Action area
        action_area_y = height - 3
        draw_hr(stdscr, action_area_y)

        if search_mode:
            try:
                stdscr.addstr(action_area_y + 1, 1, f"Search: {search_query}"[:inner_width - 1], curses.color_pair(COLOR_ACTION) | curses.A_BOLD)
            except curses.error:
                pass
        elif confirm_mode and action == "delete":
            entry = filtered_DIRS[list(filtered_DIRS.keys())[selected_entry]]
            delete_msg = f"Delete entry '{entry['alias']}' ({entry['path']})? [enter/q]"
            try:
                stdscr.addstr(action_area_y + 1, 1, delete_msg[:inner_width - 1], curses.color_pair(COLOR_WARNING) | curses.A_BOLD)
            except curses.error:
                pass
        elif pre_selected_path:
            try:
                stdscr.addstr(action_area_y + 1, 1, f"Command: cd {os.path.abspath(os.path.expanduser(pre_selected_path))}"[:inner_width - 1], curses.color_pair(COLOR_ACTION) | curses.A_BOLD)
            except curses.error:
                pass
        else:  # Display help/info when no results and not in other modes
            if not filtered_DIRS and not search_mode and not confirm_mode:
                try:
                    stdscr.addstr(action_area_y + 1, 1, "Type 's' to search or add new entries."[:inner_width - 1], curses.color_pair(COLOR_DEFAULT) | curses.A_BOLD)
                except curses.error:
                    pass

        try:
            stdscr.refresh()
        except curses.error:
            pass

        # Handle key and mouse events
        try:
            key = stdscr.getch()
        except curses.error:
            continue  # Handle interrupted getch (e.g., during resize)

        # Handle resize events with debouncing
        if key == curses.KEY_RESIZE:
            current_time = time.time()
            if current_time - last_resize_time >= 0.1:  # Debounce: 0.1s minimum interval
                last_resize_time = current_time
                try:
                    curses.resizeterm(*stdscr.getmaxyx())
                    stdscr.clear()
                    stdscr.refresh()
                    error_log.debug(f"Resized to {width}x{height}")
                except curses.error:
                    pass
            continue  # Skip to next loop to allow other events

        # Handle mouse events
        if key == curses.KEY_MOUSE:
            try:
                _, x, y, _, state = curses.getmouse()
                if state & curses.BUTTON1_PRESSED:  # Left-click
                    # Check for clicks on toggle keys
                    for toggle_key, (key_y, key_x) in toggle_key_positions.items():
                        if y == key_y and x == key_x and not search_mode and not confirm_mode:
                            if toggle_key == 'n':
                                show_id_column = not show_id_column
                                if save_config_func:
                                    updated_config = CONFIG.copy()
                                    updated_config["show_id_column"] = show_id_column
                                    save_config_func(updated_config)
                            elif toggle_key == 't':
                                show_created_column = not show_created_column
                                if save_config_func:
                                    updated_config = CONFIG.copy()
                                    updated_config["show_created_column"] = show_created_column
                                    save_config_func(updated_config)
                            elif toggle_key == 'p':
                                path_display_mode = (path_display_mode + 1) % 3
                                if save_config_func:
                                    updated_config = CONFIG.copy()
                                    updated_config["path_display_mode"] = path_display_mode
                                    save_config_func(updated_config)
                            elif toggle_key == 'o':
                                # Cycle through sort criteria
                                criteria_options = ["alias", "id", "path", "created"]
                                current_index = criteria_options.index(sort_criteria)
                                sort_criteria = criteria_options[(current_index + 1) % len(criteria_options)]
                                filtered_DIRS = sort_entries(filtered_DIRS, sort_criteria, sort_descending)
                                if save_config_func:
                                    updated_config = CONFIG.copy()
                                    updated_config["sort_criteria"] = sort_criteria
                                    save_config_func(updated_config)
                            elif toggle_key == 'l':
                                # Toggle sort order
                                sort_descending = not sort_descending
                                filtered_DIRS = sort_entries(filtered_DIRS, sort_criteria, sort_descending)
                                if save_config_func:
                                    updated_config = CONFIG.copy()
                                    updated_config["sort_descending"] = sort_descending
                                    save_config_func(updated_config)
                            break
                    # Check for clicks on directory entries
                    if y in entry_rows and max_items > 0 and not search_mode and not confirm_mode:
                        # Update selected entry to highlight it
                        selected_entry = entry_rows[y]
                        # Immediately select the entry (mimic Enter key)
                        selected_entry_id = list(filtered_DIRS.keys())[selected_entry]
                        return filtered_DIRS[selected_entry_id]
            except curses.error:
                pass  # Ignore mouse errors (e.g., invalid mouse event)

        # Before handling specific modes, adjust selected_entry for navigation if list is empty
        if not filtered_DIRS:
            if key == curses.KEY_UP or key == ord("k") or key == curses.KEY_DOWN or key == ord("j"):
                # Ignore navigation keys if there's nothing to navigate
                continue  # Skip to next loop iteration
            if key == ord("\n"):  # Cannot select if no items
                continue

        if search_mode:
            if key == ord("\n"):
                search_mode = False
                post_search_mode = True
            elif key == curses.KEY_BACKSPACE or key == 127:
                search_query = search_query[:-1]
                filter_dirs_by_search(search_query)
                filtered_DIRS = sort_entries(filtered_DIRS, sort_criteria, sort_descending)
            else:
                try:
                    # Prevent adding non-printable characters to search query
                    if 32 <= key <= 126:  # ASCII printable characters
                        search_query += chr(key)
                        filter_dirs_by_search(search_query)
                        filtered_DIRS = sort_entries(filtered_DIRS, sort_criteria, sort_descending)
                except ValueError:
                    pass
        elif post_search_mode:
            if key == ord("q") or key == 27:  # 27 is ESC key
                filtered_DIRS = original_DIRS
                filtered_DIRS = sort_entries(filtered_DIRS, sort_criteria, sort_descending)
                post_search_mode = False
                search_query = ""  # Clear search query on exit
                selected_entry = 0  # Reset selection
            elif key == curses.KEY_UP or key == ord("k"):
                selected_entry = max(0, selected_entry - 1)
            elif key == curses.KEY_DOWN or key == ord("j"):
                selected_entry = min(max_items - 1, selected_entry + 1)
            elif key == ord("\n"):
                if max_items > 0:  # Only return if there's something to select
                    selected_entry_id = list(filtered_DIRS.keys())[selected_entry]
                    return filtered_DIRS[selected_entry_id]
            elif key == ord("n"):
                show_id_column = not show_id_column
                # Save config if save_config_func is provided
                if save_config_func:
                    updated_config = CONFIG.copy()
                    updated_config["show_id_column"] = show_id_column
                    save_config_func(updated_config)
            elif key == ord("t"):
                show_created_column = not show_created_column
                # Save config if save_config_func is provided
                if save_config_func:
                    updated_config = CONFIG.copy()
                    updated_config["show_created_column"] = show_created_column
                    save_config_func(updated_config)
            elif key == ord("p"):
                path_display_mode = (path_display_mode + 1) % 3
                # Save config if save_config_func is provided
                if save_config_func:
                    updated_config = CONFIG.copy()
                    updated_config["path_display_mode"] = path_display_mode
                    save_config_func(updated_config)
            elif key == ord("o"):
                # Cycle through sort criteria
                criteria_options = ["alias", "id", "path", "created"]
                current_index = criteria_options.index(sort_criteria)
                sort_criteria = criteria_options[(current_index + 1) % len(criteria_options)]
                filtered_DIRS = sort_entries(filtered_DIRS, sort_criteria, sort_descending)
                if save_config_func:
                    updated_config = CONFIG.copy()
                    updated_config["sort_criteria"] = sort_criteria
                    save_config_func(updated_config)
            elif key == ord("l"):
                # Toggle sort order
                sort_descending = not sort_descending
                filtered_DIRS = sort_entries(filtered_DIRS, sort_criteria, sort_descending)
                if save_config_func:
                    updated_config = CONFIG.copy()
                    updated_config["sort_descending"] = sort_descending
                    save_config_func(updated_config)
        elif confirm_mode:
            if key == ord("\n") and action == "delete":
                if max_items > 0:  # Ensure there's an item to delete
                    selected_entry_id = list(filtered_DIRS.keys())[selected_entry]
                    data = crud.load_data(CONFIG)
                    try:
                        crud.delete_entry(CONFIG, data, selected_entry_id)
                        del filtered_DIRS[selected_entry_id]
                        # Adjust selected_entry after deletion
                        if selected_entry >= len(filtered_DIRS) and len(filtered_DIRS) > 0:
                            selected_entry = len(filtered_DIRS) - 1
                        elif len(filtered_DIRS) == 0:
                            selected_entry = -1  # No items left
                    except KeyError:
                        error_log.error(f"Entry ID {selected_entry_id} not found during deletion attempt")
                confirm_mode = False
            else:
                confirm_mode = False
        else:  # Normal navigation mode
            if key == curses.KEY_UP or key == ord("k"):
                selected_entry = (selected_entry - 1) % max_items if max_items > 0 else -1
            elif key == curses.KEY_DOWN or key == ord("j"):
                selected_entry = (selected_entry + 1) % max_items if max_items > 0 else -1
            elif key == ord("\n"):
                if max_items > 0:
                    selected_entry_id = list(filtered_DIRS.keys())[selected_entry]
                    return filtered_DIRS[selected_entry_id]
            elif key == ord("q"):
                return None
            elif key == ord("d") or key == curses.KEY_BACKSPACE:
                if max_items > 0:  # Only allow delete if there are items
                    confirm_mode = True
                    action = "delete"
            elif key == ord("s"):
                search_mode = True
                selected_entry = 0  # Reset selection on entering search
                search_query = ""  # Clear previous search query
                filter_dirs_by_search(search_query)  # Reset filtered_DIRS to all
                filtered_DIRS = sort_entries(filtered_DIRS, sort_criteria, sort_descending)
            elif key == ord("n"):
                show_id_column = not show_id_column
                # Save config if save_config_func is provided
                if save_config_func:
                    updated_config = CONFIG.copy()
                    updated_config["show_id_column"] = show_id_column
                    save_config_func(updated_config)
            elif key == ord("t"):
                show_created_column = not show_created_column
                # Save config if save_config_func is provided
                if save_config_func:
                    updated_config = CONFIG.copy()
                    updated_config["show_created_column"] = show_created_column
                    save_config_func(updated_config)
            elif key == ord("p"):
                path_display_mode = (path_display_mode + 1) % 3
                # Save config if save_config_func is provided
                if save_config_func:
                    updated_config = CONFIG.copy()
                    updated_config["path_display_mode"] = path_display_mode
                    save_config_func(updated_config)
            elif key == ord("o"):
                # Cycle through sort criteria
                criteria_options = ["alias", "id", "path", "created"]
                current_index = criteria_options.index(sort_criteria)
                sort_criteria = criteria_options[(current_index + 1) % len(criteria_options)]
                filtered_DIRS = sort_entries(filtered_DIRS, sort_criteria, sort_descending)
                if save_config_func:
                    updated_config = CONFIG.copy()
                    updated_config["sort_criteria"] = sort_criteria
                    save_config_func(updated_config)
            elif key == ord("l"):
                # Toggle sort order
                sort_descending = not sort_descending
                filtered_DIRS = sort_entries(filtered_DIRS, sort_criteria, sort_descending)
                if save_config_func:
                    updated_config = CONFIG.copy()
                    updated_config["sort_descending"] = sort_descending
                    save_config_func(updated_config)

def display_select(config, dirs, save_config_func=None):
    """Wrapper to run the TUI."""
    global CONFIG, DIRS, filtered_DIRS, search_query, original_DIRS
    CONFIG = config
    DIRS = dirs
    filtered_DIRS = DIRS
    original_DIRS = DIRS
    search_query = ""
    return curses.wrapper(display_select_screen, save_config_func)
