#!/usr/bin/env bash
DIR=$(cd "$(dirname "$0")"; pwd)

docker stop selenzyme #$(docker ps -a -q)
docker rm selenzyme #$(docker ps -a -q)
docker rmi selenzyme #$(docker images -q)

sudo rm -rf selenzyme
rm selenzy.tar.gz

# Base container, build only once before installing selenzyme
#docker build -t sbc/selenzybase -f Dockerfile.base .

mkdir selenzyme
wget http://130.88.113.226/selenzy/selenzy.tar.gz
tar -xzvf selenzy.tar.gz -C selenzyme


docker build -t selenzyme .

docker run --name nginx-proxy -d -p 80:80 -p 88:7700 -v /var/run/docker.sock:/tmp/docker.sock:ro jwilder/nginx-proxy

docker run --name selenzyme -d -p :5000 -e LD_LIBRARY_PATH='/opt/conda/bin/../lib' -e VIRTUAL_HOST=selenzyme.synbiochem.co.uk -v $DIR/selenzyme:/selenzyme selenzyme

