#!/bin/bash

cd $REPO

docker build -t gem-bimbingbung .

docker tag -f gem-bimbingbung qa-mesos-persistence.za.prk-host.net:5000/gem-bimbingbung

docker push qa-mesos-persistence.za.prk-host.net:5000/gem-bimbingbung
