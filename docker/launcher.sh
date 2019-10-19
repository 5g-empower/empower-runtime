#!/bin/sh

_term() {
  echo "Caught SIGTERM signal!"
  kill -TERM "$child"
}

trap _term SIGTERM

./empower-runtime-master/empower-runtime.py

child=$!

wait "$child"
