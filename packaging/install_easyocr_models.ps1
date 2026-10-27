param(
    [string]$TargetModelDirectory = (Join-Path $env:USERPROFILE ".EasyOCR\model")
)

$ErrorActionPreference = "Stop"
$PackagedModelDirectory = Join-Path $PSScriptRoot "runtime\resource\easyocr\model"
$Models = @(
    @{ Name = "craft_mlt_25k.pth"; Md5 = "2F8227D2DEF4037CDB3B34389DCF9EC1" },
    @{ Name = "zh_sim_g2.pth"; Md5 = "B601CE7143293387D3EC4F41A66EDC07" }
)

# .NET works in Windows PowerShell even when the host has inherited a different
# PowerShell edition's module search path and Get-FileHash is unavailable.
function Get-ModelHash([string]$Path) {
    $Hasher = [System.Security.Cryptography.MD5]::Create()
    $Stream = [System.IO.File]::OpenRead($Path)
    try { return [System.BitConverter]::ToString($Hasher.ComputeHash($Stream)).Replace("-", "") }
    finally { $Stream.Dispose(); $Hasher.Dispose() }
}

New-Item -ItemType Directory -Path $TargetModelDirectory -Force | Out-Null
foreach ($Model in $Models) {
    $SourcePath = Join-Path $PackagedModelDirectory $Model.Name
    $TargetPath = Join-Path $TargetModelDirectory $Model.Name
    if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf)) {
        throw "Packaged EasyOCR model is missing: $SourcePath"
    }
    if ((Get-ModelHash $SourcePath) -ne $Model.Md5) {
        throw "Packaged EasyOCR model checksum mismatch: $($Model.Name)"
    }
    if (Test-Path -LiteralPath $TargetPath -PathType Leaf) {
        if ((Get-ModelHash $TargetPath) -eq $Model.Md5) {
            Write-Host "[INFO] EasyOCR model is already installed: $($Model.Name)"
            continue
        }
    }
    Copy-Item -LiteralPath $SourcePath -Destination $TargetPath -Force
    if ((Get-ModelHash $TargetPath) -ne $Model.Md5) {
        throw "Installed EasyOCR model checksum mismatch: $TargetPath"
    }
    Write-Host "[SUCCESS] Installed EasyOCR model: $TargetPath"
}
Write-Host "[SUCCESS] EasyOCR models are ready: $TargetModelDirectory"
