#!/usr/bin/env bash

#### Building the directory to mount

echo "Remake selenzyme2 folder? yes:1, no:0"
read remake_selenzyme2
if [ $remake_selenzyme2 == 1 ]
then
	sudo rm -rf selenzyme2
	mkdir selenzyme2

	echo "\n     COPYING selenzyme2 code"
	cp -rp gitcode2023/* selenzyme2
	mkdir -p selenzyme2/selenzyPro

	echo "\n     COPYING selenzyme2 data"
	sudo rm -rf data_2023
	echo "unzipping data_2023.zip !!!"
	unzip compressed_data/data_2023.zip -d selenzyme2/selenzyPro/data/
	mv selenzyme2/selenzyPro/data/data_2023/* selenzyme2/selenzyPro/data/

	echo "unzipping seqs.zip"
	unzip compressed_data/seqs.zip -d selenzyme2/selenzyPro/data

	echo "\n     MAKING additional folders"
	mkdir -p selenzyme2/selenzyPro/log
	mkdir -p selenzyme2/selenzyPro/uploads 
else
	echo "Delete selenzyme2/uploads folder? yes:1, no:0"
	read delete_uploads

	if [ $delete_uploads == 1 ]
	then
		sudo rm -r selenzyme2/selenzyPro/uploads/*
	fi
fi


### The Docker bit 

# if nginx not running then start it
echo "restart nginx? yes:1, no:0"
read restart_nginx
if [ $restart_nginx == 1 ]
then
	docker run --name nginx-proxy -d -p 80:80 -p 88:7700 -v /var/run/docker.sock:/tmp/docker.sock:ro jwilder/nginx-proxy
fi


# remove any old images and containers
docker stop sbc/selenzybase2023
docker rm sbc/selenzybase2023
docker rmi sbc/selenzybase2023

docker stop selenzyme2023
docker rm selenzyme2023
docker rmi selenzyme_image


# Base container, build only once before installing selenzyme2
echo "\n     BUILDING sbc/selenzybase2 from Dockerfile.base"
docker build -t sbc/selenzybase2023 -f Dockerfile.base .

echo "\n     BUILDING selenzyme2"
docker build -t selenzyme_image -f Dockerfile .

DIR=$(cd "$(dirname "$0")"; pwd)
docker run --name selenzyme2023 -d -p 32784:5001 -e LD_LIBRARY_PATH='/opt/conda/bin/../lib' -e VIRTUAL_HOST=selenzymeRF.synbiochem.co.uk -v $DIR/selenzyme2:/selenzyme2 selenzyme_image

docker ps

echo ""
echo "finishing running but wait 5 mins to test website - stuff still loading in the background $(date -d "$TIME 5min" +"%H:%M:%S")"
echo "docker logs -t selenzyme2023 -n 10"
