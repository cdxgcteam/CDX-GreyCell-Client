#! /bin/sh
Xvfb :99 &
export DISPLAY=:99
export PATH=$PATH:../bin
pypy run_client.py $1 $2 $3
ps | grep Xvfb | cut -d ' ' -f1 | xargs kill
