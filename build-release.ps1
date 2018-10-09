$result="../result"
foreach( $a in ($Env:ARCH_INSTALLS -split ' ') )
{
    switch( $a )
    {
        'win32' { $arch="win32"; $dist="bin_win32"; $python="c:/python32/python.exe" }
        'win64' { $arch="win64"; $dist="bin_win64"; $python="c:/python64/python.exe" } 
        default { Write-Error "Unsupported architecture $a"; exit 0 }
    }

    Write-Host "........................"
    Write-Host "Building $arch release"
    Write-Host "........................"

    Remove-Item -Path $dist -Force -Recurse -ErrorAction SilentlyContinue
    New-Item -ItemType directory -Path $dist | Out-Null
    Remove-Item -Path $result/fb2mobi_all_$arch.zip -Force -ErrorAction SilentlyContinue
    Copy-Item -Path ../kindlegen.exe -Destination ./kindlegen.exe -ErrorAction SilentlyContinue

    &$python setup-all.win32.cx_freeze.py build_exe -b $dist

    Write-Host "Cleaning after cx_freeze..."
    $dirs="imageformats", "platforms", "styles"
    foreach( $d in $dirs )
    {
        # Move-Item -Path $dist/$d/Qt5* -Destination $dist/lib -ErrorAction SilentlyContinue
        Copy-Item -Path $dist/$d/Qt5* -Destination $dist/lib -ErrorAction SilentlyContinue
        Remove-Item -Path $dist/$d/Qt5* -ErrorAction SilentlyContinue
        Remove-Item -Path $dist/$d/VCRUNTIME140.dll -ErrorAction SilentlyContinue
        Remove-Item -Path $dist/$d/MSVCP140.dll -ErrorAction SilentlyContinue
    }
    Move-Item -Path $dist/lib/VCRUNTIME140.dll -Destination $dist/VCRUNTIME140.dll -ErrorAction SilentlyContinue
    Move-Item -Path $dist/lib/MSVCP140.dll $dist/MSVCP140.dll -ErrorAction SilentlyContinue

    Write-Host "Compressiing result..."
    Compress-Archive -Path $dist -DestinationPath $result/fb2mobi_all_$arch
}
