#!/bin/bash

for file in $(cat list.txt)
# Content in list.txt like as:
# ./drupal/CVE-2019-6341/docker-compose.yml
# ./drupal/CVE-2014-3704/docker-compose.yml
# ./drupal/CVE-2018-7600/docker-compose.yml
# ./apereo-cas/4.1-rce/docker-compose.yml
# U can use command  <find ./ -name "*.yml"> to get it.
do
	file_backup=$file".backup"
	cp $file $file_backup
  
  #Parsing file path
	pre_path="vulns_app"
	app=`echo $file_backup |awk -F '/' '{print $2}' | tr '[A-Z]' '[a-z]'`
	app_path=$pre_path"/"$app
	cve=`echo $file_backup |awk -F '/' '{print $3}' | tr '[A-Z]' '[a-z]'`
	cve2=`echo $file_backup |awk -F '/' '{print $3}'`
	cve_path=$app_path"/"$cve2
	
  #Create directory
	if [ ! -d $pre_path ];then
		mkdir $pre_path
	fi
	if [ ! -d $app_path ];then
		mkdir $app_path
	fi
	if [ ! -d $cve_path ];then
		mkdir $cve_path
	fi
	
  #Convert docker-compose.yml to K8s-yaml
  outpath=$cve_path"/"
	output_file=$cve_path"/"$cve".yaml"
	home_path=`pwd`"/"
	kompose convert -f $file_backup -o $output_file --volumes hostPath
	sed -i "s!$home_path!!g" $output_file
	
  #Create desc.yaml
  
  touch $outpath/desc.yaml
	str="cve"
	if [[ $cve == *$str* ]];then
	    name=$cve
	else
	    name=$app"-"$cve
	fi
  echo "name:  "$name >> $outpath/desc.yaml
  echo "class:  "$app >> $outpath/desc.yaml
  echo "type:  rce" >> $outpath/desc.yaml
	key_path='volumes:'
	if [[ `grep $key_path $file_backup` ]];then
	    echo "hostPath: true" >> $outpath/desc.yaml
	fi
  echo "dependencies:" >> $outpath/desc.yaml
  echo "  yamls:" >> $outpath/desc.yaml
  for d in $(ls $outpath*.yaml);do
    list=`echo $d |awk -F '/' '{print $4}'`
    if [ $list != "desc.yaml" ];then
	    echo "    - "$list >> $outpath/desc.yaml
	  fi
	done
  echo "links:" >> $outpath/desc.yaml
  echo "  - https://github.com/vulhub/vulhub/tree/master/"$app"/"$cve2 >> $outpath/desc.yaml
	
  rm -f $file_backup

done