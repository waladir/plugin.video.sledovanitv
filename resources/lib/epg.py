# -*- coding: utf-8 -*-
import time

from resources.lib.session import Session
from resources.lib.api import call_api
from resources.lib.utils import get_kodi_version, display_message

kodi_version = get_kodi_version()

def get_live_epg():
    """Z EPG dat vrací aktualní a následující pořad pro všechny kanály"""
    ts = int(time.time())    
    epg_now, epg_next = {}, {}
    data = call_api(api = 'epg', data = {'detail': 'description,score,poster,backdrop,genres,rating', 'backdropSize' : '1280', 'posterSize' : '234', 'PHPSESSID' : Session().sessionid })    
    if 'err' in data or data.get('status', 0) != 1:
        display_message('Problém při stažení EPG')
        return {}, {}
    for channel_id, items in data.get('channels', {}).items():
        for item in items:
            epgId = item['eventId']
            start = int(time.mktime(time.strptime(item['startTime'], '%Y-%m-%d %H:%M')))
            end = int(time.mktime(time.strptime(item['endTime'], '%Y-%m-%d %H:%M')))
            duration = int(item.get('duration') or 0)
            title = item.get('title', '')
            description = item.get('description') or ''
            year = str(item.get('year', ''))
            poster = item.get('poster') or ''
            backdrop = item.get('backdrop') or ''
            event = {'epgId': epgId, 'start': start, 'end': end, 'duration': duration, 'title': title, 'description': description, 'year': year, 'poster': poster, 'backdrop': backdrop }
            if start <= ts < end:
                epg_now[channel_id] = event
            elif start >= ts and channel_id not in epg_next:
                epg_next[channel_id] = event
    return epg_now, epg_next

def get_epg_date(channelKey, date, duration = 1440):
    epg = {}
    session = Session()
    params = {'time': date, 'duration' : str(duration), 'detail' : 'description,poster,backdrop', 'backdropSize' : '1280', 'posterSize' : '234', 'PHPSESSID' : session.sessionid}    
    if channelKey is not None:
        params['channels'] = channelKey
    data = call_api(api = 'epg', data = params)
    if 'err' in data or data.get('status', 0) != 1:
        display_message('Problém při stažení EPG')
        return {}
    else:
        for channel, items in data.get('channels', {}).items():
            if channelKey is None or channelKey == channel:
                for item in items:
                    epgId = item['eventId']
                    start = int(time.mktime(time.strptime(item['startTime'], '%Y-%m-%d %H:%M')))
                    end = int(time.mktime(time.strptime(item['endTime'], '%Y-%m-%d %H:%M')))
                    duration = int(item.get('duration') or 0)
                    title = item.get('title', '')
                    description = item.get('description') or ''
                    year = str(item.get('year', ''))
                    poster = item.get('poster') or ''
                    backdrop = item.get('backdrop') or ''
                    if channelKey is None:
                        key = channel + ';' + str(start)
                    else:
                        key = start
                    epg.update({ key : { 'epgId' : epgId, 'start' : start, 'end' : end, 'duration' : duration, 'title' : title, 'description' : description, 'year' : year, 'poster' : poster, 'backdrop' : backdrop }})
    return epg    

def epg_listitem(list_item, epg, icon):
    """Vyplní metadata"""
    if kodi_version >= 20:
        infotag = list_item.getVideoInfoTag()
        infotag.setMediaType('movie')
        infotag.setTitle(epg['title'])
    else:
        list_item.setInfo('video', {'mediatype' : 'movie'})
        list_item.setInfo('video', {'title': epg['title']})
    if epg.get('backdrop'):
        list_item.setArt({'poster': epg['backdrop'],'thumb': epg.get('poster', ''), 'icon': epg.get('poster', '')})
    else:
        list_item.setArt({'thumb': icon, 'icon': icon})
    if epg.get('poster') =='https://sledovanitv.cz/img/posters/general.jpg':
        list_item.setArt({'thumb': icon, 'icon': icon})          
    if epg.get('description'):
        if kodi_version >= 20:
            infotag.setPlot(epg['description'])
        else:
            list_item.setInfo('video', {'plot': epg['description']})
    if epg.get('year') and str(epg['year']).isdigit():
        if kodi_version >= 20:
            infotag.setYear(int(epg['year']))
        else:
            list_item.setInfo('video', {'year': int(epg['year'])})
    return list_item
