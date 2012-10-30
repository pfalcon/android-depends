#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

static void print_usage() {
    printf("perror, convert error code(decimal) to description text\n"
            "   usage: perror errorno\n");
}

int main(int argc, const char *argv[])
{
    int err = 0;
    if(argc != 2) {
        print_usage();
        return 1;
    }
    err = strtol(argv[1], NULL, 10);
    if(errno == EINVAL || errno == ERANGE) {
        fprintf(stderr, "error code is invalid\n");
        return 1;
    }
    if(err < 0)
        err = -1*err;
    printf("%s\n", strerror(err));
    return 0;
}
