#ifdef _WIN32
#include <process.h>
#else
#include <unistd.h>
#endif
#include <signal.h>

#include "dir.h"

#ifdef _WIN32
# define OS_SEP "\\"
#else
# define OS_SEP "/"
#endif

static void handler(int sig);

int main(int argc, char **argv)
{
    (void)argc;
    (void)argv;
    (void)signal(SIGINT, handler);

    /* implicit function it's fine */
    return system("python -OO " THISDIR OS_SEP THISPY);
}

static void handler(int sig)
{
    (void)sig;
}
