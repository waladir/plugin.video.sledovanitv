# -*- coding: utf-8 -*-
import sys
import os
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
try:
    from xbmcvfs import translatePath
except ImportError:
    from xbmc import translatePath
    
from urllib.parse import quote  
from datetime import datetime
import time

from resources.lib.api import call_api
from resources.lib.session import Session
from resources.lib.channels import Channels
from resources.lib.epg import epg_listitem
from resources.lib.utils import get_url, plugin_id, display_message, day_translation_short

_handle = int(sys.argv[1])

def list_search(label):
    """Vypíše menu pro vyhledávání včetně historie"""
    xbmcplugin.setPluginCategory(_handle, label)
    list_item = xbmcgui.ListItem(label='Nové hledání')
    url = get_url(action='program_search', query='-----', label=f"{label} / Nové hledání")
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    for item in load_search_history():
        list_item = xbmcgui.ListItem(label=item)
        url = get_url(action='program_search', query=item, label=f"{label} / {item}")
        list_item.addContextMenuItems([('Smazat', f"RunPlugin(plugin://{plugin_id}?action=delete_search&query={quote(item)})")])
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def program_search(query, label):
    """Samotné vyhledávání"""
    xbmcplugin.setPluginCategory(_handle, label)
    xbmcplugin.setContent(_handle, 'movies')
    if query == '-----':
        kb = xbmc.Keyboard('', 'Hledat')
        kb.doModal()
        if not kb.isConfirmed() or not kb.getText():
            if kb.isConfirmed(): 
                display_message('Je potřeba zadat vyhledávaný řetězec')
            xbmcplugin.endOfDirectory(_handle, succeeded=False)
            return
        query = kb.getText()
        save_search_history(query)

    data = call_api(api='epg-search', data={ 'query': query, 'detail': 'description,poster,backdrop', 'backdropSize': '1280', 'posterSize': '234', 'PHPSESSID': Session().sessionid})
    if 'err' in data or data.get('status', 0) != 1:
        display_message('Problém při vyhledávání')
        xbmcplugin.endOfDirectory(_handle, succeeded=False)
        return
    if 'events' in data and len(data['events']) > 0:
        channels = Channels()
        channels_list = channels.get_channels_list()
        for event in data['events']:
            startts = int(time.mktime(time.strptime(event['startTime'], '%Y-%m-%d %H:%M')))
            start = datetime.fromtimestamp(startts)
            endts = int(time.mktime(time.strptime(event['endTime'], '%Y-%m-%d %H:%M'))) 
            end = datetime.fromtimestamp(endts)
            epgId = event['eventId']
            if event['channel'] in channels_list and endts < time.time():
                list_item = xbmcgui.ListItem(label = event['title'] + ' (' + channels_list[event['channel']]['name'] + ' | ' + day_translation_short[start.strftime('%w')] + ' ' + start.strftime('%d.%m %H:%M') + ' - ' + end.strftime('%H:%M') + ')')
                list_item.setInfo('video', {'mediatype':'movie', 'title': event['title'] + ' (' + channels_list[event['channel']]['name']}) 
                list_item = epg_listitem(list_item, event, channels_list[event['channel']]['logo'])
                list_item.setProperty('IsPlayable', 'true')
                list_item.setContentLookup(False)          
                url = get_url(action='play_stream', channelKey = event['channel'], epgId = epgId)
                xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
        xbmcplugin.endOfDirectory(_handle)
    else:
        display_message('Nic nenalezeno', 'info')
        xbmcplugin.endOfDirectory(_handle, succeeded=False)

def load_search_history():
    """Načtení historie"""
    filename = _get_history_file()
    if not os.path.exists(filename): return []
    history = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            history = [line.strip() for line in f if line.strip()]
    except Exception: # osetreni spatneho enkodovani
        try:
            with open(filename, 'r') as f:
                history = [line.strip() for line in f if line.strip()]
            with open(filename, 'w', encoding='utf-8') as f:
                for item in history: f.write(f"{item}\n")
        except Exception: history = []
    return history    

def save_search_history(query):
    """Uloření historie"""
    history = load_search_history()
    if query in history: history.remove(query)
    history.insert(0, query)
    max_h = int(xbmcaddon.Addon().getSetting('search_history') or 10)
    with open(_get_history_file(), 'w', encoding='utf-8') as f:
        for item in history[:max_h]: f.write(f"{item}\n")

def delete_search(query):
    """Odstranění stringu z historie"""
    history = [item for item in load_search_history() if item != query]
    with open(_get_history_file(), 'w', encoding='utf-8') as f:
        for item in history: f.write(f"{item}\n")
    xbmc.executebuiltin('Container.Refresh')

def _get_history_file():
    """Vrací jméno souboru s historií vyhledávání"""
    addon = xbmcaddon.Addon()
    path = translatePath(addon.getAddonInfo('profile'))
    if not os.path.exists(path): os.makedirs(path)
    return os.path.join(path, 'search_history.txt')
