param(
    [string]$DistributionRoot = "E:\python\local_ocr_dist",
    [string]$PythonExe = "E:\python\ghost_catcher\.venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"
$PackageRoot = Join-Path $DistributionRoot "local_ocr"
if (-not (Test-Path -LiteralPath (Join-Path $PackageRoot "resource\easyocr\model"))) {
    throw "Existing distribution with EasyOCR assets is required: $PackageRoot"
}

$PythonSources = @(
    "config.py", "main.py", "ocr_engine.py", "lmstudio_client.py",
    "ensure_lmstudio.py"
)
$SourceFiles = @("requirements.txt", ".env.example", "quick_start.bat")
$RuntimeRoot = Join-Path $PackageRoot "runtime"
New-Item -ItemType Directory -Path $RuntimeRoot -Force | Out-Null
& $PythonExe -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 11) else 1)'
if ($LASTEXITCODE -ne 0) { throw "Bytecode builds require Python 3.11" }
foreach ($Name in $PythonSources) {
    $Source = Join-Path $PSScriptRoot $Name
    $Target = Join-Path $RuntimeRoot ([System.IO.Path]::ChangeExtension($Name, ".pyc"))
    & $PythonExe -c 'import py_compile,sys; py_compile.compile(sys.argv[1], cfile=sys.argv[2], dfile=sys.argv[3], doraise=True)' $Source $Target $Name
    if ($LASTEXITCODE -ne 0) { throw "Bytecode compilation failed: $Name" }
}
foreach ($Name in $SourceFiles) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $Name) -Destination (Join-Path $PackageRoot $Name) -Force
}
foreach ($Name in @("start.bat", "README_START.txt", "install_easyocr_models.ps1", "install_deps.bat")) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "packaging\$Name") -Destination (Join-Path $PackageRoot $Name) -Force
}

# Use an explicit file manifest so local configuration and caches never enter the ZIP.
$Names = $SourceFiles + @("start.bat", "README_START.txt", "install_deps.bat", "install_easyocr_models.ps1")
$Files = @($Names | ForEach-Object { Get-Item -LiteralPath (Join-Path $PackageRoot $_) })
$Files += @($PythonSources | ForEach-Object {
    Get-Item -LiteralPath (Join-Path $RuntimeRoot ([System.IO.Path]::ChangeExtension($_, ".pyc")))
})
foreach ($Name in @("resource\common_ch_sim_clean.txt", "resource\easyocr\model\craft_mlt_25k.pth", "resource\easyocr\model\zh_sim_g2.pth")) {
    $Target = Join-Path $RuntimeRoot $Name
    New-Item -ItemType Directory -Path (Split-Path $Target -Parent) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $PackageRoot $Name) -Destination $Target -Force
    $Files += Get-Item -LiteralPath $Target
}
Add-Type -AssemblyName System.IO.Compression
$ZipPath = Join-Path $DistributionRoot "local_ocr_ready.zip"
$Stream = [System.IO.File]::Open($ZipPath, [System.IO.FileMode]::Create)
$Archive = [System.IO.Compression.ZipArchive]::new($Stream, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($File in $Files) {
        $Relative = $File.FullName.Substring($PackageRoot.Length + 1).Replace('\', '/')
        $Entry = $Archive.CreateEntry("local_ocr/$Relative", [System.IO.Compression.CompressionLevel]::Optimal)
        $InputStream = [System.IO.File]::OpenRead($File.FullName)
        $OutputStream = $Entry.Open()
        try { $InputStream.CopyTo($OutputStream) }
        finally { $OutputStream.Dispose(); $InputStream.Dispose() }
    }
}
finally { $Archive.Dispose(); $Stream.Dispose() }

Get-Item -LiteralPath $ZipPath | Select-Object FullName, Length
Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256
