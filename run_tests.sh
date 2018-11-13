#!/bin/bash

python app.py & 
sleep 2
nosetests
pkill -9 python