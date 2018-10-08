#!/bin/bash

# Standard preambule
plain() {
  local mesg=$1; shift
  printf "    ${mesg}\n" "$@" >&2
}

print_warning() {
  local mesg=$1; shift
  printf "${YELLOW}=> WARNING: ${mesg}${ALL_OFF}\n" "$@" >&2
}

print_msg1() {
  local mesg=$1; shift
  printf "${GREEN}==> ${mesg}${ALL_OFF}\n" "$@" >&2
}

print_msg2() {
  local mesg=$1; shift
  printf "${BLUE}  -> ${mesg}${ALL_OFF}\n" "$@" >&2
}

print_error() {
  local mesg=$1; shift
  printf "${RED}==> ERROR: ${mesg}${ALL_OFF}\n" "$@" >&2
}

ALL_OFF='[00m'
BLUE='[38;5;04m'
GREEN='[38;5;02m'
RED='[38;5;01m'
YELLOW='[38;5;03m'

readonly ALL_OFF BOLD BLUE GREEN RED YELLOW
ARCH_INSTALLS="${ARCH_INSTALLS:-linux}"

for _mingw in ${ARCH_INSTALLS}; do
	
	case ${_mingw} in
		linux)
			_glibc=`ldd --version | head -n 1 | awk '{ print $5; }'`
			_os=$(uname)
			_arch=${_os,,}_$(uname -m)
			_dist=bin_${_arch}
			_python=python3.6
		;;
	esac

	print_msg1 "........................."
	print_msg1 "Building ${_arch} release"
	print_msg1 "........................."

	[ -d ${_dist} ] && rm -rf ${_dist}

	(
		[ ! -f kindlegen ] && cp ../kindlegen .
		${_python} setup-cli.linux.cx_freeze.py build_exe -b ${_dist}
		if [ $? -eq 0 ]; then
			# clean after cx_Freeze
			for file in ${_dist}/lib/.libs/*; do
				rm ${_dist}/lib/`basename $file`
			done
			[ -f ${HOME}/result/fb2mobi_cli_${_arch}_glibc_${_glibc}.tar.xz ] && rm ${HOME}/result/fb2mobi_cli_${_arch}_glibc_${_glibc}.tar.xz
			tar --directory ${_dist} --create --xz --file ${HOME}/result/fb2mobi_cli_${_arch}_glibc_${_glibc}.tar.xz .
		fi
	)
done
exit 0

