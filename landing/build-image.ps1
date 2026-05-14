param(
    [string]$ImageName = "personal-emr-landing",
    [string]$Tag = "local",
    [string]$OutputFile = "personal-emr-landing.tar"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ImageRef = "${ImageName}:${Tag}"
$OutputPath = Join-Path $ScriptDir $OutputFile

Write-Host "Building $ImageRef from $ScriptDir"
docker build -t $ImageRef $ScriptDir
if ($LASTEXITCODE -ne 0) {
    throw "docker build failed with exit code $LASTEXITCODE"
}

Write-Host "Saving $ImageRef to $OutputPath"
docker save -o $OutputPath $ImageRef
if ($LASTEXITCODE -ne 0) {
    throw "docker save failed with exit code $LASTEXITCODE"
}

Write-Host "Done: $OutputPath"
