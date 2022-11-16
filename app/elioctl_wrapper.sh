#!/bin/sh

SCRIPTS_PATH=/etc/elastio/dla

create_script()
{
	local filename=$1
	shift

	echo '#!/bin/sh' > "${filename}"
	echo /usr/bin/elioctl $@ >> "${filename}"
	chmod +x "${filename}"
	sync
}

filter_args()
{
	local filter=$1
	shift

	local res=
	local pass=false
	for arg do
		if [ "$arg" = "$filter" ]; then
			pass=true
			continue
		fi

		if [ "$pass" = "true" ]; then
			pass=false
			continue
		fi

		res="$res $arg"
	done
	echo $res
}

remove_2_firsts()
{
	shift 2
	echo $@
}

only_second()
{
	echo $2
}

read_full_current()
{
	tail -1 "$1"
}

read_current()
{
	remove_2_firsts $(read_full_current "$1")
}

remove_tail()
{
	local res=
	local prev=
	for arg do
		res="$res $prev"
		prev=$arg
	done
	echo $res
}

gen_reload()
{
	local cmd=$1
	shift

	for minor; do true; done
	local script_name="${SCRIPTS_PATH}/reload_${minor}.sh"

	local values=
	local line=
	case "${cmd}" in

		setup-snapshot)
			create_script "${script_name}" reload-snapshot $(filter_args '-f' $@)
			break;;

		destroy)
			rm "${script_name}"
			break;;

		transition-to-incremental)
			values=$(read_current "${script_name}")
			create_script "${script_name}" reload-incremental ${values}
			break;;

		transition-to-snapshot)
			values=$(read_current "${script_name}")
			values=$(remove_tail ${values})
			values=$(remove_tail ${values})
			create_script "${script_name}" reload-snapshot ${values} $(filter_args '-f' ${@})
			break;;

		reconfigure)
			values=$(read_current "${script_name}")
			values="$1 $2 $(filter_args '-c' ${values})"
			line=$(read_full_current "${script_name}")
			create_script "${script_name}" $(only_second ${line}) ${values}
			break;;

		reload-snapshot) break;;
		reload-incremental) break;;
		help) break;;

	esac
}

/usr/bin/elioctl $@ || exit $?
gen_reload $@
