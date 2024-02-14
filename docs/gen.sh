#!/usr/bin/env bash

rm source/mdb*rst source/modules.rst

export SPHINX_APIDOC_OPTIONS=members,show-inheritance
sphinx-apidoc -E -o source ../mdb

make clean > /dev/null
make html
