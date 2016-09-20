#!/bin/env python
"""
    Usage:
        zk.py create      <zoo_path> <data> [--acl=<acl>]  [-H HOSTS] [-a AUTH_DATA] 
        zk.py create_long <zoo_path> [-H HOSTS] [-a AUTH_DATA]
        zk.py set_acl     <zoo_path> <user_name> <password>
        zk.py put_file    <zoo_path> <local_file> [-H HOSTS] [-a AUTH_DATA]
        zk.py put_str     <zoo_path> <string_buf> [-H HOSTS] [-a AUTH_DATA]
        zk.py put_dir     <zoo_path>  <local_dir>  [-H HOSTS] [-a AUTH_DATA]
        zk.py get         <zoo_path> <local_file> [-H HOSTS] [-a AUTH_DATA]
        zk.py get_dir     <zoo_path>  <local_dir>  [-H HOSTS] [-a AUTH_DATA]
        zk.py cat         <zoo_path> [-H HOSTS] [-a AUTH_DATA]
        zk.py cp          <zoo_path_src> <zoo_path_dst> [-H HOSTS] [-a AUTH_DATA]
        zk.py mv          <zoo_path_src> <zoo_path_dst> [-H HOSTS] [-a AUTH_DATA]
        zk.py rm          <zoo_path> [-H HOSTS] [-a AUTH_DATA]
        zk.py rmr         <zoo_path>  [-H HOSTS] [-a AUTH_DATA]
        zk.py ls          <zoo_path> [-H HOSTS] [-a AUTH_DATA]
        zk.py update_file <zoo_path> <local_file> [-H HOSTS] [-a AUTH_DATA]
        zk.py update_dir  <zoo_path> <local_dir> [-H HOSTS] [-a AUTH_DATA]
        zk.py exist       <zoo_path> [-H HOSTS] [-a AUTH_DATA]

    Options:
        -h --help      Show this screen.
        -v --version   Show version.
        -H HOSTS       Zookeeper server hosts [default: 192.168.2.2:2181].
        -a AUTH_DATA   Zookeeper auth, format like user_name:password [default: guest:guest123].

"""

from docopt import docopt
import sys
import os
import time
import hashlib
from kazoo.client import KazooClient
from kazoo.security import *
from kazoo.exceptions import *
from kazoo.security import *

