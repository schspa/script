#/usr/bin/zsh
# https://github.com/schspa/script
# script for let usr to select device for adb command
#
# Author: Schspa (schspa@gmail.com)
# V0.0.1
#

function adba {
	ADB=$(command which adb)
	local MANDROID_SERIAL
	TEMP=`getopt -o s: -- "$@"`
	if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi
	eval set -- "$TEMP"
	while true ; do
		case "$1" in
			-s) echo "Option -s, argument \`$2'" && MANDROID_SERIAL=$2; shift 2;;
			--) shift ; break ;;
			*) echo "Internal error!" ; exit 1 ;;
		esac
	done

	if [ "$MANDROID_SERIAL"x != ""x ]; then
	   	$ADB -s $ANDROID_SERIAL $@
	else
		$ADB $@ 2>/dev/null
		if [ $? != 0 ]; then
			local num=0
			local device_array=()
			for i in `$ADB devices | awk '{ print $1 }'`; do
				let "num+=1"
				if [ $num != 1 ]; then
					device_array+=$i
				fi
			done
			select i in $device_array; do
				echo "connect to $i"
				$ADB -s $i $@
				break
			done
		fi
	fi
}

alias adb=adba
