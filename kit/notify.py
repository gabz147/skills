"""Native completion/input notification, with no third-party runtime."""
import subprocess
import sys
from pathlib import Path

if __name__ == '__main__':
    body = 'Waiting on you - input needed' if '--waiting' in sys.argv else 'Done - ready for input'
    if sys.platform == 'darwin':
        subprocess.run(['osascript', '-e', f'display notification "{body}" with title "Claude Code"'],
                       timeout=10, check=True)
    elif sys.platform == 'win32':
        subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                        '-File', str(Path(__file__).with_name('notify-done.ps1')), '-Title', 'Claude Code', '-Body', body],
                       creationflags=subprocess.CREATE_NO_WINDOW, timeout=15, check=True)
