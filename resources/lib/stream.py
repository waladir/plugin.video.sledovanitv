# -*- coding: utf-8 -*-
import sys
import xbmcgui
import xbmcplugin

from datetime import datetime
import time

from resources.lib.session import Session
from resources.lib.api import call_api
from resources.lib.epg import get_epg_date, kodi_version
from resources.lib.utils import display_message, stream_caps

def play_stream(channelKey, epgId, fromstart=False):
    """Ošetřuje spuštění streamu"""
    if epgId is None:
        list_item = xbmcgui.ListItem(path='http://sledovanitv.cz/vlc/api-channel/' + channelKey + ".m3u8?quality=40&capabilities=h265,adaptive&PHPSESSID=" + Session().sessionid)
    else:
        data = call_api(api='event-timeshift', data={'format': 'm3u8', 'quality': '40', 'capabilities': stream_caps, 'eventId': epgId, 'PHPSESSID': Session().sessionid})
        if 'err' in data or data.get('status', 0) != 1:
            display_message('Problém při přehrání')
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem())
            return
        list_item = xbmcgui.ListItem(path=data['url'])
    prop = list_item.setProperty
    prop('inputstream', 'inputstream.adaptive')
    if kodi_version < 21: # od Kodi 21 deprecated, typ manifestu se detekuje automaticky
        prop('inputstream.adaptive.manifest_type', 'hls')
    if fromstart:
        prop('inputstream.adaptive.play_timeshift_buffer', 'true')
    list_item.setMimeType('application/vnd.apple.mpegurl')
    list_item.setContentLookup(False)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, list_item)

def play_recording(recordId):
    """Ošetřuje spuštění nahrávky"""
    data = call_api(api='record-timeshift', data={'format': 'm3u8', 'quality': '40', 'capabilities': stream_caps, 'recordId': recordId, 'PHPSESSID': Session().sessionid})
    if 'err' in data or data.get('status', 0) != 1:
        display_message('Problém při přehrání')
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem())
        return
    list_item = xbmcgui.ListItem(path=data['url'])
    prop = list_item.setProperty
    prop('inputstream', 'inputstream.adaptive')
    if kodi_version < 21: # od Kodi 21 deprecated, typ manifestu se detekuje automaticky
        prop('inputstream.adaptive.manifest_type', 'hls')
    list_item.setMimeType('application/vnd.apple.mpegurl')
    list_item.setContentLookup(False)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, list_item)

def play_catchup(id, start_ts, end_ts):
    """Ošetřuje spuštění catchupu"""
    start_ts, end_ts = int(start_ts), int(end_ts)
    den = datetime.fromtimestamp(start_ts).strftime('%Y-%m-%d')
    epg = get_epg_date(channelKey=id, date=den)
    item = epg.get(start_ts)
    if item: # pokud se najde pořad v EPG, pustí se catchup, jinak jako fallback živé vysílání
        if item['end'] > (time.time() - 10):
            play_stream(channelKey=id, epgId=item['epgId'], fromstart=True)
        else:
            play_stream(channelKey=id, epgId=item['epgId'])
    else:
        play_stream(channelKey=id, epgId=None)

