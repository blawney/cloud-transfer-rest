#!/bin/bash
supervisorctl stop all
supervisorctl remove transfer_celery_beat
supervisorctl remove transfer_celery_worker
supervisorctl remove redis
echo "" >/var/log/cccb_transfers/celery_worker.log
echo "" >/var/log/cccb_transfers/celery_beat.log
echo "" >/var/log/cccb_transfers/redis.log
