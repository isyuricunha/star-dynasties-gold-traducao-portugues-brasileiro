# Compatibility entry point. Python owns cross-platform builds and LF fingerprints.
$ErrorActionPreference = 'Stop'
& python (Join-Path $PSScriptRoot 'build-helper.py') @args
exit $LASTEXITCODE
