#! /bin/sh

set -e

/golem/john/run/john --format=raw-md5 /golem/work/in.hash --node=$1/$2 > /golem/work/log.txt 2>&1 

/golem/john/run/john --show --format=raw-md5 /golem/work/in.hash > /golem/work/out.txt