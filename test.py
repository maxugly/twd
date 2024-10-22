from curses import wrapper


def main(screen):
    screen.clear()

    screen.addstr(0, 0, "Hi :)")

    screen.refresh()

    screen.getch()


wrapper(main)
