#!/bin/bash

log_file="/var/logging/log/spaceusage.log"

#date -u --rfc-3339=seconds >> $log_file
date --utc +%FT%TZ >> $log_file
du -s /var/logging/data /var/logging/log >> $log_file
