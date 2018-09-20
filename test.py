# -*- coding: utf-8 -*-
# import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import urllib, urllib2, re, string, sys, os, gzip, StringIO
from uuid import uuid4
from random import random,randint
from math import floor
import hashlib
import simplejson
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

def getHttpData(url,header=headers):
    req = urllib2.Request(url,headers=header)
    try:
        response = urllib2.urlopen(req)
        httpdata = response.read()
        charset = response.headers.getparam('charset')
        if response.headers.get('Content-Encoding') == 'gzip':
            httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
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

def getContentList(id,url='----------------iqiyi--.html'):
    url = 'http://list.iqiyi.com/www/%s/%s' % (id, url)
    html = getHttpData(url)

    # 获取筛选列表
    filters = re.compile('<div class="mod_sear_list(.+?)</div>', re.DOTALL).findall(html)

    for i in filters:
        option = re.compile('<h3>(.+?)</h3>', re.DOTALL).findall(i)
        if len(option) == 0 or '频道' in option[0]: continue
        
        links = re.compile('<a href="/www/'+id+'/(.+?)</a>', re.DOTALL).findall(i)
        links = [l.replace('">','<>') for l in links]

        li = xbmcgui.ListItem('%s(选择)' % option[0][:-3])
        u = sys.argv[0]+"?mode=4&id="+urllib.quote_plus(id)+"&uri="+urllib.quote_plus(option[0][:-3]+'<||>'+'<|>'.join(links))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    # 获取页码列表
    pages = re.compile('<a data-key="up|down" class="a1"|data-search-page="item"(.+?)</a>', re.DOTALL).findall(html)
    pages = [(i.split('">')[-1],i.split('">')[0].split('/')[-1]) for i in pages if i != '']
    # for i in pages: print i

    # 获取内容列表
    content = re.compile('<ul class="site-piclist site-piclist-180236 site-piclist-auto">(.+?)</ul>', re.DOTALL).findall(html)
    # xbmc.log(str(content))
    content = re.compile('<li>(.+?)</li>', re.DOTALL).findall(content[0])
    for i in content:
        pid = re.compile('data-qidanadd-albumid="(\d+)"').search(i).group(1)
        name = re.compile('alt="(.+?)"').findall(i)[0]
        thumb = re.compile('src\s*=\s*"(.+?)"').findall(i)[0]
        uri  = re.compile('href="([^"]*)"').search(i).group(1)
        filmLength = re.compile('<span class="icon-vInfo">([^<]+)</span>').search(i).group(1).strip()
        rating = re.compile('(\d)</strong>.(\d)').search(i)
        if rating is not None: rating = rating.group().replace('</strong>','')

        cast = re.compile('<em>主演:</em>(.+?)</div>', re.DOTALL).search(i)
        cast = re.compile('<a [^>]+>([^<]*)</a>').findall(cast.group(1)) if cast else []
        cast = [i.replace('\n','').replace('\r','').strip() for i in cast]

        role = re.compile('<div class="role_info">(.+?)</div>', re.DOTALL).findall(i)
        role = re.compile('_blank">(.+?)</a>', re.DOTALL).findall(role[0])[0] if role else ''

        name += '(%s)--%s分' % (filmLength,rating) if rating is not None else '(%s)' % filmLength

        mode,isdir = ('2',True) if '更新' in filmLength or '集全' in filmLength else ('3',False)

        li = xbmcgui.ListItem(name, iconImage = '', thumbnailImage = thumb)
        u = sys.argv[0]+"?mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&thumb="+urllib.quote_plus(thumb)+"&uri="+urllib.quote_plus(uri)
        li.setInfo(type = "Video", infoLabels = {"Title":name, "Cast":cast, "Rating":rating})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, isdir)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getSeriesList(uri):
    html = getHttpData(urllib.unquote(uri))
    series = re.compile('<ul class="site-piclist(.+?)</ul>', re.DOTALL).findall(html)
    series = re.compile('<li data-albumlist-elem="playItem">(.+?)</li>', re.DOTALL).findall(series[0])

    for i in series:
        thumb = re.compile('src\s*=\s*"(.+?)"').findall(i)[0]
        number,name = re.compile('<a [^>]+>([^<]*)</a>').findall(i)

        uri  = re.compile('href="([^"]*)"').search(i).group(1)
        filmLength = re.compile('<span class="mod-listTitle_right">(\d+?):(\d+?)</span>').findall(i)
        # print filmLength,name.strip(),number.strip(),uri

        li = xbmcgui.ListItem('%s-%s %s' % (number.strip(),name.strip(),':'.join(filmLength[0])), iconImage = '', thumbnailImage = thumb)
        li.setInfo(type = "Video", infoLabels = {"Title":name})
        u = sys.argv[0] + "?mode=3&name=" + urllib.quote_plus(number.strip()+'-'+name.strip()) + "&thumb=" + urllib.quote_plus(thumb) + "&uri=" + urllib.quote_plus(uri)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def performChanges(id,uri):
    option,url = urllib.unquote(uri).split('<||>')
    dialog = xbmcgui.Dialog()

    if len(url) == 0: return

    names = [x.split('<>')[1] for x in url.split('<|>') if len(x.split('<>')) > 1]
    urls = [x.split('<>')[0] for x in url.split('<|>') if len(x.split('<>')) > 1]

    sel = dialog.select(option, names)

    if sel != -1: getContentList(id,urls[sel])

