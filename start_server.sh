#!/usr/bin/env bash
DIR=$(cd "$(dirname "$0")"; pwd)

docker stop $(docker ps -a -q)
docker rm $(docker ps -a -q)
docker rmi $(docker images -q)

rm -rf selenzyme
mkdir selenzyme
wget http://130.88.113.226/selenzy/selenzy.tar.gz
tar -xzvf selenzy.tar.gz -C selenzyme

docker build -t selenzyme .

docker run --name nginx-proxy -d -p 80:80 -p 88:7700 -v /var/run/docker.sock:/tmp/docker.sock:ro jwilder/nginx-proxy

docker run --name selenzyme -d -p :5000 -e LD_LIBRARY_PATH='/opt/conda/bin/../lib' -e VIRTUAL_HOST=selenzyme.synbiochem.co.uk -v $DIR/selenzyme:/selenzyme selenzyme

# Selprom

GITLAB=ssh://gitlab@gitlab.cs.man.ac.uk:22222/pablo-carbonell
GITHUB=https://github.com/synbiochem/selprom.git
# Run script from its folder
CWD=$PWD
# Define repository location
REPO=$GITLAB/sbc-prom.git

# Clone production server
rm -rf sbc-prom
git clone $REPO sbc-prom
cd sbc-prom
git checkout -b prod origin/prod
cd $CWD

# Clone container 
git clone $GITHUB selprom
cd selprom

docker build -t selprom .

# Run container with user's uid to avoid permission issues when updating the repository
docker run -u `id -u $USER` --name selprom -d -p 7700:7700 -e LD_LIBRARY_PATH='/opt/conda/bin/../lib' -v $CWD/sbc-prom:/selprom selprom 
