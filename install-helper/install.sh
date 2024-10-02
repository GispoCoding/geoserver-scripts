#!/bin/bash

# Up/downgrade a Geoserver running under Tomcat on Ubuntu.
# We assume the GEOSERVER_DATA_DIR is external to the Geoserver install AND
# set externally, e.g. in /usr/share/tomcat9/bin/setenv.sh
# See download.sh for how to fill the source directory.

TOMCAT_SERVICE=tomcat9
TOMCAT_ROOT=/var/lib/tomcat9/webapps
BACKUP=/tmp/geoserver-$(date +'%F:%H.%M.%S').tgz

howmany() { echo -n $#; }

if [ $# == 0 ] ; then
    echo "Usage: $0 directory"
    exit 1
elif [ ! -d $1 ] ; then
    echo "Directory $1 not found"
    exit 1
elif [ ! -f $1/geoserver.war ] ; then
    echo "No geoserver.war in $1"
    exit 1
fi

SRCDIR=$1

JARS=$(ls $SRCDIR/plugin-jars/*.jar)

echo ""
echo "geoserver.war and " $(howmany $JARS) " jars to copy from $1. OK?"
select yesno in "Yes" "No" ; do
    case $yesno in
        Yes ) echo "Proceeding with install."
	      break
	      ;;
        No ) exit
	     ;;
    esac
done

if systemctl --quiet is-active $TOMCAT_SERVICE ; then 
    # Stop Tomcat and let's hope nothing we need is under the geoserver path
    echo "Stopping Tomcat"	     
    sudo systemctl stop $TOMCAT_SERVICE
fi

echo "Backing up and removing Geoserver directory"
tar czf $BACKUP $TOMCAT_ROOT/geoserver*
sudo rm -rf $TOMCAT_ROOT/geoserver*
echo "Installing geoserver.war"
sudo cp $SRCDIR/geoserver.war $TOMCAT_ROOT
echo "Starting Tomcat." 
sudo systemctl start $TOMCAT_SERVICE
sleep 3
if ! systemctl --quiet is-active $TOMCAT_SERVICE ; then 
    echo "Tomcat not running. Aborting."
    exit 1
fi

echo "" 
echo "Now would be a good time to check the logs. Is all OK?"
select yesno in "Yes" "No" ; do
    case $yesno in
        Yes ) echo "Nice to hear. Proceeding with install."
	      break
	      ;;
        No ) echo "You might want to restore manually from $BACKUP"
	     exit
	     ;;
    esac
done

if [ ! -z "$JARS" ]  ; then 
    echo "Installing jars"
    if ! [ -d $TOMCAT_ROOT/geoserver/WEB-INF/lib ] ; then
	echo "No lib dir? Is geoserver OK? Aborting."
	exit 1
    fi
    
    for J in $JARS ; do
	JAR=$(basename $J)
	echo " - $JAR"
	sudo cp $J $TOMCAT_ROOT/geoserver/WEB-INF/lib
	sudo chown tomcat.tomcat $TOMCAT_ROOT/geoserver/WEB-INF/lib/$JAR
    done
    sudo systemctl reload-or-restart $TOMCAT_SERVICE
fi

echo "Done."
exit 0
