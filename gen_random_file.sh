#!/bin/bash
if [ $# -ne 2 ];then
    echo "usage:$0 file file_size"
    echo "      $0 xx 123"
    echo "      $0 xx 123K"
    echo "      $0 xx 123M"
    exit 1
fi

target_file=$1
/bin/rm -f $target_file

file_size=$2

echo "$file_size" | grep -Eq "^[0-9]+[kKmM]?$"
if [ $? -ne 0 ];then
    echo "file_size[$file_size] error! Please use 123 or 123K or 123M"
    exit 1
fi

echo "$file_size" | grep -qE "^[0-9]+[mM]$"
if [ $? -eq 0 ];then
    block_size=1M
    tmp_file=/tmp/tmp.$$
    dd if=/dev/urandom of=$tmp_file bs=$block_size count=1
    count=`echo "$file_size" | grep -Eo "^[0-9]+"`
    seq $count | xargs -I{} cat $tmp_file >> $target_file
    /bin/rm -f $tmp_file
else
    block_size=$file_size
    dd if=/dev/urandom of=$target_file bs=$block_size count=1
fi
