#!/usr/bin/env bash

remote=$1
dir=$2
remotedir=$dir
if [[ $# -gt 2 ]]; then
   remotedir=$3
fi

# ssh -o StreamLocalBindUnlink=yes -R /tmp/$(id -n -u)_local.socket:localhost:22 schspa@remote.com
# sshfs -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o ProxyCommand="socat - UNIX-CLIENT:/tmp/%r_local.socket" -o idmap=user,uid=$(id -u),gid=$(id -g) -o auto_unmount  schspa@localhost:/Volumes/work ~/work

command_exists() {
    ssh $remote which $1 >/dev/null
    return $?
}

show_install() {
    cat << 'EOF'
Please install required packages first!!
Ubuntu:    sudo apt-get install socat sshfs
ArchLinux: sudo pacman -S socat sshfs
EOF
}

command_exists socat || {
    show_install
    exit -1
}
command_exists sshfs || {
    show_install
    exit -2
}

echo "Tring to mount $dir directory to remote ${remote} $remotedir"
eval local_dir=$dir
eval local_dir=$(readlink -f $local_dir)

ssh -o StreamLocalBindUnlink=yes -R /tmp/$(id -n -u)_local.socket:localhost:22 ${remote} bash -s << EOF
sshfs -f -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o ProxyCommand="socat - UNIX-CLIENT:/tmp/%r_local.socket" -o idmap=user,uid=\$(id -u),gid=\$(id -g) -o auto_unmount  schspa@localhost:${local_dir} $remotedir
EOF
