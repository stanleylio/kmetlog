#!/bin/bash

log_file="/root/logging/log/spaceusage.log"

#date -u --rfc-3339=seconds >> $log_file
date --utc +%FT%TZ >> $log_file
du -s /root/logging/data /root/logging/log >> $log_file
