# Rebuild only the offline metadata utility. Never edit the game or generate PTBR.
$ErrorActionPreference = 'Stop'
$workRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $workRoot
$cursor = Get-Item -LiteralPath $repoRoot
while ($null -ne $cursor) {
    if ((Test-Path -LiteralPath (Join-Path $cursor.FullName 'StarDynasties.exe')) -and
        (Test-Path -LiteralPath (Join-Path $cursor.FullName 'StarDynasties_Data'))) {
        throw 'The game installation is read-only. Use the translation repository.'
    }
    $cursor = $cursor.Parent
}
$lockPath = Join-Path $PSScriptRoot 'toolchain.json'
$lock = Get-Content -LiteralPath $lockPath -Raw | ConvertFrom-Json
$unchanged = $true
foreach ($property in $lock.files.PSObject.Properties) {
    $path = Join-Path $workRoot $property.Name
    if (!(Test-Path -LiteralPath $path) -or
        (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $property.Value) {
        $unchanged = $false
    }
}
if ($unchanged) { Write-Output 'unchanged: helper and source hashes match'; exit 0 }
$library = Join-Path $workRoot 'vendor\mono-cecil-0.11.6\Mono.Cecil.dll'
if ((Get-FileHash -LiteralPath $library -Algorithm SHA256).Hash.ToLowerInvariant() -ne
    'c41bdb9ffd3c5f6e17d2382c1012d73703e035e3f1100245fdd4e08c8dc6eb5b') {
    throw 'Mono.Cecil does not match the pinned official package.'
}
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (!(Test-Path -LiteralPath $compiler)) { throw 'Install/use the .NET Framework 4.x C# compiler on the engineering host.' }
$staging = Join-Path $workRoot ('.state\helper-build-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $staging | Out-Null
$output = Join-Path $staging 'GrammarTool.exe'
$source = Join-Path $PSScriptRoot 'GrammarTool.cs'
$launcher = Join-Path $PSScriptRoot 'Launcher.cs'
& $compiler /nologo /optimize+ /target:exe /main:Launcher ('/out:' + $output) ('/reference:' + $library) /reference:System.Web.Extensions.dll $source $launcher
if ($LASTEXITCODE -ne 0) { throw 'Compiler failed; the accepted helper was preserved.' }
Move-Item -LiteralPath $output -Destination (Join-Path $PSScriptRoot 'GrammarTool.exe') -Force
foreach ($property in $lock.files.PSObject.Properties) {
    $property.Value = (Get-FileHash -LiteralPath (Join-Path $workRoot $property.Name) -Algorithm SHA256).Hash.ToLowerInvariant()
}
$json = ($lock | ConvertTo-Json -Depth 8) + "`n"
[IO.File]::WriteAllText($lockPath, $json, (New-Object Text.UTF8Encoding($false)))
Write-Output 'Helper rebuilt. Run the full tests and review/update runtime-support.json fingerprints before authorizing a native build.'
