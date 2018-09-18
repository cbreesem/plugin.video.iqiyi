# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib2, urllib, re, string, sys, os, gzip, StringIO
# import urllib, re, string, sys, os, gzip
from uuid import uuid4
from random import random,randint
from math import floor
import hashlib
import requests
import simplejson
from bs4 import BeautifulSoup
import json

# Plugin constants
__addonname__ = "爱奇艺视频"
__addonid__   = "plugin.video.iqiyi"
__addon__     = xbmcaddon.Addon(id=__addonid__)

headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
           'Accept-Encoding': 'gzip, deflate, sdch, br',
           'Accept-Language': 'zh-CN,zh;q=0.8',
           'Connection': 'keep-alive',
           'Upgrade-Insecure-Requests': '1',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

channel = [['2','电视剧'],['1','电影'],['6','综艺'],['4','动漫'],['3','纪录片'],['8','游戏'],['25','资讯'],['7','娱乐'],['24','财经'],['16','网络电影'],['10','片花'],['5','音乐'],['28','军事'],['12','教育'],['17','体育'],['15','儿童'],['9','旅游'],['13','时尚'],['21','生活'],['26','汽车'],['22','搞笑'],['20','广告'],['27','原创'],['29','母婴'],['30','科技'],['31','脱口秀'],['32','健康']]

def GetHttpData(url,header=headers):
    req = urllib2.Request(url,headers=header)
    try:
        response = urllib2.urlopen(req)
        httpdata = response.read()
        if response.headers.get('content-encoding', None) == 'gzip':
            httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
        charset = response.headers.getparam('charset')
        response.close()
    except:
        xbmc.log( "%s: %s (%d) [%s]" % (
            __addonname__,
            sys.exc_info()[ 2 ].tb_frame.f_code.co_name,
            sys.exc_info()[ 2 ].tb_lineno,
            sys.exc_info()[ 1 ]
            ), level=xbmc.LOGERROR)
        return ''
    match = re.compile('<meta http-equiv=["]?[Cc]ontent-[Tt]ype["]? content="text/html;[\s]?charset=(.+?)"').findall(httpdata)
    if len(match)>0:
        charset = match[0]
    if charset:
        charset = charset.lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = httpdata.decode(charset, 'ignore').encode('utf8', 'ignore')
    return httpdata


def getParams():
    param = {}
    paramstring = sys.argv[2] if len(sys.argv) >= 3 else []
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param

def getRootList():
    for id,name in channel:
        li = xbmcgui.ListItem(name)
        u = sys.argv[0]+"?mode=1&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)
        xbmc.log(u)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getContentList(name,id,url='----------------iqiyi--.html'):
    url = 'http://list.iqiyi.com/www/%s/%s' % (id, url)
    try:
        res = GetHttpData(url)
        html = BeautifulSoup(res.content,'html.parser')
    except Exception as e: pass
    else:
        filters = html.find_all('div', class_='mod_sear_list')
        for div in filters:
            h3 = div.find('h3')
            if h3 is None or '频道' in h3.getText() or '搜索' in h3.getText(): continue
            lis = [(i.a.getText(),i.a.get('href').split('/')[-1]) for i in div.find_all('li') if '#' not in i.a.get('href') and i.a.getText() != '收起']

            # print(h3.getText()[:-1],json.dumps(lis))
            li = xbmcgui.ListItem('name-- %s -- (选择)' % h3.getText()[:-1])
            u = sys.argv[0]+"?mode=4&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&url="+urllib.quote_plus(json.dumps(lis))
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)

        pageCount = html.find('div',class_='mod-page')
        if pageCount is not None:
            pages = pageCount.find_all('a')
            pages = [(i.getText(),i.get('href').split('/')[-1]) for i in pages]
            # print(pages)

        content = html.find('div',class_='wrapper-piclist')
        content = content.find_all('li')
        for i in content:
            pid = i.find('div',class_='site-piclist_pic').a.get('data-qidanadd-albumid') # 影片id
            episode = i.find('div',class_='site-piclist_pic').a.get('data-qidanadd-episode') == '1'

            thumb = i.find('div',class_='site-piclist_pic').a.img.get('src')  # 缩略图地址
            name = i.find('div',class_='site-piclist_pic').a.img.get('alt') # 名称
            rating = i.find('span',class_='score').getText()    # 评分
            cast = [i.getText().replace('\n','').replace('\r','').strip() for i in i.find_all('em') if '主演' not in i.getText()] # 演员表
            pianchang = i.find('span',class_='icon-vInfo').getText().strip() # 片长或者更新情况

            if '更新至第' in pianchang or '共' in pianchang:
                name += '(%s)' % pianchang
                episode = True

            mode,isdir = (2,True) if episode else (3,False)

            li = xbmcgui.ListItem(str(i + 1) + '.' + name, iconImage = '', thumbnailImage = thumb)
            u = sys.argv[0]+"?mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(pid)+"&thumb="+urllib.quote_plus(thumb)
            li.setInfo(type = "Video", infoLabels = {"Title":name, "Cast":','.join(cast), "Rating":rating})
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, isdir, totalItems)
    finally:
        pass

params = getParams()
mode = params.get('mode')
name = params.get('name')
id = params.get('id')

if mode == None: getRootList()
elif mode == '1': getContentList(name,id)