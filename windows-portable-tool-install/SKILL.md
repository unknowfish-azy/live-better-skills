---
name: windows-portable-tool-install
description: Install portable Windows command-line tools (e.g. John the Ripper, Hashcat, nmap) from official binary archives on this machine. This skill should be used when the user asks to install a CLI/security tool on Windows and winget has no official package. Installs to E:\Tools per user preference (all tools live on the E drive, never C). Covers environment quirks (PowerShell-only shell, log-file output capture, no PyPI access), verified official download URLs, 7zr.exe extraction, user-PATH setup, and per-tool verification commands.
agent_created: true
---

# Windows Portable Tool Install

## Overview

Install portable Windows CLI tools from official binary archives into `E:\Tools\<tool>`, verify them, and register them on the user PATH. Trigger when the user asks to install a command-line tool (e.g. "帮我安装 John the Ripper / Hashcat / nmap") and winget has no official package.

## Environment facts (verified 2026-10-18 — do not re-discover)

- Shell: the Bash tool is broken in this environment (coreutils missing from PATH, `dirname`/`ls` not found). Use the **PowerShell tool** for everything.
- Output capture: the PowerShell tool frequently does not echo stdout back. Always redirect command output to a log file (`| Out-File <path> -Encoding utf8`) and read it with the Read tool. Never rely on seeing stdout directly.
- Package managers: `winget` v1.29.380 works; choco absent; scoop present but useless for these tools. Run `winget search <tool> --accept-source-agreements` first — if an official package exists, `winget install --id <id> --accept-package-agreements --accept-source-agreements --disable-interactivity` and skip to verification.
- pip/PyPI is unreachable from the managed Python venv ("No matching distribution found"). Do not depend on pip; use standalone binaries instead.
- 7-Zip is not installed. Fetch the official standalone extractor once: `https://www.7-zip.org/a/7zr.exe` (~600 KB) → `E:\Tools\7zr.exe`. **Critical: `7zr.exe` is the reduced build and handles ONLY the 7z format** — pointed at a `.zip` it fails with `Can't open as archive: 1` (exit 2). For zip files use `Expand-Archive -LiteralPath <zip> -DestinationPath <dir> -Force` or system `tar -xf`.
- Install convention (user preference, set 2026-10-18): tools go to `E:\Tools\<tool>` — the user keeps ALL tools on the E drive (see `E:\ffmpeg`, `E:\AWSCLI`, and `E:\Tools` which already holds gInk/OpenBoard/ZoomIt). Never install large tools on C. Downloaded archives go to `E:\安装包` (the user's installer archive folder); staging under `E:\Tools\_staging`.

## Workflow

1. Search winget. If a package exists, install via winget and skip to step 5.
2. Find the official binary URL. Prefer the vendor's own site; confirm the latest version with WebFetch on the download page. To get real hrefs: `Invoke-WebRequest` the page and inspect `$html.Links` — **resolve relative links against the page URL** (see the John pitfall in the sources table).
3. Download the archive via `Invoke-WebRequest -UseBasicParsing -TimeoutSec 600` (final archive home: `E:\安装包`).
4. Ensure `E:\Tools\7zr.exe` exists (download from 7-zip.org if missing). Extract to staging, then move the inner folder to `E:\Tools\<tool>`.
5. Verify the tool runs (see verification table).
6. Append the tool's bin dir to the **user** PATH (skip if already present):
   `$cur = [Environment]::GetEnvironmentVariable("Path","User"); $new = "$cur;<dir>"; [Environment]::SetEnvironmentVariable("Path", $new, "User")`
7. Clean up staging dirs and temp logs. Keep the archives in `E:\安装包` and mention they can be deleted to reclaim space.

A ready-made script implementing steps 3-7: `scripts/install-portable-tool.ps1`.

## Verified official sources (2026-10-18)

| Tool | URL | Notes |
|---|---|---|
| John the Ripper 1.9.0-jumbo-1 (win64) | `https://www.openwall.com/john/k/john-1.9.0-jumbo-1-win64.7z` | Pitfall: the openwall.com/john/ page's relative links resolve under `/john/k/`, NOT `/john/j/` (that path 404s). Archive contains `john-1.9.0-jumbo-1-win64/` with `run/john.exe`. |
| Hashcat | `https://hashcat.net/files/hashcat-<ver>.7z` (v7.1.2 at time of writing) | Confirm the latest version at https://hashcat.net/hashcat/ before downloading. Archive contains `hashcat-<ver>/` with `hashcat.exe`. |
| 7zr.exe standalone | `https://www.7-zip.org/a/7zr.exe` | Extraction dependency. |

## GUI / installer-based tools (desktop apps)

When the user wants a *desktop* (GUI) version of a CLI tool, install a third-party GUI front-end as a companion — the underlying CLI stays as-is and the GUI only points at its exe.

1. **Find assets**: GitHub release pages are JS-rendered and WebFetch returns nothing useful. Use the API instead:
   `Invoke-RestMethod "https://api.github.com/repos/<owner>/<repo>/releases/latest" -Headers @{ "User-Agent"="WorkBuddy" }` → `.assets[].browser_download_url`.
2. **Identify the installer type** before trying silent flags (read the exe as bytes and regex the ASCII dump; `Add-Type` is blocked by the sandbox, so do NOT use it):
   `$text = [System.Text.Encoding]::ASCII.GetString([System.IO.File]::ReadAllBytes($exe))`
   - matches "Inno Setup" → silent: `Start-Process $exe -ArgumentList '/VERYSILENT','/NORESTART','/SUPPRESSMSGBOXES','/DIR=<target>' -Wait -PassThru`
   - matches "NullsoftInstall" → NSIS: `/S /D=<target>`
   - neither → run `$exe --help`; a usage line mentioning `--script` means **Qt Installer Framework (QtIFW)**.
3. **QtIFW unattended install**: write a controller script (`install.qs`) with page callbacks (`IntroductionPageCallback`, `TargetDirectoryPageCallback` → `gui.pageById(QInstaller.TargetDirectory).TargetDirectoryLineEdit.setText("E:\\Tools\\X")`, `ComponentSelectionPageCallback`, `LicenseAgreementPageCallback`, `ReadyForInstallationPageCallback`/`PerformInstallationPageCallback` → `buttons.CommitButton`, `FinishedPageCallback` → `buttons.FinishButton`), then `Start-Process $exe -ArgumentList '--script','<path>.qs','-v' -Wait -PassThru`. Exit code 0 = installed.
4. **Gotcha**: QtIFW launches the app at the finish page and the installer process does NOT exit until that window closes — `Start-Process -Wait` hangs for as long as the app stays open (observed 16 min). If it hangs, `Get-Process <app> | Stop-Process -Force` to release it. Unchecking the launch box in `FinishedPageCallback` (`page.findChild("RunProgramCheckBox")`) does not always prevent this.
5. **Verifying a GUI app started**: GUI apps can take >10 s to appear. Start with `-PassThru`, `Start-Sleep 12`, then check `$p.HasExited` — checking after only ~8 s gives a false "it crashed" reading.
6. Installers create Start Menu / Desktop shortcuts automatically; tell the user where. Config files often live in a dotfolder under `$HOME` (e.g. Johnny → `C:\Users\<user>\.john\johnny.conf`, key `PathToJohn`) — pre-fill the path to the CLI exe so the GUI works on first launch.

## Verified GUI front-ends (2026-10-18)

| GUI | Target CLI | Source | Installed path |
|---|---|---|---|
| Johnny 2.2 | John the Ripper | `https://openwall.info/wiki/_media/john/johnny/johnny_2.2_win.zip` (zip contains `johnnyInstaller.exe`, QtIFW) | `E:\Tools\Johnny` |
| hashcat-gui v1.4.1 | Hashcat | GitHub `Felix3214g/hashcat-gui` latest release asset `HashcatGUI-v1.4.1-windows-x64-setup.exe` (Inno Setup) | `E:\Tools\HashcatGUI` |
| HashcatGUI (blandyuk) | Hashcat | Hashkiller forum, Windows-only, .NET 4.8, community classic with a Chinese localization; not installed (GitHub option preferred) | — |

## Verification commands

| Tool | Command | Expected output |
|---|---|---|
| John | `& "E:\Tools\john\run\john.exe" --list=build-info` | `Version: 1.9.0-jumbo-1`, `Build: cygwin 64-bit x86_64 AVX2 AC OMP` |
| Hashcat | `& "E:\Tools\hashcat\hashcat.exe" --version` | `v7.1.2` |
| Hashcat GPU | Run `.\hashcat.exe -I --quiet` **from inside the hashcat dir** (use `Push-Location`) — OpenCL kernels are cwd-relative; running from elsewhere fails with `./OpenCL/: No such file or directory`. This machine: NVIDIA GeForce RTX 4060 Laptop GPU (NVIDIA CUDA OpenCL platform) plus an Intel OpenCL Graphics platform detected. `CUDA SDK Toolkit not installed` and `nvmlDeviceGetFanSpeed(): Not Supported` warnings are normal without the CUDA toolkit; OpenCL fallback works. |

## Ethics

John the Ripper and Hashcat are dual-use security auditing tools. Install and use them only on systems the user owns or is explicitly authorized to test. State this briefly when installing.
