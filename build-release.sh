#!env bash

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
ARCH_INSTALLS="${ARCH_INSTALLS:-win32 win64 linux}"

w_cmd=/mnt/c/Windows/System32/cmd.exe

find . -type d -name '__pycache__' -print0 | xargs -0 rm -rf

for _mingw in ${ARCH_INSTALLS}; do
	
	case ${_mingw} in
		win32)
			_arch=win32
			_msystem=MINGW32
			_dist=bin_win32
			_python=d:/python/python3.6.0_x86/python.exe
		;;
		win64)
			_arch=win64
			_msystem=MINGW64
			_dist=bin_win64
			_python=d:/python/python3.6.0_x64/python.exe
		;;
		linux)
			_glibc=`ldd --version | head -n 1 | awk '{ print $5; }'`
			_msystem=
			_os=$(uname)
			_arch=${_os,,}_$(uname -m)
			_dist=bin_${_arch}
			_python=python3.6
		;;
	esac

	print_msg1 "Building ${_arch} release"
	print_msg1 "........................."

	[ -d ${_dist} ] && rm -rf ${_dist}

	(
		if [ -z ${_msystem} ]; then
			${_python} setup-cli.linux.cx_freeze.py build_exe -b ${_dist}
			if [ $? -eq 0 ]; then
				[ -f fb2mobi_cli_${_arch}_glibc_${_glibc}.tar.xz ] && rm fb2mobi_cli_${_arch}_glibc_${_glibc}.tar.xz
				tar --directory ${_dist} --create --xz --file fb2mobi_cli_${_arch}_glibc_${_glibc}.tar.xz .
			fi
		else
			[ -f fb2mobi_all_${_arch}.7z ] && rm fb2mobi_${_arch}.7z

			w_tmp_dir=`${w_cmd} /c echo %TMP% 2>/dev/null | tr -d '\r'`
			u_tmp_dir=/mnt/c`echo -n ${w_tmp_dir:2} | tr '\\\\\\\\' '/'`
			u_work_dir=`mktemp -d -p "${u_tmp_dir}"`
			w_work_dir=${w_tmp_dir}\\`basename ${u_work_dir}`

			repo=`git remote -v | grep fetch | awk '{ print $2; }'`

			pushd ${u_work_dir}
			git clone ${repo} .
			popd
			cp kindlegen.exe ${u_work_dir}/.

			cat <<EOF >${u_work_dir}/_build_${_arch}.cmd
cd ${w_work_dir}
${_python} setup-all.win32.cx_freeze.py build_exe -b ${_dist}
EOF

			${w_cmd} /c ${w_work_dir}/_build_${_arch}.cmd 2>/dev/null

			if [ -d ${u_work_dir}/${_dist} ]; then
				cp -R ${u_work_dir}/${_dist} ${_dist}
				rm -rf ${u_work_dir}

				cd ${_dist}
				7z a -r ../fb2mobi_all_${_arch}
			fi
		fi
	)

done

find . -type d -name '__pycache__' -print0 | xargs -0 rm -rf

exit 0

