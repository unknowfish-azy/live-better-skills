#requires -Version 5.1
<#
.SYNOPSIS
Installs a portable Windows CLI tool from an official archive into E:\Tools.
.DESCRIPTION
Downloads the archive, extracts it (.7z via 7zr.exe, .zip via Expand-Archive),
moves the inner folder to C:\Users\33908\Tools\<ToolName>, and optionally
appends the install dir to the user PATH.
.PARAMETER Url
Direct download URL of the official archive (.7z or .zip).
.PARAMETER ToolName
Target folder name under C:\Users\33908\Tools.
.PARAMETER InnerFolder
Name of the top-level folder inside the archive (omit if the archive root is the tool dir).
.PARAMETER AddToPath
Append the install dir to the user PATH.
.EXAMPLE
powershell -File scripts\install-portable-tool.ps1 -Url "https://hashcat.net/files/hashcat-7.1.2.7z" -ToolName "hashcat" -InnerFolder "hashcat-7.1.2" -AddToPath
#>
param(
  [Parameter(Mandatory=$true)][string]$Url,
  [Parameter(Mandatory=$true)][string]$ToolName,
  [string]$InnerFolder,
  [switch]$AddToPath
)
$ErrorActionPreference = "Stop"
$ToolsRoot = "E:\Tools"
$Downloads = "E:\安装包"
$Staging   = Join-Path $ToolsRoot "_staging\$ToolName"
$SevenZr   = Join-Path $ToolsRoot "7zr.exe"
$archive   = Join-Path $Downloads ([System.IO.Path]::GetFileName($Url))
$dest      = Join-Path $ToolsRoot $ToolName

New-Item -ItemType Directory -Force -Path $Downloads, $Staging | Out-Null

if (-not (Test-Path $SevenZr)) {
  Invoke-WebRequest -Uri "https://www.7-zip.org/a/7zr.exe" -OutFile $SevenZr -UseBasicParsing -TimeoutSec 120
}

Invoke-WebRequest -Uri $Url -OutFile $archive -UseBasicParsing -TimeoutSec 600
Write-Output "Downloaded $archive ($((Get-Item $archive).Length) bytes)"

$outDir = Join-Path $Staging "out"
if ($archive -like "*.7z") {
  & $SevenZr x $archive -o"$outDir" -y | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "7zr extraction failed" }
} elseif ($archive -like "*.zip") {
  Expand-Archive -Path $archive -DestinationPath $outDir -Force
} else { throw "Unsupported archive type: $archive" }

$src = $outDir
if ($InnerFolder) { $src = Join-Path $outDir $InnerFolder }
if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
Move-Item -Path $src -Destination $dest
Write-Output "Installed to $dest"

if ($AddToPath) {
  $cur = [Environment]::GetEnvironmentVariable("Path", "User")
  if ($cur -notlike "*$dest*") {
    if ([string]::IsNullOrEmpty($cur)) { $new = $dest } else { $new = "$cur;$dest" }
    [Environment]::SetEnvironmentVariable("Path", $new, "User")
    Write-Output "Added to user PATH: $dest"
  } else { Write-Output "Already on user PATH: $dest" }
}

Remove-Item -Recurse -Force (Join-Path $ToolsRoot "_staging") -ErrorAction SilentlyContinue
Write-Output "Done. Archive kept at $archive"
