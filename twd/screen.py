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


def draw_hr(stdscr, y, mode=None):
    _, max_cols = stdscr.getmaxyx()
    mode = mode if mode is not None else curses.A_NORMAL
    stdscr.addstr(y, 1, "─" * (max_cols - 2), mode)


def filter_dirs_by_search(query):
    global filtered_DIRS
    filtered_DIRS = (
        {k: v for k, v in DIRS.items() if query.lower() in v["alias"].lower()}
        if query
        else DIRS
    )


def display_select_screen(stdscr):
    global search_query, filtered_DIRS, original_DIRS
    selected_entry = 0
    pre_selected_path = None
    confirm_mode = False
    action = None
    search_mode = False
    post_search_mode = False

    running = True

    while running:
        max_items = len(filtered_DIRS)
        stdscr.clear()

        # Border setup
        height, width = stdscr.getmaxyx()
        stdscr.addstr(0, 0, "╭")
        stdscr.addstr(0, 1, "─" * (width - 2))
        stdscr.addstr(0, width - 1, "╮")
        stdscr.addstr(height - 1, 0, "╰")
        stdscr.addstr(height - 1, 1, "─" * (width - 2))
        stdscr.addstr(height - 2, width - 1, "╯")
        for i in range(1, height - 1):
            stdscr.addstr(i, 0, "│")
            stdscr.addstr(i, width - 1, "│")

        inner_height = height - 2
        inner_width = width - 2
        stdscr.addstr(1, 1, f"Current directory: {os.getcwd()}")

        draw_hr(stdscr, 2)

        # Header
        max_alias_len = max(
            max(len(entry["alias"]) for entry in filtered_DIRS.values()), 5
        )
        max_path_len = max(
            max(len(entry["path"]) for entry in filtered_DIRS.values()), 4
        )
        max_id_len = max(max(len(alias_id) for alias_id in filtered_DIRS.keys()), 2)

        alias_col = max_alias_len + 2
        id_col = max_id_len + 2
        path_col = max_path_len

        header_text = f"{'ALIAS'.ljust(alias_col)}{'ID'.ljust(id_col)}{'PATH'.ljust(path_col)}  CREATED AT"
        stdscr.addstr(3, 1, header_text[:inner_width])

        draw_hr(stdscr, 4)

        # List entries
        line_start = 5
        for entry_id, entry in enumerate(filtered_DIRS.values()):
            if line_start >= inner_height - 5:
                break
            alias = entry["alias"].ljust(max_alias_len)
            path = entry["path"].ljust(max_path_len)
            alias_id = list(filtered_DIRS.keys())[entry_id].ljust(max_id_len)
            created_at = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(entry["created_at"])
            )

            line_text = f"{alias}  {alias_id}  {path}  {created_at}"
            if entry_id == selected_entry:
                stdscr.addstr(line_start, 1, line_text[:inner_width], curses.A_REVERSE)
                pre_selected_path = entry["path"]
            else:
                stdscr.addstr(line_start, 1, line_text[:inner_width])

            line_start += 1

        # Controls
        controls_y = height - 5
        draw_hr(stdscr, controls_y, curses.A_DIM)
        controls_text = (
            "ctrls: enter=select"
            if search_mode
            else "ctrls: ↑/k=up  ↓/j=down  enter=select  d/backspace=delete  q=exit search  s=search"
            if post_search_mode
            else "ctrls: ↑/k=up  ↓/j=down  enter=select  d/backspace=delete  q=quit  s=search"
        )
        stdscr.addstr(controls_y + 1, 1, controls_text, curses.A_DIM)

        # Action area
        action_area_y = height - 3
        draw_hr(stdscr, action_area_y)

        if search_mode:
            stdscr.addstr(action_area_y + 1, 1, f"Search: {search_query}")
        elif confirm_mode and action == "delete":
            entry = filtered_DIRS[list(filtered_DIRS.keys())[selected_entry]]
            stdscr.addstr(
                action_area_y + 1,
                1,
                f"Delete entry '{entry['alias']}' ({entry['path']})? [enter/q]",
            )
        elif pre_selected_path:
            stdscr.addstr(
                action_area_y + 1,
                1,
                f"Command: cd {os.path.abspath(os.path.expanduser(pre_selected_path))}",
            )

        stdscr.refresh()

        # Handle key events
        key = stdscr.getch()

        if search_mode:
            if key == ord("\n"):
                search_mode = False
                post_search_mode = True
            elif key == curses.KEY_BACKSPACE or key == 127:
                search_query = search_query[:-1]
                filter_dirs_by_search(search_query)
            else:
                search_query += chr(key)
                filter_dirs_by_search(search_query)
        elif post_search_mode:
            if key == ord("q") or key == 27:  # 'q' or 'esc'
                filtered_DIRS = original_DIRS
                post_search_mode = False
            elif key == curses.KEY_UP or key == ord("k"):
                selected_entry = max(0, selected_entry - 1)
            elif key == curses.KEY_DOWN or key == ord("j"):
                selected_entry = min(max_items - 1, selected_entry + 1)
            elif key == ord("\n"):
                selected_entry_id = list(filtered_DIRS.keys())[selected_entry]
                return filtered_DIRS[selected_entry_id]
        elif confirm_mode:
            if key == ord("\n") and action == "delete":
                selected_entry_id = list(filtered_DIRS.keys())[selected_entry]
                data = crud.load_data(CONFIG)
                try:
                    crud.delete_entry(CONFIG, data, selected_entry_id)
                except KeyError:
                    error_log.error(f"Entry ID {selected_entry_id} not found")
                del filtered_DIRS[selected_entry_id]
                if selected_entry >= len(filtered_DIRS):
                    selected_entry = max(len(filtered_DIRS) - 1, 0)
                confirm_mode = False
            else:
                confirm_mode = False
        else:
            if key == curses.KEY_UP or key == ord("k"):
                selected_entry = (selected_entry - 1) % max_items
            elif key == curses.KEY_DOWN or key == ord("j"):
                selected_entry = (selected_entry + 1) % max_items
            elif key == ord("\n"):
                selected_entry_id = list(filtered_DIRS.keys())[selected_entry]
                return filtered_DIRS[selected_entry_id]
            elif key == ord("q"):
                return None
            elif key == ord("d") or key == curses.KEY_BACKSPACE:
                confirm_mode = True
                action = "delete"
            elif key == ord("s"):
                search_mode = True
                selected_entry = 0


def display_select(config, dirs):
    global CONFIG, DIRS, filtered_DIRS, search_query, original_DIRS
    CONFIG = config
    DIRS = dirs
    filtered_DIRS = DIRS
    original_DIRS = DIRS
    search_query = ""
    return curses.wrapper(display_select_screen)
