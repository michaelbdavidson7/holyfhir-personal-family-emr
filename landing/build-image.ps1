param(
    [string]$ImageName = "personal-emr-landing",
    [string]$Tag = "local",
    [string]$OutputFile = "personal-emr-landing.tar",
    [switch]$NoCache
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ImageRef = "${ImageName}:${Tag}"
$OutputPath = Join-Path $ScriptDir $OutputFile

$BuildArgs = @("build", "-t", $ImageRef)
if ($NoCache) {
    $BuildArgs += "--no-cache"
}
$BuildArgs += $ScriptDir

Write-Host "Building $ImageRef from $ScriptDir"
docker @BuildArgs
if ($LASTEXITCODE -ne 0) {
    throw "docker build failed with exit code $LASTEXITCODE"
}

Write-Host "Saving $ImageRef to $OutputPath"
docker save -o $OutputPath $ImageRef
if ($LASTEXITCODE -ne 0) {
    throw "docker save failed with exit code $LASTEXITCODE"
}

Write-Host "Done: $OutputPath"
