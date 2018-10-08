param($tag="latest")
$global:ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

if( $tag -eq "latest" )
{
    $tag = Invoke-WebRequest -UseBasicParsing -Uri 'https://api.github.com/repos/rupor-github/fb2mobi/releases/latest' | ConvertFrom-Json | Select -ExpandProperty "tag_name"
}

Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/rupor-github/fb2mobi/archive/${TAG}.zip" -OutFile "src.zip"; 
Write-Host "Uncompressing sources..."
Expand-Archive -Path "src.zip" -DestinationPath "."
Remove-Item "src.zip" -Force

Push-Location -Path "fb2mobi-$tag"
./build-release.ps1
Pop-Location

