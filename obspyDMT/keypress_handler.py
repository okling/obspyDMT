import sys


if sys.platform.startswith("win"):
    import threading
    import termios
    TERMIOS = termios
    # need a lock for the global quitflag variable which is used in two threads
    lock = threading.RLock()

# this is to support windows without changing the rest
if sys.platform.startswith("win"):
    class keypress_thread():
        """
        Empty class, for windows support.
        """
        def __init__(self):
            print "Detected windows, no keypress-thread started."

        def start(self):
            print "No 'q' key support on windows."

    def check_quit():
        """
        Does nothing, for windows support.
        """
        return
#
else:
    class keypress_thread (threading.Thread):
        """
        This class will run as a second thread to capture keypress events
        """
        global quitflag, done

        def run(self):
            global quitflag, done
            while not done:
                c = getkey()
                print c
                if c == 'q' and not done:
                    try:
                        with lock:
                            quitflag = True
                    except:
                        pass
                    print "\n=======================================" + \
                                "======================================="
                    print "You pressed q."
                    msg = "obspyDMT will finish downloading and saving the " \
                    + "last file and quit gracefully."
                    print msg
                    print "=======================================" + \
                                "======================================="
                    # exit this thread
                    sys.exit(0)

    def getkey():
        """
        Uses termios to wait for a keypress event and return the char.
        """
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        new[3] = new[3] & ~TERMIOS.ICANON & ~TERMIOS.ECHO
        new[6][TERMIOS.VMIN] = 1
        new[6][TERMIOS.VTIME] = 0
        termios.tcsetattr(fd, TERMIOS.TCSANOW, new)
        c = None
        try:
                c = os.read(fd, 1)
        finally:
                termios.tcsetattr(fd, TERMIOS.TCSAFLUSH, old)
        return c

    def check_quit():
        """
        Checks if the user pressed q to quit downloading meanwhile.
        """
        global quitflag
        with lock:
            if quitflag:
                print "\n\n=======================================" + \
                                "========================="
                msg = "Quitting. To resume the download: \nplease use " + \
                        "the 'Update' functionality described in the tutorial."
                print msg
                print "=======================================" + \
                                "========================="
                sys.exit(0)
