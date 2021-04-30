#!/bin/bash
export MPLBACKEND=agg
sleep 10 # give db time to start up
shifthelper_db_cloner &
sleep 20 # give the cloner some time to do the initial clone
shifthelper
