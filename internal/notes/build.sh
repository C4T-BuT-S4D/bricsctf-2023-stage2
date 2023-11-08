#!/bin/bash

docker build -t notes-builder .
docker run -d --name notes-builder-1 notes-builder
docker cp notes-builder-1:/build/userlib.so .
docker rm notes-builder-1
docker rmi notes-builder

mv ./userlib.so ../../services/notes/src/