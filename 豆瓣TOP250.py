import requests
import re
import logging
from urllib.parse import urljoin
from os.path import exists
from os import makedirs
import json

#设置系统日志打印格式
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s: %(message)s')
BASE_URL = 'https://movie.douban.com/'                             #定义初始url
TOTAL_PAGE = 1                           #定义抓取的页面数量
RESULT_DIR = '豆瓣top250'                 #定义存储地址 
exists(RESULT_DIR) or makedirs(RESULT_DIR)#检测保存地址是否存在，没有则创建
HEADERS = {
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
}
#代理池
proxy = ''
proxies ={
    'http':'http://' + proxy,
    'https': 'https://' + proxy
}

#定义解析页面函数
def scrape_page(url):
    logging.info('开始抓取 %s...', url)
    try:
        rep = requests.get(url, headers=HEADERS)
        if rep.status_code == 200:
            return rep.text
        logging.error('%s无效状态码%s', url, rep.status_code)
    except requests.RequestException:
        logging.error('在抓取%s时出现错误', url, exc_info=True)

#定义循环爬取url函数
def scrape_index(page):
    index_url = f'{BASE_URL}/top250?start={page}&filter='
    return scrape_page(index_url)

#定义解析获取详细页面url的解析函数
def parse_index(html):
    pattern = re.compile('<a.*?href="(.*?)".*?class="title"', re.S)
    items = re.findall(pattern, html)
    if not items:
        return []
    for item in items:
        logging.info('获取到详细页面URL:%s', item)
        yield item

#定义获取详细页面内容的函数，包括封面地址、电影标题、种类、发布时间、剧情简介以及评分
def parse_detail(html):
    cover_pattern = re.compile('<a.*?class="nbgnbg".*?<img.*?src="(.*?)".*?</a>', re.S)#海报获取正则表达式
    name_pattern = re.compile('<h1>.*?property.*?>(.*?)</span>', re.S)#电影名
    catagories_pattern = re.compile('<span.*?property="v:genre">(.*?)</span>', re.S)#电影类型
    published_at_pattern = re.compile('<span.*?"v:initialReleaseDate".*?>(.*?)</span>')#上映时间
    score_pattern = re.compile('<div.*?typeof="v:Rating".*?property="v:average">(.*?)</strong>', re.S)#电影评分
    cover = re.search(cover_pattern, html).group(1).strip() if re.search(cover_pattern, html) else None
    name = re.search(name_pattern, html).group(1).strip() if re.search(name_pattern, html) else None
    catagories = re.findall(catagories_pattern, html) if re.findall(catagories_pattern, html) else []
    published = re.findall(published_at_pattern, html) if re.findall(published_at_pattern, html) else []
    score = re.search(score_pattern, html).group(1).strip() if re.search(score_pattern, html) else None

    return {
        '封面地址':cover,
        '电影名称':name,
        '电影种类':catagories,
        '上映时间':published,
        '电影评分':score
    }

#定义获取详细页面的函数
def scrape_detail(url):
    return scrape_page(url)

#定义存储函数
def save_data(data):
    name = data.get('电影名称')
    data_path = f'{RESULT_DIR}/{name}.json'
    json.dump(data, open(data_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

#定义main函数
def main():
    for i in range(0, TOTAL_PAGE+1):
        page = i * 25
        index_html = scrape_index(page)
        detail_urls = parse_index(index_html)
        # logging.info('详细页面URL:%s', list(detail_urls))
        for detail_url in detail_urls:
            detail_html = scrape_detail(detail_url)
            data = parse_detail(detail_html)
            logging.info('获取到的数据：%s', data)
            logging.info('开始保存爬取到的数据为json格式')
            save_data(data)
            logging.info('保存成功~')

if __name__ == "__main__":
    main()
