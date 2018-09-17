# -*- coding: utf-8 -*-
# import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib2, urllib, re, string, sys, os, gzip, StringIO
import urllib, re, string, sys, os, gzip
from uuid import uuid4
from random import random,randint
from math import floor
import hashlib
import requests
import simplejson
from bs4 import BeautifulSoup
import json

# Plugin constants
# __addonname__ = "爱奇艺视频"
# __addonid__   = "plugin.video.iqiyi"
# __addon__     = xbmcaddon.Addon(id=__addonid__)

headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
           'Accept-Encoding': 'gzip, deflate, sdch, br',
           'Accept-Language': 'zh-CN,zh;q=0.8',
           'Connection': 'keep-alive',
           'Upgrade-Insecure-Requests': '1',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

channel = [['2','电视剧'],['1','电影'],['6','综艺'],['4','动漫'],['3','纪录片'],['8','游戏'],['25','资讯'],['7','娱乐'],['24','财经'],['16','网络电影'],['10','片花'],['5','音乐'],['28','军事'],['12','教育'],['17','体育'],['15','儿童'],['9','旅游'],['13','时尚'],['21','生活'],['26','汽车'],['22','搞笑'],['20','广告'],['27','原创'],['29','母婴'],['30','科技'],['31','脱口秀'],['32','健康']]

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
        res = requests.get(url, headers=headers)
        html = BeautifulSoup(res.content,'html.parser')
    except Exception as e: pass
    else:
        filters = html.find_all('div', class_='mod_sear_list')
        for div in filters:
            h3 = div.find('h3')
            if h3 is None or '频道' in h3.getText() or '搜索' in h3.getText(): continue
            lis = [(i.a.getText(),i.a.get('href').split('/')[-1]) for i in div.find_all('li') if '#' not in i.a.get('href') and i.a.getText() != '收起']

            # print(h3.getText()[:-1],json.dumps(lis))
            # li = xbmcgui.ListItem('name-- %s -- (选择)' % h3.getText()[:-1])
            # u = sys.argv[0]+"?mode=4&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&url="+urllib.quote_plus(json.dumps(lis))
            # xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)

        pageCount = html.find('div',class_='mod-page')
        if pageCount is not None:
            pages = pageCount.find_all('a')
            pages = [(i.getText(),i.get('href').split('/')[-1]) for i in pages]
            print(pages)
    finally:
        pass



    # print(res.text)
# params = getParams()
# mode = params.get('mode')
name = '电影'
id = '1'
cat = ''
area = ''
year = ''
order = '3'
paytype = '0'
num = '1'
page = '1'
url = None
thumb = None
# print(mode)

getContentList(name,id)
# if mode == None: getRootList()
# elif mode == '1': getContentList(name,id,page,cat,area,year,order,paytype)