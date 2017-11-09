#!/bin/bash
function usage
{
cat << EOF
this is a wrapper of tcpdump, usage:
    tcpdump [<tcpdump_options>] [ int-type expression] [ txt-type expression ] [ stxt-type expression ]
    int-type expression: int-type <type>, 指定netmsg消息的type值，类型为整数，如int-type 689
    txt-type expression: txt-type <type>, 指定客户端txt消息的type值，类型为字符串，如txt-type loginreq
    stxt-type expression: stxt-type <type>, 指定server group消息里的txt消息的type值，类型为字符串，如stxt-type loginreq

for example:
    tcpdump.sh -Xnn -i any port 8001 and int-type 689                          # 抓取8001端口netmsg消息类型为689的包
    tcpdump.sh -Xnn -i any port 8001 and txt-type loginreq                     # 抓取8001端口文本消息type@=loginreq的包
    tcpdump.sh -Xnn -i any port 8001 and txt-type ''                           # 抓取8001端口所有客户端文本消息的包
    tcpdump.sh -Xnn -i any \( port 8001 or port 8002 \) and stxt-type loginreq # 抓取8001和8002端口上客户端文本消息type@=loginreq的包
    tcpdump.sh -Xnn -i any port 8001 and stxt-type ''                          # 抓取8001端口所有server group消息里的文本消息的包
    tcpdump.sh -Xnn -i any \( port 8001 or port 8002 \) and stxt-type loginreq # 抓取8001和8002端口上server group消息里的文本消息type@=loginreq的包

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
        return 
    elif [ $# -eq 1 ];then
        offset=$1
        echo -n "tcp[(tcp[12]>>2)+$offset:4]=0x74797065"
        return
    fi

    offset=$1
    echo -n "( tcp[(tcp[12]>>2)+$offset:4]=0x74797065"
    offset=$(($offset+6))
    echo -n $2 | hexdump -ve '4/1 "%02x" "\n"' | while read hex
    do
        # tcpdump: data size must be 1, 2, or 4
        len=`echo ${#hex}/2 | bc`
        if [ $len -eq 3 ];then
            echo -n " and tcp[(tcp[12]>>2)+$offset:2]=0x`echo -n $hex | head -c 4`"
            offset=$(($offset+2))
            echo -n " and tcp[(tcp[12]>>2)+$offset:1]=0x`echo -n $hex | tail -c 2`"
            offset=$(($offset+1))
        else
            echo -n " and tcp[(tcp[12]>>2)+$offset:$len]=0x$hex"
            offset=$(($offset+$len))
        fi
    done
    echo -n " )"
}

declare -a argv
count=0
while [ $# -gt 0 ]
do
    if [ "$1" = "int-type" ];then
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
    elif [ "$1" = "txt-type" ];then
        if [ $# -lt 2 ];then
            echo "txt-type arugment missing"
            exit 1
        fi
        argv[$count]=`generate_txt_type 12 $2`
        if [ $? -ne 0 ];then
            echo "txt-type argument error:$2"
            exit 1
        fi
        shift 2
    elif [ "$1" = "stxt-type" ];then
        if [ $# -lt 2 ];then
            echo "stxt-type arugment missing"
            exit 1
        fi
        argv[$count]=`generate_txt_type 32 $2`
        if [ $? -ne 0 ];then
            echo "stxt-type argument error:$2"
            exit 1
        fi
        shift 2
    elif [ "$1" = "-h" ] || [ "$1" = "--help" ];then
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
