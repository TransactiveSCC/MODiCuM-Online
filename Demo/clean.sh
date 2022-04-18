#!/bin/bash

influx delete --bucket modicumdb --start '1970-01-01T00:00:00Z' --stop $(date +"%Y-%m-%dT%H:%M:%SZ") --predicate '_measurement="Events"'
