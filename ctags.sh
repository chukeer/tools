#!/bin/bash
if [ $# -ne 1 ];then
    exit 0
fi
dir=$1
CTAGS=~/bin/ctags
if [ -f tags ];then
    # 增量生成tags
    find $dir \( -name "*.cpp" -o -name "*.h" \) -cnewer tags | xargs -n 200 | xargs $CTAGS --sort=yes --c++-kinds=+p --fields=+iaS --extra=+q --language-force=C++ -a >/dev/null 2>&1
    if [ $? -eq 0 ];then
        # 有新增文件且执行成功，再全量生成tags并替换原来的tags文件
        rm -f tags.bak
        find $1 \( -name "*.cpp" -o -name "*.h" \) | xargs -n 200 | xargs $CTAGS --sort=yes --c++-kinds=+p --fields=+iaS --extra=+q --language-force=C++ -a -f tags.bak
        mv tags.bak tags
    fi
else
    # 生成全量文件tags
    find $dir \( -name "*.cpp" -o -name "*.h" \) | xargs -n 200 | xargs $CTAGS --sort=yes --c++-kinds=+p --fields=+iaS --extra=+q --language-force=C++
fi
