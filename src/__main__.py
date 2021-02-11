#coding=utf-8

# 程序名
#
# MIT License
#
# Copyright (c) 2021 Haujet Zhao
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# 内存分析：
# @profile
# python -m memory_profiler __main__.py

import argparse
import os
import shlex
import subprocess
import sys

# 这里从相对路径导入，在被 pyinstaller 打包时，需要换成绝对路径
from .moduel import *

def main():
    不马上退出 = False
    if len(sys.argv) == 1:
        不马上退出 = True

        print(f'''
你没有输入任何文件，因此进入文字引导。
程序的用处主要是***，例如：
  * ~~~
  * ~~~
''')
        print(f'\n首先输入 *** ')
        sys.argv.append(得到输入文件())

        print(f'\n再输入 *** ')
        sys.argv.append(得到输入文件())


    parser = argparse.ArgumentParser(
        description='''功能：*****  用途示例：  *****''',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('Audio', type=str, help='外置音频，只能输入一个')
    parser.add_argument('Video', nargs='+',  type=str, help='可一次添加多个文件')

    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    parser.add_argument('--time', metavar='Minutes', type=int, default=0, help='分钟数')
    parser.add_argument('--switch',action='store_true', help='开关')

    args = parser.parse_args()

    for index, video in enumerate(args.Video):
        print(f'\n总共有 {len(args.Video)} 个文件需要处理，正在对齐第 {index + 1} 个：{video}')
        处理文件(video)

    if 不马上退出:
        input('\n所有任务处理完毕，按下回车关闭窗口')

def 得到输入文件():
    while True:
        用户输入 = input(f'请输入文件路径 或 直接拖入：')
        if 用户输入 == '':
            continue
        if os.path.exists(用户输入.strip('\'"')):
            输入文件 = 用户输入.strip('\'"')
            break
        else:
            print('输入的文件不存在，请重新输入')
    return 输入文件

def 处理文件(file):
    ...

if __name__ == '__main__':
    main()