class ZKClient():

    def __init__(self, hosts, auth_data=None):
        if auth_data:
            auth_data = [('digest', auth_data)] 
        self.zk = KazooClient(hosts=hosts, auth_data=auth_data)
        self.zk.start()

    def __del__(self):
        self.zk.stop()

    def exist(self, zoo_path):
        ret = self.zk.exists(zoo_path)
        if ret:
            print True
        else:
            print False
        return ret

    def mv(self, zoo_path_src, zoo_path_dst):
        if self.zk.exists(zoo_path_dst):
            print '%s exists! Please delete it manually'
            return False
        if self.cp(zoo_path_src, zoo_path_dst):
            self.rmr(zoo_path_src)
        else:
            self.rmr(zoo_path_dst)

    def cp(self, zoo_path_src, zoo_path_dst):
        if not self.zk.exists(zoo_path_src):
            print '%s does not exist!' % zoo_path_src
            return False
        src_name = filter(lambda x:x, zoo_path_src.split('/'))[-1]
        try:
            children = self.zk.get_children(zoo_path_dst)
            if children:
                zoo_path_dst = zoo_path_dst + '/' + src_name
        except NoNodeError, e:
            pass
        children = self.zk.get_children(zoo_path_src)
        if not children:
            buf = self.__get_zk_file(zoo_path_src)
            src_name = filter(lambda x:x, zoo_path_src.split('/'))[-1]
            try:
                dst_is_dir = self.zk.get_children(zoo_path_dst)
                if dst_is_dir:
                    dst_path = zoo_path_dst + '/' + src_name
                else:
                    dst_path = zoo_path_dst
                self.put_str(dst_path, buf)
            except NoNodeError, e:
                self.create_long(zoo_path_dst)
                self.put_str(zoo_path_dst, buf)
        else:
            for child in children:
                self.cp(zoo_path_src + '/' + child, zoo_path_dst + '/' + child)
        return True


    def update_file(self, zoo_path, local_file):
        if not self.zk.exists(zoo_path): 
            return  self.put_file(zoo_path, local_file)
        else:
            zoo_buf = self.__get_zk_file(zoo_path)
            if not zoo_buf:
                return False
            else:
                local_buf = open(local_file).read()
                if hashlib.sha224(local_buf).hexdigest() != hashlib.sha224(zoo_buf).hexdigest():
                    print 'changed, %s -> %s' % (zoo_path, local_file)
                    return self.put_str(zoo_path, local_buf)
                else:
                    print 'same, %s = %s' % (zoo_path, local_file)

    def update_dir(self, zoo_path, local_dir):
        if not self.zk.exists(zoo_path):
            return self.put_dir(zoo_path, local_dir)
        for file_name in os.listdir(local_dir):
            tmp_zoo_path = zoo_path + '/' + file_name
            local_file = local_dir + '/' + file_name
            if os.path.isfile(local_file):
                self.update_file(tmp_zoo_path, local_file)
            elif os.path.isdir(local_file):
                self.update_dir(tmp_zoo_path, local_file)


    def create(self, zoo_path, data, acl=None):
        if acl:
            f = acl.split(':')
            if len(f) != 2:
                print 'acl[%s] format error. using like user:passwd' % acl
                return
            acl = [make_digest_acl(f[0], f[1], all=True)]
        return self.zk.create(str(zoo_path), str(data), acl)

    def create_long(self, zoo_path):
        field = filter(lambda x:x, zoo_path.split('/'))
        tmp_path = ''
        for name in field:
            tmp_path = tmp_path + '/' + name
            if not self.zk.exists(tmp_path):
                self.create(tmp_path, name)

    def set_acl(self, zoo_path, user_name, password):
        if not self.zk.exists(zoo_path):
            print '%s does not exist!' % zoo_path
            return
        acl = [make_digest_acl(user_name, password, all=True)]
        return self.zk.set_acls(zoo_path, acl)
    
    def ls(self, zoo_path):
        try:
            children = self.zk.get_children(zoo_path)
            zoo_path = '/' + '/'.join(filter(lambda x: x, zoo_path.split('/')))
            if zoo_path == '/':
                zoo_path = ''
            return sorted([zoo_path + '/' + child for child in children])
        except NoNodeError, e:
            print '%s does not exist!' % zoo_path
        except NoAuthError, e:
            print '%s auth error!' % zoo_path

    def cat(self, zoo_path):
        return self.__get_zk_file(zoo_path)

    def get(self, zoo_path, local_file):
        return self.__get_zk_file(zoo_path, local_file)

    def put_str(self, zoo_path, buffer):
        if not self.zk.exists(zoo_path):
            self.zk.create(zoo_path, buffer)
        else:
            self.zk.set(zoo_path, buffer)

    def put_file(self, zoo_path, local_file):
        buffer = open(local_file).read()
        return self.put_str(zoo_path, buffer)

    def rm(self, zoo_path):
        try:
            self.zk.delete(zoo_path)
        except NoNodeError, e:
            print '%s does not exist!' % zoo_path
        except NotEmptyError, e:
            print '%s has children!' % zoo_path

    def rmr(self, zoo_path):
        try:
            self.zk.delete(zoo_path, recursive=True)
        except NoNodeError, e:
            print '%s does not exist!' % zoo_path

    def __get_zk_file(self, zoo_path, local_file=None):
        try:
            buffer, znode_state = self.zk.get(zoo_path)
            if local_file:
                try:
                    with open(local_file, 'w') as file:
                        file.write(buffer)
                except:
                    print 'open %s failed!' % local_file
            else:
                return buffer
        except NoNodeError, e:
            print '%s does not exist!' % zoo_path
        except NoAuthError, e:
            print '%s auth error!' % zoo_path

    def get_dir(self, zoo_path, local_dir):
        try:
            children = self.zk.get_children(zoo_path)
        except NoNodeError, e:
            print '%s does not exist!' % zoo_path
            return
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)
        elif os.path.isfile(local_dir):
            print '%s is file, not dir!' % local_dir
            return
        for child in children:
            tmp_zoo_path = zoo_path + '/' + child
            local_file = local_dir + '/' + child
            children = self.zk.get_children(tmp_zoo_path)
            if children:
                self.get_dir(tmp_zoo_path, local_file) 
            else:
                self.__get_zk_file(tmp_zoo_path, local_file)

    def put_dir(self, zoo_path, local_dir):
        if not self.zk.exists(zoo_path):
            self.zk.create(zoo_path, str(time.time()))
        else:
            local_dir_name = filter(lambda x:x, local_dir.split('/'))[-1]
            zoo_path = zoo_path + '/' + local_dir_name
            if not self.zk.exists(zoo_path):
                self.zk.create(zoo_path, str(time.time()))
        for file_name in os.listdir(local_dir):
            tmp_zoo_path = zoo_path + '/' + file_name
            local_file = local_dir + '/' + file_name
            if os.path.isfile(local_file):
                self.put_file(tmp_zoo_path, local_file)
            elif os.path.isdir(local_file):
                self.put_dir(tmp_zoo_path, local_file)

if __name__ == '__main__':
    arguments = docopt(__doc__, version='python zookeeper client 1.0.0.0')

    zk = ZKClient(arguments['-H'], arguments['-a'])

    if arguments['create']:
        zk.create(arguments['<zoo_path>'], arguments['<data>'], arguments['--acl'])
    elif arguments['create_long']:
        zk.create_long(arguments['<zoo_path>'])
    elif arguments['set_acl']:
        zk.set_acl(arguments['<zoo_path>'], arguments['<user_name>'], arguments['<password>'])
    elif arguments['put_file']:
        zk.put_file(arguments['<zoo_path>'], arguments['<local_file>'])
    elif arguments['put_str']:
        zk.put_str(arguments['<zoo_path>'], arguments['<string_buf>'])
    elif arguments['put_dir']:
        zk.put_dir(arguments['<zoo_path>'], arguments['<local_dir>'])
    elif arguments['get_dir']:
        zk.get_dir(arguments['<zoo_path>'], arguments['<local_dir>'])
    elif arguments['get']:
        zk.get(arguments['<zoo_path>'], arguments['<local_file>'])
    elif arguments['cat']:
        print zk.cat(arguments['<zoo_path>'])
    elif arguments['rm']:
        zk.rm(arguments['<zoo_path>'])
    elif arguments['rmr']:
        zk.rmr(arguments['<zoo_path>'])
    elif arguments['ls']:
        ret = zk.ls(arguments['<zoo_path>'])
        if ret:
            print '\n'.join(ret)
    elif arguments['exist']:
        zk.exist(arguments['<zoo_path>'])
    elif arguments['update_file']:
        zk.update_file(arguments['<zoo_path>'], arguments['<local_file>'])
    elif arguments['update_dir']:
        zk.update_dir(arguments['<zoo_path>'], arguments['<local_dir>'])
    elif arguments['cp']:
        zk.cp(arguments['<zoo_path_src>'], arguments['<zoo_path_dst>'])
    elif arguments['mv']:
        zk.mv(arguments['<zoo_path_src>'], arguments['<zoo_path_dst>'])
