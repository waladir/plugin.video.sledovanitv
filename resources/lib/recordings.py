# -*- coding: utf-8 -*-
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

from datetime import date, datetime, timedelta
import time

from resources.lib.session import Session
from resources.lib.channels import Channels
from resources.lib.epg import epg_listitem, get_epg_date
from resources.lib.api import call_api
from resources.lib.utils import get_url, plugin_id, day_translation, day_translation_short, display_message

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

def list_recordings(label):
    """Menu s nahrávkami"""
    xbmcplugin.setPluginCategory(_handle, label)
    channels_list = Channels().get_channels_list()
    now_ts = int(datetime.now().timestamp())
    list_item = xbmcgui.ListItem(label='Plánování nahrávek')
    url = get_url(action='list_planning_recordings', label = label + ' / ' + 'Plánování')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    data = call_api(api='get-pvr2', data={'detail': 'description,poster,backdrop', 'backdropSize': '1280', 'posterSize': '234', 'PHPSESSID': Session().sessionid})
    if 'err' in data or data.get('status', 0) != 1:
        display_message('Problém při načtení nahrávek')
        xbmcplugin.endOfDirectory(_handle)
        return
    records = [] # (start, nahrávka) - nahrávky i jednotlivé díly seriálů
    for item in data.get('items', []):
        if item.get('recordId') is None:
            series_data = call_api(api='mdb-title', data={'titleId': str(item['seriesId']), 'channel': item['channel'], 'detail': 'description,score,poster,backdrop,genres,mdbIdTitle,rating', 'backdropSize': '1280', 'posterSize': '234', 'PHPSESSID': Session().sessionid})
            if 'err' in series_data or 'series' not in series_data:
                continue
            series_item = series_data['series']
            for episode_item in series_data.get('episodes', {}):
                if episode_item.get('recordId') is not None:
                    episode_item['title'] = series_item['title']
                    episode_item['channel'] = series_item['channel']
                    if len(episode_item.get('poster', '')) == 0:
                        episode_item['poster'] = series_item['poster']
                    if len(episode_item.get('backdrop', '')) == 0:
                        episode_item['backdrop'] = series_item['backdrop']
                    if len(episode_item.get('description', '')) == 0:
                        episode_item['description'] = series_item.get('description')
                    start = int(time.mktime(time.strptime(episode_item['startTime'], '%Y-%m-%d %H:%M:%S')))
                    records.append((start, episode_item))
        else:
            start = int(time.mktime(time.strptime(item['startTime'], '%Y-%m-%d %H:%M')))
            records.append((start, item))
    for start, item in records:
        dt_start = datetime.fromtimestamp(start)
        item_label = (f"{item['title']} | {channels_list.get(item['channel'], {}).get('name', item['channel'])} | {day_translation_short[dt_start.strftime('%w')]} {dt_start.strftime('%d.%m. %H:%M')}")
        if start > now_ts:
            item_label = f"[COLOR gray]{item_label}[/COLOR]"
        list_item = xbmcgui.ListItem(label=item_label)
        list_item = epg_listitem(list_item=list_item, epg=item, icon=None)
        if start > now_ts:
            action = 'play_future'
            list_item.setProperty('IsPlayable', 'false')
        else:
            action = 'play_recording'
            list_item.setProperty('IsPlayable', 'true')
        list_item.setContentLookup(False)
        url = get_url(action=action, recordId = item['recordId'])
        list_item.addContextMenuItems([('Smazat nahrávku', f"RunPlugin(plugin://{plugin_id}?action=delete_recording&recordId={item['recordId']})")])
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    xbmcplugin.endOfDirectory(_handle)

def list_planning_recordings(label):
    """Seznam kanálů"""    
    addon = xbmcaddon.Addon()
    xbmcplugin.setPluginCategory(_handle, label)
    channels_list = Channels().get_channels_list('channel_number')
    channel_numbers = addon.getSetting('channel_numbers')
    cnt = 0
    for number in sorted(channels_list.keys()):  
        channel = channels_list[number]
        if not channel.get('liveOnly', False):
            cnt += 1
            if channel_numbers == 'číslo kanálu':
                channel_number = f"{number}. "
            elif channel_numbers == 'pořadové číslo':
                channel_number = f"{cnt}. "
            else:
                channel_number = ""
            list_item = xbmcgui.ListItem(label=f"{channel_number}{channel['name']}")
            list_item.setArt({'thumb': channel['logo'], 'icon': channel['logo']})
            url = get_url(action='list_rec_days', id=channel['id'], label=f"{label} / {channel['name']}")
            xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle)

