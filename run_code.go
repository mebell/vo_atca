#!/bin/bash

set -e

export EMAIL_RECIPIENTS="martinbell81@googlemail.com gemma_anderson@hotmail.com"
export SEND_EMAIL="true"

# call like this:
send_email() {
    if [ -z "${SEND_EMAIL}" ]; then
        return
    fi

    local subject=$1
    local msg=$2

    if [ -z "$subject" ]; then
        msg="no subject"
    fi

    if [ -z "$msg" ]; then
        msg="no message"
    fi

    cat << EOF | fmt | mail -s "$subject" $EMAIL_RECIPIENTS
VOevent handler code has died:
$msg
EOF
}
trap "echo 'The script has died'; send_email 'Triggering code has died' 'please restart'" EXIT HUP INT QUIT TERM


./listen_for_voevents.sh >> vo.log


