#ifdef _WIN32
#include "process.h"
#else
#include "unistd.h"
#endif

#include "dir.h"

#ifdef _WIN32
# define OS_SEP "\\"
#else
# define OS_SEP "/"
#endif

int main(int argc, char **argv)
{
    (void)argc;
    (void)argv;

    /* implicit function it's fine */
    return system("python -OO " THISDIR OS_SEP THISPY);
}
