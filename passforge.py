#!/usr/bin/env python3

import os
import sys
from shell.shell import PassForgeShell

def main():
    shell = PassForgeShell()  # Create an instance of the PassForgeShell class, which initializes the shell state and command completer.
    shell.run()  # Start the shell's main loop, allowing the user to interact with the command-line interface.

if __name__ == "__main__":
    main()