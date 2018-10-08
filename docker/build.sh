#!/bin/bash

if [[ "${1}" == "latest" || "${1}" == "" ]]; then
    TAG=$(curl -s https://api.github.com/repos/rupor-github/fb2mobi/releases/latest | grep tag_name |  cut -d '"' -f 4)
else
    TAG=${1}
fi
curl -LO https://github.com/rupor-github/fb2mobi/archive/${TAG}.tar.gz
tar -xvf ${TAG}.tar.gz
rm ${TAG}.tar.gz

cd fb2mobi-${TAG}
./build-release.sh
