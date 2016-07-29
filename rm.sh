#!/bin/bash
trash_dir="$HOME/.Trash"
mkdir -p $trash_dir
rm_files=`echo "$*" | tr ' ' '\n' | grep -v "^-" | tr '\n' ' '`
if [ x"$rm_files" = x ];then
    echo "arg error!"
    exit 1
fi
date=`date +"%y-%m-%d_%H:%M:%S:%N"`
for file in $rm_files
do
    file_name=${file##*/}
    mv -f $file $trash_dir/$file_name.`date +%N`
done
