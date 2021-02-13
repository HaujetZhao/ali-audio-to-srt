import os, subprocess, time, json, srt, datetime, re

from pprint import pprint

from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

class AliTrans():
    def __init__(self, appKey, language, accessKeyId, accessKeySecret):
        self.appKey = appKey
        # 地域ID，常量内容，请勿改变
        self.REGION_ID = "cn-shanghai"
        self.PRODUCT = "nls-filetrans"
        self.DOMAIN = "filetrans.cn-shanghai.aliyuncs.com"
        self.API_VERSION = "2018-08-17"
        self.POST_REQUEST_ACTION = "SubmitTask"
        self.GET_REQUEST_ACTION = "GetTaskResult"
        # 请求参数key
        self.KEY_APP_KEY = "appkey"
        self.KEY_FILE_LINK = "file_link"
        self.KEY_VERSION = "version"
        self.KEY_ENABLE_WORDS = "enable_words"
        # 是否开启智能分轨
        self.KEY_AUTO_SPLIT = "auto_split"
        # 响应参数key
        self.KEY_TASK = "Task"
        self.KEY_TASK_ID = "TaskId"
        self.KEY_STATUS_TEXT = "StatusText"
        self.KEY_RESULT = "Result"
        # 状态值
        self.STATUS_SUCCESS = "SUCCESS"
        self.STATUS_RUNNING = "RUNNING"
        self.STATUS_QUEUEING = "QUEUEING"
        # 创建AcsClient实例
        self.client = AcsClient(accessKeyId, accessKeySecret, self.REGION_ID)

        self.查询请求 = ''

        pass

    def 提交任务(self, 文件链接):
        # 提交录音文件识别请求
        postRequest = CommonRequest()
        postRequest.set_domain(self.DOMAIN)
        postRequest.set_version(self.API_VERSION)
        postRequest.set_product(self.PRODUCT)
        postRequest.set_action_name(self.POST_REQUEST_ACTION)
        postRequest.set_method('POST')
        # 新接入请使用4.0版本，已接入(默认2.0)如需维持现状，请注释掉该参数设置
        # 设置是否输出词信息，默认为false，开启时需要设置version为4.0
        task = {self.KEY_APP_KEY: self.appKey,
                self.KEY_FILE_LINK: 文件链接,
                self.KEY_VERSION: "4.0",
                self.KEY_ENABLE_WORDS: True,
                'max_single_segment_time': 10000}
        # 开启智能分轨，如果开启智能分轨 task中设置KEY_AUTO_SPLIT : True
        # task = {KEY_APP_KEY : appKey, KEY_FILE_LINK : fileLink, KEY_VERSION : "4.0", KEY_ENABLE_WORDS : False, KEY_AUTO_SPLIT : True}
        task = json.dumps(task)
        # print(task)
        postRequest.add_body_params(self.KEY_TASK, task)
        任务回执 = ""
        try:
            postResponse = self.client.do_action_with_exception(postRequest)
            postResponse = json.loads(postResponse)
            print(f'postResponse: {postResponse}')

            statusText = postResponse[self.KEY_STATUS_TEXT]

            if statusText == self.STATUS_SUCCESS:
                self.任务回执 = postResponse[self.KEY_TASK_ID]
                print(f'录音文件识别请求成功响应！\n    statusText: {statusText}\n    keyTaskId: {self.任务回执}')
                return True
            elif statusText == 'USER_BIZDURATION_QUOTA_EXCEED':
                print(f'你今天的阿里云识别额度已用完！\n    statusText: {statusText}')
                return False
            else:
                print(
                    f'录音文件识别请求失败，失败原因是：{statusText}，你可以将这个代码复制，到 “https://help.aliyun.com/document_detail/90727.html” 查询具体原因\n')
                return False
        except Exception as e:
            print(f'错误信息：\n    {e}')
            return False

    def 查询任务详情(self):
        if not self.查询请求:
            # 创建CommonRequest，设置任务ID
            self.查询请求 = CommonRequest()
            self.查询请求.set_domain(self.DOMAIN)
            self.查询请求.set_version(self.API_VERSION)
            self.查询请求.set_product(self.PRODUCT)
            self.查询请求.set_action_name(self.GET_REQUEST_ACTION)
            self.查询请求.set_method('GET')
            self.查询请求.add_query_param(self.KEY_TASK_ID, self.任务回执)
            # 提交录音文件识别结果查询请求
            # 以轮询的方式进行识别结果的查询，直到服务端返回的状态描述符为"SUCCESS"、"SUCCESS_WITH_NO_VALID_FRAGMENT"，
            # 或者为错误描述，则结束轮询。
        try:
            任务详情 = self.client.do_action_with_exception(self.查询请求)
            self.任务详情 = json.loads(任务详情)
        except Exception as e:
            print(e)
            return False
        return True

    def 轮询任务(self):
        while True:
            成功查询 = 查询任务详情()
            if not 成功查询: break
            statusText = self.任务详情[KEY_STATUS_TEXT]
            if statusText == STATUS_RUNNING or statusText == STATUS_QUEUEING:
                # 继续轮询
                if statusText == STATUS_QUEUEING:
                    print(f'任务 {任务回执} 正在排队中\n')
                elif statusText == STATUS_RUNNING:
                    print(f'任务 {任务回执} 正在音频转文字中\n')
                time.sleep(5)
            else:
                break
        return 成功查询

    def 结果转srt(self):
        # print(f'任务详情：')

        # pprint(self.任务详情)

        # 新建一个列表，用于存放字幕

        字幕全部文本 = ''
        for i in range(len(self.任务详情['Result']['Sentences'])):
            字幕全部文本 = 字幕全部文本 + self.任务详情['Result']['Sentences'][i]['Text']
        print(f'字幕文本：\n{字幕全部文本}')

        单词合并 = ''
        for i in range(len(self.任务详情['Result']['Words'])):
            单词合并 = 单词合并 + self.任务详情['Result']['Words'][i]['Word']
        print(f'单词合并：\n{单词合并}')

        字幕列表 = []
        for i in range(len(self.任务详情['Result']['Words'])):
            if i > 0:
                lastEndTime = EndTime
            Word = self.任务详情['Result']['Words'][i]['Word']
            BeginTime = self.任务详情['Result']['Words'][i]['BeginTime']
            EndTime = self.任务详情['Result']['Words'][i]['EndTime']
            if i == 0:
                开始时间 = BeginTime
                本句字幕内容 = Word
                字幕全部文本 = 字幕全部文本[len(Word):]
                continue

            if 字幕全部文本[0] == Word[0]:
                本句字幕内容 += Word
                字幕全部文本 = 字幕全部文本[len(Word):]
            else:
                if Word not in 字幕全部文本:
                    continue

                结束时间 = lastEndTime

                开始秒数 = 开始时间 // 1000
                开始毫秒数 = 开始时间 % 1000 * 1000
                结束秒数 = 结束时间 // 1000
                结束毫秒数 = 结束时间 % 1000 * 1000

                # 设定字幕起始时间
                if 开始秒数 == 0:
                    srt开始时间 = datetime.timedelta(microseconds=开始毫秒数)
                else:
                    srt开始时间 = datetime.timedelta(seconds=开始秒数, microseconds=开始毫秒数)

                # 设定字幕终止时间
                if 结束秒数 == 0:
                    srt结束时间 = datetime.timedelta(microseconds=结束毫秒数)
                else:
                    srt结束时间 = datetime.timedelta(seconds=结束秒数, microseconds=结束毫秒数)

                字幕列表.append(srt.Subtitle(index=i, start=srt开始时间, end=srt结束时间, content=本句字幕内容))

                本句字幕内容 = Word
                开始时间 = BeginTime
                删除次数 = 0
                while 字幕全部文本[0] != Word[0] and len(字幕全部文本) > len(Word):
                    字幕全部文本 = 字幕全部文本[1:]
                    删除次数 += 1
                字幕全部文本 = 字幕全部文本[len(Word):]

                # 以防有 bug，在这里中断：
                # if 删除次数 > 5:
                #     print('出问题了，返回的词和句子内容不同！')
                #     break

        字幕内容列表 = []
        for i in 字幕列表:
            字幕内容列表.append(i.content)
        print(f'优化后的字幕内容合并：')
        pprint(字幕内容列表)

        return srt.compose(字幕列表, reindex=True, start_index=1, strict=True)
