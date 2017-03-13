#!/bin/sh
if [ -d ./build ]; then
	rm -rf ./build
fi
if [ -d ./dist ]; then
	rm -rf ./dist
fi

echo "Building..."
python setup-all.mac.cx_freeze.py

rm -rf ./build/exe.macos*
mkdir dist
ln -s /Applications ./build/Applications
echo "Making DMG..."
hdiutil create -volname fb2mobi -format UDZO -srcfolder ./build ./dist/fb2mobi_mac.dmg

rm -rf ./build
if [ -d ./dist ]; then
	open ./dist
fi