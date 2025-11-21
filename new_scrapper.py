
import requests
from bs4 import BeautifulSoup
import time
import hmac
import hashlib
import base64
import json

DINGDING_WEBHOOK_BASE = "https://oapi.dingtalk.com/robot/send?access_token=193af1e88c7fb172acf94083149830a4bcfec8c5043ff0acee3622449861f603"
DINGDING_SECRET = "SECfa6cfd6d5a3484500b4e6d77bc2e6cb6fec14e510a7eda2257f1685a6bf76d9f"

def get_hot_news():
    """爬取百度热搜榜，并返回格式化的新闻列表"""
    url = "http://www.baidu.com"
    headers = {
        # 伪装成浏览器访问，防止被网站屏蔽
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        # 确保使用正确的编码，防止中文乱码
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        # 百度热搜的定位方式（可能会随网站更新而变化，需要自行调试）
        hot_wrapper = soup.find('div', id='s-hotsearch-wrapper')

        if not hot_wrapper:
            print("错误：未找到ID为：'s-hotsearch-wrapper'的父容器")
            return ['新闻爬取失败，定位失效']

        hot_list = hot_wrapper.find_all('li',class_='hotsearch-item')

        news_items = []
        # 只提取前10条
        for i, item in enumerate(hot_list[:10]):
            # 提取标题和链接，具体class需要根据实时网页结构调整
            title_tag = item.find('a')
            if title_tag:
                title_span = title_tag.find('span',class_='title-content-title')
                if title_span:
                    title= title_span.get_text(strip=True)
                else:
                    title=title_tag.get_text(strip=True)
                link = title_tag.get('href')
                news_items.append(f'{i+1}.[{title}]({link})')
                # title = title_tag.get_text(strip=True)
                # link = title_tag.get('href')
                # news_items.append(f"{i + 1}. [{title}]({link})")

        return news_items

    except Exception as e:
        print(f"爬取新闻时发生错误: {e}")
        return [f"新闻爬取失败，请检查脚本或网络连接。错误信息: {e}"]

def sign_dingding_request():
    # 获取当前时间戳（毫秒）
    timestamp = str(round(time.time()*1000))

    # 构造签名字符串： timestamp + "\n" +secret
    string_to_sign = '{}\n{}'.format(timestamp,DINGDING_SECRET)

    secret_bytes = DINGDING_SECRET.encode('utf-8')
    string_to_sign_bytes = string_to_sign.encode('utf-8')

    # 使用 HmacSHA256 进行哈希计算
    hmac_code = hmac.new(secret_bytes,string_to_sign_bytes,digestmod=hashlib.sha256).digest()

    # Base64 编码，并转换成字符串
    sign = base64.b64encode(hmac_code).decode('utf-8')

    return timestamp,sign

def send_dingding_message(news_list=None):
    timestamp,sign = sign_dingding_request()

    # 构造完整的URL，包含timestamp和sing参数
    url = f"{DINGDING_WEBHOOK_BASE}&timestamp={timestamp}&sign={sign}"

    # 构造Markdown格式的完整消息内容
    # 注意：Markdown格式要求内容之间用\n\n隔开
    markdown_text = (
        f"##📰每日热点新闻（{time.strftime('%Y-%m-%d')}）"
        f"**来源：**百度热搜"
        f"{''.join(news_list)}"
        f"---"
    )

    # 构造请求体（JSON Payload）
    headers = {'Content-Type':'application/json'}
    data = {
        'msgtype':'markdown',
        'markdown':{
            'title':f'【热点新闻】{time.strftime("%Y-%m-%d")}',
            'text':markdown_text,
        },
        'at':{
            'isAtAll':False # 是否需要@所有人，如果需要，则改为True
        }
    }

    print('正在发送钉钉消息...')
    try:
        response = requests.post(url,headers=headers,data=json.dumps(data),timeout=15)
        result = response.json()

        if result.get('errcode') == 0:
            print('【成功】消息发送成功')
            return True
        else:
            print('【失败】钉钉消息发送失败:{result}')
            return False
    except Exception as e:
        print(f'【失败】发送消息时发生网络错误:{e}')
        return False
    
def main_job(new_list=None):
    print(f"---任务开始：{time.strftime('%Y-%m-%d %H:%M:%S')}---")
    news_list = get_hot_news()
    
    # 仅在爬取有效内容是才发送，否则发送失败
    if news_list and len(news_list[0]) >20: # 假设有效新闻长度大于20字符，排除短的错误信息
        send_dingding_message(news_list)
    else:
        error_message = "❌每日新闻爬取失败，请手动检查脚本。详情："
        print(error_message)
        
    print('---任务结束---')
    


if __name__ == '__main__':
    main_job()
