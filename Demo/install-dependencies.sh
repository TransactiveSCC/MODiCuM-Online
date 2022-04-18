#!/bin/bash
set -o allexport; source .env; set +o allexport


mkdir -p $PULSAR_DEPEN
cd $PULSAR_DEPEN
git clone https://github.com/apache/pulsar-helm-chart;\
git clone git@github.com:streamnative/charts.git;\
