#!/bin/sh
./update_version.py
./compile_resources.sh
rm -rf dist
python3 -m build
#python3 setup.py build