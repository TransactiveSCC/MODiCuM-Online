#!/bin/bash

docker run --rm --name stress-ng-app eiselesr/stress-ng-app \
#"pulsar://172.21.20.53:6650" customer_1 market_100 supplier_1 allocation_1 honest 1
##pulsar_url, tenant, namespace, user_uuid, allocation_uuid

#python3 app-shim.py "pulsar://172.21.20.70:6650" customer_1 market_11 supplier_1 allocation_1 honest 1