def playVideo(name,uri):
    html = getHttpData(urllib.unquote(uri))
    print(html)

    return 
    id = id.split(',')
    if len(id) == 1:
        try:
            if ("http:" in id[0]):
                link = GetHttpData(id[0])
                tvId = re.compile('data-player-tvid="(.+?)"', re.DOTALL).findall(link)[0]
                videoId = re.compile('data-player-videoid="(.+?)"', re.DOTALL).findall(link)[0]
            else:
                url = 'http://cache.video.qiyi.com/avlist/%s/' % (id[0])
                link = GetHttpData(url)
                data = link[link.find('=')+1:]
                json_response = simplejson.loads(data)
                tvId = str(json_response['data']['vlist'][0]['id'])
                videoId = json_response['data']['vlist'][0]['vid'].encode('utf-8')
        except:
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(__addonname__, '未能获取视频地址')
            return
    else:
         tvId = id[0]
         videoId = id[1]

    gen_uid = uuid4().hex
    info = getVMS(tvId, videoId, gen_uid)
    if info["code"] != "A000000":
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(__addonname__, '密钥过期，需升级插件')
        return

    vs = info["data"]["vp"]["tkl"][0]["vs"]
    #print [(x['bid'],x['scrsz']) for x in vs]
    sel = selResolution([x['bid'] for x in vs])
    if sel == -1:
        return

    video_links = vs[sel]["fs"] #now in i["flvs"] not in i["fs"]
    if not vs[sel]["fs"][0]["l"].startswith("/"):
        tmp = getVrsEncodeCode(vs[sel]["fs"][0]["l"])
        if tmp.endswith('mp4'):
             video_links = vs[sel]["flvs"]

    # New method to avoid url expired
    qyplayer.play(name, thumb, info["data"]["vp"]["du"], video_links, gen_uid)
    while qyplayer.is_active:
        xbmc.sleep(100)

    # Old method
    #urls = []
    #size = 0
    #for i in video_links:
    #    vlink = i["l"]
    #    if not vlink.startswith("/"):
    #        #vlink is encode
    #        vlink=getVrsEncodeCode(vlink)
    #    key=getDispathKey(vlink.split("/")[-1].split(".")[0])
    #    size+=i["b"]
    #    baseurl=info["data"]["vp"]["du"].split("/")
    #    baseurl.insert(-1,key)
    #    url="/".join(baseurl)+vlink+'?su='+gen_uid+'&qyid='+uuid4().hex+'&client=&z=&bt=&ct=&tn='+str(randint(10000,20000))
    #    urls.append(simplejson.loads(GetHttpData(url))["l"])

    #stackurl = 'stack://' + ' , '.join(urls)
    #listitem = xbmcgui.ListItem(name,thumbnailImage=thumb)
    #listitem.setInfo(type="Video",infoLabels={"Title":name})
    #xbmc.Player().play(stackurl, listitem)
# params = getParams()
# mode = params.get('mode')
# name = params.get('name')
# id = params.get('id')

# if mode == None: 
#     getRootList()
# elif mode == '1': 
#     if params.get('uri') is None:
#         getContentList(id)
#     else:
#         getContentList(id, params.get('uri'))
# elif mode == '2':
#     getSeriesList(params.get('uri'))
# elif mode == '3':
#     playVideo(name,id,thumb)
# elif mode == '4':
#     performChanges(id,params.get('uri'))
playVideo('第40集-周志超乔装司机','http://www.iqiyi.com/v_19rr05rei8.html')
# getContentList('1')
# getSeriesList('http://www.iqiyi.com/a_19rrj5x3zh.html#vfrm=2-4-0-1')
# getSeriesList('http://www.iqiyi.com/a_19rrh5cl15.html#vfrm=2-4-0-1')