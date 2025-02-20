import curses
    
def interface(stdscr):
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True) # Enable special keys
    run = True
    i = 0;

    try:
        stdscr.addstr(0, 0, "User Interface:")
        stdscr.addstr(1, 0, "[esc]: Exit")
        stdscr.addstr(2, 0, "[c]: Does a Circle")
        stdscr.addstr(3, 0, "[s]: Settle and Sit\n")
        stdscr.refresh()
        while run:
            key = stdscr.getch()
            stdscr.addstr(5, 0, f"          ")
            stdscr.addstr(5, 0, f"   {key}")
            if key == ord('p'):
                break
            elif key == ord('c'):
                stdscr.addstr(4, 0, "                           ")
                stdscr.addstr(4, 0, "Circle")
            elif key == ord('s'):
                stdscr.addstr(4, 0, "                           ")
                stdscr.addstr(4, 0, "Stop")
            
                
            stdscr.refresh()
            # i = ((i + 1) % 9)
                        
    finally:
        curses.nocbreak()
        curses.echo()
        stdscr.keypad(False)
        curses.endwin()
        

curses.wrapper(interface)

