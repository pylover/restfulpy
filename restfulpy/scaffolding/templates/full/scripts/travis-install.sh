#!/usr/bin/env bash


pip3 install -U pip setuptools wheel cython
pip3 install -r requirements-dev.txt
pip3 install -e .
