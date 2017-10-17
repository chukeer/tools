package main

import (
	"bytes"
	"encoding/binary"
	"flag"
	"fmt"
	"os"
)

var typeStr = flag.String("type", "", "stt编码消息类型")
var typeInt = flag.Int("type-int", 0, "netmsg消息类型")

func main() {
	flag.Parse()

	if len(os.Args) <= 1 {
		flag.Usage()
		return
	}

	if *typeInt < 0 && *typeStr == "" {
		flag.Usage()
		return
	}

	if *typeInt > 0 {
		buf := new(bytes.Buffer)
		binary.Write(buf, binary.LittleEndian, uint16(*typeInt))
		fmt.Println(fmt.Sprintf("netmsg_type=%d\n    tcp['(tcp[12]>>2)+8':2]=0x%x", *typeInt, buf.Bytes()))
	}

	if *typeStr != "" {
		fmt.Printf("type@=%s\n    tcp['(tcp[12]>>2)+12':4]=0x%x", *typeStr, "type")

		buffer := []byte(*typeStr)
		offset := 18 //  size[4] size[4] msgType[2] isCrypto[1] reserved[1] "type@="[6]
		for i := 0; i < len(buffer); i = i + 4 {
			length := 4
			if len(buffer)-i < 4 {
				length = len(buffer) - i
			}
			format := fmt.Sprintf(" and tcp['(tcp[12]>>2)+%d':%d]=0x%%x", offset, length)
			fmt.Printf("%s", fmt.Sprintf(format, buffer[i:i+length]))

			offset = offset + 4
		}
		fmt.Println()
	}

}
