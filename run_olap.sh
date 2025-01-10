#!/usr/bin/bash

HOMOGENEOUS_DIR=homogeneous
HETEROGENEOUS_DIR=heterogeneous

LOGDIR=logs

DURATION=1800
RAMP_TIME=300
# CONCURRENCY_OLTP=50
CONCURRENCY_OLAP=25

HOMOGENEOUS_PORT=26257
HETEROGENEOUS_PORT_OLTP=26258
HETEROGENEOUS_PORT_OLAP=26259

# Heterogeneous Cluster

if [ ! -d ${HETEROGENEOUS_DIR} ]; then
  mkdir ${HETEROGENEOUS_DIR}
fi

cd ${HETEROGENEOUS_DIR}

if [ ! -d ${LOGDIR} ]; then
  mkdir ${LOGDIR}
fi

nohup dbworkload run -w ../dbworkload/DatapointOLAP_1.py \
    --uri postgresql://root@localhost:${HETEROGENEOUS_PORT_OLAP}/oltaptest?sslmode=disable \
    -s -r ${RAMP_TIME} \
    -c ${CONCURRENCY_OLAP} -d ${DURATION} -p 26263 > ${LOGDIR}/heterogeneous-olap.log 2>&1 &

cd ..

