#!/bin/bash
if [ $# -ne 3 ];then
    echo "usage:$0 character output_file file_size(Byte)"
    exit 1
fi

character=$1
output_file=$2
target_file_size=$3

echo "$character" | grep -Eq "^[a-zA-Z]$"
if [ $? -ne 0 ];then
    echo "$character is not a character!"
    exit 1
fi

echo "$character" | dd of=$output_file bs=1 count=1
while true
do
    cur_file_size=`du -b $output_file | awk '{print $1}'`
    if [ $cur_file_size -ge $target_file_size ];then
        break
    fi
    remain_bytes=`echo "$target_file_size-$cur_file_size" | bc`
    if [ $remain_bytes -ge $cur_file_size ];then
        cat $output_file | dd of=$output_file seek=1 bs=$cur_file_size count=1
    else
        dd if=$output_file of=$output_file seek=1 obs=$cur_file_size skip=1 ibs=$(($cur_file_size-$remain_bytes))
    fi
    if [ $? -ne 0 ];then
        break
    fi
done
