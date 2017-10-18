#!/bin/bash
function usage
{
cat << EOF
this is a wrapper of tcpdump, usage:
    tcpdump [<tcpdump_options>] [ int-type expression] [ txt-type expression ]
    int-type expression: int-type <type>, 指定netmsg消息的type值，类型为整数，如int-type 689
    txt-type expression: txt-type <type>, 指定txt消息的type值，类型为字符串，如txt-type loginreq

for example:
    tcpdump.sh -Xnn -i any port 8001 and int-type 689                         # 抓取8001端口netmsg消息类型为689的包
    tcpdump.sh -Xnn -i any port 8001 and txt-type loginreq                    # 抓取8001端口文本消息type@=loginreq的包
    tcpdump.sh -Xnn -i any port 8001 and txt-type ''                          # 抓取8001端口所有文本消息的包
    tcpdump.sh -Xnn -i any \( port 8001 or port 8002 \) and txt-type loginreq # 抓取8001和8002端口上文本消息type@=loginreq的包

EOF
tcpdump -h
}

function generate_int_type
{
    if [ $# -ne 1 ];then
        return 1
    fi

    echo $1 | grep -Eq "^[0-9]+$"
    if [ $? -ne 0 ];then
        return 1
    fi

    hex=`python -c "import struct;print struct.pack('<H', $1).encode('hex')"`
    if [ $? -ne 0 ];then
        return 1
    fi

    echo "tcp[(tcp[12]>>2)+8:2]=0x$hex"
}

function generate_txt_type
{
    if [ $# -eq 0 ];then
        echo -n "tcp[(tcp[12]>>2)+12:4]=0x74797065"
        return
    fi

    offset=18
    echo -n "( tcp[(tcp[12]>>2)+12:4]=0x74797065"
    echo -n $1 | hexdump -ve '4/1 "%02x" "\n"' | while read hex
    do
        len=`echo ${#hex}/2 | bc`
        echo -n " and tcp[(tcp[12]>>2)+$offset:$len]=0x$hex"
        offset=$(($offset+4))
    done
    echo -n " )"
}

declare -a argv
count=0
while [ $# -gt 0 ]
do
    if [ $1 = "int-type" ];then
        if [ $# -lt 2 ];then
            echo "int-type argument missing"
            exit 1
        fi
        argv[$count]=`generate_int_type $2`
        if [ $? -ne 0 ];then
            echo "int-type argument error:$2"
            exit 1
        fi
        shift 2
    elif [ $1 = "txt-type" ];then
        if [ $# -ne 2 ];then
            echo "txt-type arugment missing"
            exit 1
        fi
        argv[$count]=`generate_txt_type $2`
        if [ $? -ne 0 ];then
            echo "txt-type argument error:$2"
            exit 1
        fi
        shift 2
    elif [ $1 = "-h" ] || [ $1 = "--help" ];then
        usage
        exit 0
    else
        argv[$count]=$1
        shift
    fi
    let count++
done

echo tcpdump ${argv[@]}
tcpdump ${argv[@]}
