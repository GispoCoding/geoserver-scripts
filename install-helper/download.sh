#!/bin/bash

# Batch downloader for multiple Geoserver versions with extensions.

# Adjust to fit
VERSIONS="2.17.5 2.18.5 2.19.5 2.20.6 2.21.4"
PLUGINS="css monitor pyramid ysld"

for V in $VERSIONS ; do
    mkdir $V
    pushd $V
    wget https://sourceforge.net/projects/geoserver/files/GeoServer/$V/geoserver-$V-war.zip/download -O geoserver-$V-war.zip
    unzip geoserver-$V-war.zip geoserver.war 

    mkdir plugin-jars
    for P in $PLUGINS ; do
	wget https://sourceforge.net/projects/geoserver/files/GeoServer/$V/extensions/geoserver-$V-$P-plugin.zip/download -O geoserver-$V-$P-plugin.zip
	unzip -o geoserver-$V-$P-plugin.zip '*.jar' -d plugin-jars 
    done
    
    popd
done
