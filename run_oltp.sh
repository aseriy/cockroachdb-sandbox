#!/usr/bin/bash

HOMOGENEOUS_DIR=homogeneous
HETEROGENEOUS_DIR=heterogeneous

LOGDIR=logs

DURATION=3600
RAMP_TIME=300
CONCURRENCY_OLTP=50
CONCURRENCY_OLAP=1

HOMOGENEOUS_PORT=26257
HETEROGENEOUS_PORT_OLTP=26258
HETEROGENEOUS_PORT_OLAP=26259

# Homogeneous Cluster

if [ ! -d ${HOMOGENEOUS_DIR} ]; then
  mkdir ${HOMOGENEOUS_DIR}
fi

cd ${HOMOGENEOUS_DIR}

if [ ! -d ${LOGDIR} ]; then
  mkdir ${LOGDIR}
fi

nohup dbworkload run -w ../dbworkload/DatapointOLTP.py \
    --uri postgresql://root@localhost:${HOMOGENEOUS_PORT}/oltaptest?sslmode=disable \
    -s -r ${RAMP_TIME} -k 300 \
    -c ${CONCURRENCY_OLTP} -d ${DURATION} -p 26260 > ${LOGDIR}/homogeneous-oltp.log 2>&1 &

# nohup dbworkload run -w ../dbworkload/DatapointOLAP.py \
#     --uri postgresql://root@localhost:${HOMOGENEOUS_PORT}/oltaptest?sslmode=disable \
#     -s -r ${RAMP_TIME} \
#     -c ${CONCURRENCY_OLAP} -d ${DURATION} -p 26261 > ${LOGDIR}/homogeneous-olap.log 2>&1 &

cd ..


# Heterogeneous Cluster

if [ ! -d ${HETEROGENEOUS_DIR} ]; then
  mkdir ${HETEROGENEOUS_DIR}
fi

cd ${HETEROGENEOUS_DIR}

if [ ! -d ${LOGDIR} ]; then
  mkdir ${LOGDIR}
fi

nohup dbworkload run -w ../dbworkload/DatapointOLTP.py \
    --uri postgresql://root@localhost:${HETEROGENEOUS_PORT_OLTP}/oltaptest?sslmode=disable \
    -s -r ${RAMP_TIME} -k 300  \
    -c ${CONCURRENCY_OLTP} -d ${DURATION} -p 26262 > ${LOGDIR}/heterogeneous-oltp.log 2>&1 &

# nohup dbworkload run -w ../dbworkload/DatapointOLAP.py \
#     --uri postgresql://root@localhost:${HETEROGENEOUS_PORT_OLAP}/oltaptest?sslmode=disable \
#     -s -r ${RAMP_TIME} \
#     -c ${CONCURRENCY_OLAP} -d ${DURATION} -p 26263 > ${LOGDIR}/heterogeneous-olap.log 2>&1 &

cd ..

