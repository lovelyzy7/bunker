"""Build commands that also run on Windows.

The Android tools are not all executables. apktool ships as a .bat/.cmd wrapper
around java, and Python's subprocess starts a batch file only through cmd.exe.
Their folders also hold apksigner.bat rather than apksigner.exe, while the
callers name the tool without a suffix, as on the other platforms.
"""
import os
import shutil


def resolve(exe):
    """The file to run for exe: on Windows, the .exe/.bat/.cmd that matches."""
    path = str(exe)
    found = shutil.which(path)
    if found:
        return found
    if os.name == "nt" and not os.path.exists(path):
        for extension in os.environ.get("PATHEXT", ".EXE;.BAT;.CMD").split(os.pathsep):
            if extension and os.path.exists(path + extension):
                return path + extension
    return path


def command(exe, *args):
    """The argv that runs exe with args on this platform."""
    path = resolve(exe)
    if os.name == "nt" and path.lower().endswith((".bat", ".cmd")):
        return [os.environ.get("COMSPEC", "cmd.exe"), "/c", path, *[str(a) for a in args]]
    return [path, *[str(a) for a in args]]
