
# Geoserver install helper

This is a crude installer thing for when you want to upgrade Geoserver through multiple versions. It is said it's safer to do small increments and not jump too far.
The assumption is that you run Geoserver using a WAR file under Tomcat 9 on Ubuntu (tested on 22.04). 
NB! THIS DOESN'T CHECK FOR THE DATA DIRECTORY. The data directory should be external to the Geoserver directory, as should the location of its configuration.

## Download

Adjust the versions and plugins you want to download in download.sh and run the script. The files will be downloaded into a subdirectory named after the version, e.g. 2.22.2. The WAR file will be in the subdirectory and the JAR files from the plugins will be in a further subdirectory called plugin-jars.

## Install

Run install.sh followed by a directory downloaded in the previous step, or one containing a geoserver.war file.
