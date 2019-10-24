#!/usr/bin/python3


from glob import glob
import os.path
import itertools
import re
import sys

from xdg import BaseDirectory
from xdg.DesktopEntry import DesktopEntry
from xdg.IniFile import IniFile

PATH = os.environ["PATH"].split(':')
FILTER = re.compile("(?<!%)%[a-zA-Z]")

class ProgramNotFound(Exception):
    def __init__(self, prog):
        super().__init__("Not in PATH: '%s'." % prog)

def which(prog):
    if prog[0] == "/":
        if os.path.exists(prog):
            return prog
        else:
            raise ProgramNotFound(prog)

    if "/" in prog:
        raise ProgramNotFound(prog)

    for d in PATH:
        p = os.path.join(d, prog)
        if os.path.exists(p):
            return p

    raise ProgramNotFound(prog)

generator_dir = sys.argv[3]

withpty = which("withpty")

for dfile in itertools.chain.from_iterable(
        glob(os.path.join(path, '*.desktop'))
        for path in BaseDirectory.load_data_paths('applications')
):
    desktop = DesktopEntry(dfile)
    fname = os.path.splitext(os.path.basename(dfile))[0]

    try:
        cmd = FILTER.sub('', desktop.getExec()).split(' ', 1)
        cmd[0] = which(cmd[0])
    except ProgramNotFound:
        continue

    if desktop.getTerminal():
        cmd.insert(0, withpty)

    #service_path = os.path.join(generator_dir, fname)
    service_path = os.path.join(generator_dir, fname + "@.service")
    service = IniFile()
    service.addGroup('Unit')
    service.set('SourcePath', dfile, 'Unit')
    if not desktop.getHidden():
        service.set('X-ShowInMenu', "True", 'Unit')
    service.set('Description', desktop.getName(), 'Unit')
    service.addGroup('Service')
    service.set('EnvironmentFile', "%t/sessions/%i/environ", 'Service')
    service.set('ExecStart', " ".join(cmd), 'Service')

    service.defaultGroup = 'Unit'

    service.write(service_path)
