import datetime
import json
import time
import requests
from lxml import etree

delay = 2  # 翻页延迟，防止屏蔽相应


class Tieba(object):

    def __init__(self, name):
        self.url = 'https://tieba.baidu.com/f?kw={}&ie=utf-8&pn=0'.format(name)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
            # 'User-Agent': 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)'
        }

    def get_data(self, url):
        response = requests.get(url, headers=self.headers)
        return response.content

    def parse_data(self, data):
        # 创建element对象
        data = data.decode().replace('<!--', '').replace('-->', '')
        html = etree.HTML(data)
        els = html.xpath('//li/div/div[2]/div[1]/div[1]/a')
        for el in els:
            temp = dict()
            temp['title'] = el.xpath('./text()')[0]
            temp['link'] = 'https://tieba.baidu.com' + el.xpath('./@href')[0]
            temp['user_info_list'] = self.get_user_info(temp['link'])
            self.save_data(temp)
            time.sleep(delay)
        # 获取下一页
        try:
            next_url = 'https:' + html.xpath('//a[contains(text(),"下一页>")]/@href')[0]
            # print(next_url)
        except Exception as e:
            print('未查找到最后一页或已经到尾页:', e)
            next_url = None
        return next_url

    def save_data(self, data):
        def save_and_log(string):
            print(string)
            string += '\n'
            with open('info.log', 'a', encoding='utf8') as f:
                f.write(string)

        save_and_log(datetime.datetime.now().strftime("========[%Y-%m-%d, %H:%M:%S]========"))
        save_and_log('①帖子标题：{0}\n②帖子链接：{1}\n③回帖人员信息：'.format(data['title'], data['link']))
        for user in data['user_info_list']:
            save_and_log('      昵称：{0:_<14}贴吧名：{1:_<14}贴吧等级：{2:_<9}唯一用户id:{3:}'.format(user['user_nickname'],
                                                                                       user['user_name'],
                                                                                       user['level'],
                                                                                       user['user_id']))

    def get_user_info(self, url):
        next_url = url
        post_user_list = []
        while True:
            data = self.get_data(next_url)
            data = data.decode()
            html = etree.HTML(data)
            els = html.xpath('//*[@id="j_p_postlist"]/div[@class="l_post l_post_bright j_l_post clearfix  "]')
            for el in els:
                post_user_data = {}
                data = json.loads(el.xpath('./@data-field')[0])
                post_user_data['user_id'] = data['author']['user_id']
                # 去重标记
                flag = False
                for post_user in post_user_list:
                    if post_user['user_id'] == post_user_data['user_id']:
                        flag = True
                if flag:
                    continue

                post_user_data['user_name'] = data['author']['user_name']
                post_user_data['user_nickname'] = data['author']['user_nickname']
                if post_user_data['user_nickname'] is None:
                    post_user_data['user_nickname'] = post_user_data['user_name']
                post_user_data['level'] = el.xpath('.//li[@class="l_badge"]//div[@class="d_badge_lv"]/text()')[0]
                post_user_list.append(post_user_data)
            # 获取下一页
            try:
                next_url = 'https://tieba.baidu.com' + html.xpath('//a[contains(text(),"下一页")]/@href')[0]
                # print('正在解析：', next_url)
            except Exception as e:
                # print('未查找到最后一页或已经到尾页:', e)
                next_url = None
            if next_url is None:
                return post_user_list

    def run(self):
        next_url = self.url
        while True:
            data = self.get_data(next_url)
            # 从响应中提取数据，获取下一页url
            data_list, next_url = self.parse_data(data)
            self.save_data(data_list)
            print(next_url)
            # 判断终结
            if next_url is None:
                break
            self.url = next_url
            time.sleep(delay)


if __name__ == '__main__':
    print('本程序完全开源，仅用作学习交流，切勿用作跨吧执法、轨道炮等非法用途，谢谢合作。。。\n')
    print('防止请求屏蔽，默认设置翻页延迟2s，日志信息保存在info.log文件\n\n需要修改练手的朋友请自行fork，项目地址：https://github.com/holwell/TieBa\n')
    name = input('请输入需要统计的吧名：')
    try:
        tieba = Tieba(name)
        tieba.run()
    except:
        print('访问频繁或出现解析错误')
    finally:
        input('程序已结束')
