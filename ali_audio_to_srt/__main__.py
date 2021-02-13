# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021 Haujet Zhao

# 内存分析：
# @profile
# python -m memory_profiler __main__.py

import argparse
import os
import shlex
import subprocess
import sys
import configparser
import platform
import time
from pathlib import Path
from icecream import ic
from threading import Thread

from .AliOss import AliOss
from .AliTrans import AliTrans

# 这里从相对路径导入，在被 pyinstaller 打包时，需要换成绝对路径
# from .moduel import *



def main():
    配置文件 = Path(Path(__file__).absolute().parent) / 'config.ini'
    config = 检查配置文件(配置文件)

    不马上退出 = False
    if len(sys.argv) == 1:
        不马上退出 = True

        print(f'''
你没有输入任何文件，因此进入文字引导。
程序的用处主要是使用阿里云的录音文件识别服务
将视频或音频文件生成 SRT 字幕文件
''')
        print(f'\n请输入要处理的视频或音频文件')
        sys.argv.append(得到输入文件())

    parser = argparse.ArgumentParser(
        description='''功能：使用阿里云的录音文件识别服务将视频或音频文件生成 SRT 字幕文件''',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('Media', nargs='+',  type=str, help='可一次识别多个文件')

    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    parser.add_argument('-l', '--language', metavar='语言', type=str, default='', help='使用什么引擎，默认是配置文件中的第一个')

    args = parser.parse_args()

    if args.language == '':
        引擎 = config[config.sections()[0]]
    elif args.language not in config.sections():
        print(f'无法在配置文件中找到所指定语言 {args.language} 的 Api ，已配置的语言有：{config.sections()}，使用默认语言：{config.sections()[0]}')
        引擎 = config[config.sections()[0]]
    else:
        引擎 = config[args.language]
    print(f'所使用的配置文件路径：{配置文件}')
    print(f'使用引擎：{引擎.name}')

    # 检查引擎项是否有空项，如果有，就请用户重新填
    if not all(list(map(lambda x: x[1], list(引擎.items())))):
        print(f'检测到配置文件中的引擎有空项，请先在配置文件中将引擎信息填好，再重新运行')
        sys.exit()

    # if not any(list(引擎.items()))

    处理文件(args.Media, 引擎=引擎)

    if 不马上退出:
        input('\n所有任务处理完毕，按下回车结束程序')
    else:
        print('\n所有任务处理完毕')

def 检查配置文件(配置文件):
    config = configparser.ConfigParser()
    config.read(配置文件, encoding='utf-8')
    while not config.sections():
        with open(配置文件, 'w', encoding='utf-8') as f:
            config = configparser.ConfigParser()
            for section in ['中文', '英语']:
                config[section] = {}
                items = ['ali_Oss_Bucket_Name',
                         'ali_Oss_Endpoint_Domain',
                         'ali_Oss_Access_Key_Id',
                         'ali_Oss_Access_Key_Secret',
                         'ali_Api_App_Key',
                         'ali_Api_Access_Key_Id',
                         'ali_Api_Access_Key_Secret',
                         ]
                for item in items:
                    config[section][item] = ''
            config.write(f)
        print(f'检测到还没有配置文件，已生成配置模板，请先将配置文件填好，再进行识别\n配置文件路径：{配置文件}')
        if platform.system() == 'Windows':
            os.system(f'explorer /select, "{配置文件}"')
        input('按回车继续')
        config.read(配置文件, encoding='utf-8')
    return config

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

def 处理文件(files, 引擎):
    删除oss文件 = True
    线程列表 = []
    线程数 = 16
    files = list(filter(lambda x: os.path.exists(x), files))
    for index, file in enumerate(files):
        while len(线程列表) >= 线程数:
            time.sleep(1)
        print(f'\n总共有 {len(files)} 个文件需要识别，正在转码上传第 {index + 1} 个：{file}')
        # 生成 wav
        wav路径 = f'{os.path.splitext(file)[0]}_16000hz.wav'
        命令 = f'ffmpeg -y -hide_banner -i "{file}" -ac 1 -ar 16000 "{wav路径}"'
        subprocess.run(shlex.split(命令), stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        print(f'转码完成')

        # oss 初始化
        oss = 得到oss(ali_Oss_Bucket_Name            = 引擎['ali_Oss_Bucket_Name'],
                    ali_Oss_Endpoint_Domain        = 引擎['ali_Oss_Endpoint_Domain'],
                    ali_Oss_Access_Key_Id          = 引擎['ali_Oss_Access_Key_Id'],
                    ali_Oss_Access_Key_Secret      = 引擎['ali_Oss_Access_Key_Secret'])
        if not oss: return False

        # 上传 wav，得到 远程链接
        oss文件路径, 文件url链接 = 上传oss(wav路径, oss)
        print(f'上传完成，文件链接：{文件url链接}')

        # 删除本地 wav 文件
        os.remove(wav路径)

        # 初始化识别引擎
        识别引擎 = AliTrans(appKey=引擎['ali_Api_App_Key'],
                         language='',
                         accessKeyId=引擎['ali_Api_Access_Key_Id'],
                         accessKeySecret=引擎['ali_Api_Access_Key_Secret'])

        # 提交任务
        识别引擎.提交任务(文件url链接)
        print(f'第 {index + 1} 个文件 {file} 识别任务已提交')

        # 用新线程等待识别完成
        线程 = Wait_For_Response_To_Generate_Srt(file, 识别引擎, oss, oss文件路径, 文件url链接, 删除oss文件)
        线程列表.append(线程)
        线程.start()

    # 定时检测线程列表的状态
    print(f'\n所有任务线程已提交，等待识别完成')
    有线程在工作 = True
    lastTime = time.time()
    while 有线程在工作:
        thisTime = time.time()
        if thisTime - lastTime > 5:
            lastTime = thisTime
            print(f'\n各线程状况：')
            for index, 线程 in enumerate(线程列表):
                print(f'    {index}: {线程.状态} （{线程.文件}）')
                ...
        if all(list(map(lambda x: not x.is_alive(), 线程列表))): 有线程在工作 = False
        time.sleep(0.2)


def 得到oss(ali_Oss_Bucket_Name,
        ali_Oss_Endpoint_Domain,
        ali_Oss_Access_Key_Id,
        ali_Oss_Access_Key_Secret):
    oss = AliOss()
    try:
        oss.auth(bucketName=ali_Oss_Bucket_Name,
                 endpointDomain=ali_Oss_Endpoint_Domain,
                 accessKeyId=ali_Oss_Access_Key_Id,
                 accessKeySecret=ali_Oss_Access_Key_Secret)
    except Exception as e:
        print(f'oss验证出错：{e}\n请检查配置文件')
        return False
    return oss

def 上传oss(file, oss):
    # 确定当前日期
    localTime = time.localtime(time.time())
    year = localTime.tm_year
    month = localTime.tm_mon
    day = localTime.tm_mday

    文件名 = os.path.basename(file)

    上传目标路径 = f'{year}/{month}/{day}/{文件名}'

    # 上传音频文件 upload audio to cloud
    print(f'上传音频中\n    本地文件：{file}\n    目标路径：{上传目标路径}')
    文件url链接 = oss.upload(file, 上传目标路径)

    return 上传目标路径, 文件url链接


class Wait_For_Response_To_Generate_Srt(Thread):
    def __init__(self, 文件, 识别引擎, oss, oss文件路径, 文件url链接, 删除oss文件):
        super().__init__()
        self.文件 = 文件
        self.识别引擎 = 识别引擎
        self.oss = oss
        self.oss文件路径 = oss文件路径
        self.文件url链接 = 文件url链接
        self.删除oss文件 = 删除oss文件
        self.状态 = '排队中'

    def 轮询(self):
        while True:
            成功查询 = self.识别引擎.查询任务详情()
            if not 成功查询: break
            statusText = self.识别引擎.任务详情[self.识别引擎.KEY_STATUS_TEXT]
            if statusText == self.识别引擎.STATUS_RUNNING or statusText == self.识别引擎.STATUS_QUEUEING:
                # 继续轮询
                if statusText == self.识别引擎.STATUS_QUEUEING:
                    self.状态 = '排队中'
                elif statusText == self.识别引擎.STATUS_RUNNING:
                    self.状态 = '音频转文字中'
                time.sleep(3)
            else:
                self.状态 = '转换完成'
                break

    def run(self):
        轮询成功 = self.轮询()

        print(f'\n删除 oss 远端文件：{self.oss文件路径}')
        self.oss.delete(self.oss文件路径)

        任务详情 = self.识别引擎.任务详情
        srt内容 = self.识别引擎.结果转srt()


        srt文件 = os.path.splitext(self.文件)[0] + '.srt'
        print(f'写入文件：{srt文件}')
        with open(srt文件, 'w', encoding='utf-8') as f:
            f.write(srt内容)



if __name__ == '__main__':
    main()