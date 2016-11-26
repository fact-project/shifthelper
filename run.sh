#!/bin/bash
sleep 10 # give db time to start up
shifthelper_db_cloner &
sleep 10 # give the cloner some time to do the initial clone
shifthelper
