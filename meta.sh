#!/bin/bash

log_file="/var/kmetlog/log/spaceusage.log"

#date -u --rfc-3339=seconds >> $log_file
date --utc +%FT%TZ >> $log_file
du -s /var/kmetlog/data /var/kmetlog/log >> $log_file
