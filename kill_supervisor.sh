#!/bin/bash
supervisorctl stop all
supervisorctl remove celery_beat
supervisorctl remove celery_worker
supervisorctl remove redis
echo "" >/var/log/cccb_transfers/celery_worker.log
echo "" >/var/log/cccb_transfers/celery_beat.log
echo "" >/var/log/cccb_transfers/redis.log