def list_rec_days(id, label):
    """Výběr dne"""      
    xbmcplugin.setPluginCategory(_handle, label)
    today = date.today()
    labels = ['Dnes', 'Zítra']
    for i in range(8):
        day = today + timedelta(days=i)
        w_day = day.strftime('%w')
        if i < 2:
            den_label, den = labels[i], labels[i]
        else:
            den_label = f"{day_translation_short[w_day]} {day.strftime('%d.%m.')}"
            den = f"{day_translation[w_day]} {day.strftime('%d.%m.%Y')}"
        list_item = xbmcgui.ListItem(label=den)
        url = get_url(action='future_program', id=id, day=i, label=f"{label} / {den_label}")
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle)

def future_program(id, day, label):
    """Program s nastavením nahrávek"""
    addon = xbmcaddon.Addon(); day = int(day)
    icons_dir = os.path.join(addon.getAddonInfo('path'), 'resources', 'images')
    label = label.replace('Nahrávky / Plánování /', '')
    xbmcplugin.setPluginCategory(_handle, label); xbmcplugin.setContent(_handle, 'episodes')
    den = (date.today() + timedelta(days=day)).strftime('%Y-%m-%d')
    epg = get_epg_date(channelKey = id, date = den)
    base_label = label.rsplit(' / ', 1)[0]
    if day > 0:
        dt = date.today() + timedelta(days=day - 1)
        d_lbl = f"{day_translation_short[dt.strftime('%w')]} {dt.strftime('%d.%m.')}"
        list_item = xbmcgui.ListItem(label='Předchozí den')
        list_item.setArt({'thumb': os.path.join(icons_dir, 'previous_arrow.png'), 'icon': os.path.join(icons_dir, 'previous_arrow.png')})
        xbmcplugin.addDirectoryItem(_handle, get_url(action='future_program', id=id, day=day-1, label=f"{base_label} / {d_lbl}"), list_item, True)
    for key in sorted(epg.keys()):
        item = epg[key]
        dt_start = datetime.fromtimestamp(item['start'])
        dt_end = datetime.fromtimestamp(item['end'])
        if (dt_start.strftime('%Y-%m-%d') == den or dt_end.strftime('%Y-%m-%d') == den):
            item_label = (f"{day_translation_short[dt_start.strftime('%w')]} {dt_start.strftime('%d.%m. %H:%M')} - {dt_end.strftime('%H:%M')} | {item['title']}")
            list_item = xbmcgui.ListItem(label=item_label)
            list_item = epg_listitem(list_item=list_item, epg=item, icon=None)
            list_item.setProperty('IsPlayable', 'false')
            list_item.addContextMenuItems([('Přidat nahrávku', f"RunPlugin(plugin://{plugin_id}?action=add_recording&epgId={item['epgId']})")])
            xbmcplugin.addDirectoryItem(_handle, get_url(action='add_recording', epgId=item['epgId']), list_item, False)
    if day < 7:
        dt = date.today() + timedelta(days=day + 1)
        d_lbl = f"{day_translation_short[dt.strftime('%w')]} {dt.strftime('%d.%m.')}"
        list_item = xbmcgui.ListItem(label='Následující den')
        list_item.setArt({'thumb': os.path.join(icons_dir, 'next_arrow.png'), 'icon': os.path.join(icons_dir, 'next_arrow.png')})
        xbmcplugin.addDirectoryItem(_handle, get_url(action='future_program', id=id, day=day+1, label=f"{base_label} / {d_lbl}"), list_item, True)
    xbmcplugin.endOfDirectory(_handle, updateListing=True)

def add_recording(id):
    """Přidání nahrávky"""
    data = call_api(api='record-event', data={'eventId': id,'PHPSESSID': Session().sessionid})
    if 'err' in data or data.get('status', 0) != 1:
        display_message('Chyba při přidání nahrávky')
    else:
        display_message('Nahrávka přidána', 'info')
    xbmc.executebuiltin('Container.Refresh')
    
def delete_recording(id):
    """Odstranění nahrávky"""
    data = call_api(api='delete-record', data={'recordId': id,'PHPSESSID': Session().sessionid})
    if 'err' in data or data.get('status', 0) != 1:
        display_message('Chyba při smazání nahrávky')
    xbmc.executebuiltin('Container.Refresh')
