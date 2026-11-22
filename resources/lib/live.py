# -*- coding: utf-8 -*-
import sys
import xbmcgui
import xbmcplugin
import xbmcaddon

from datetime import datetime

from resources.lib.channels import Channels 
from resources.lib.epg import epg_listitem, get_live_epg
from resources.lib.utils import get_url, get_color, get_label_color, plugin_id, get_kodi_version

def list_live(label):
    """Live TV - seznam kanálů""" 
    _handle = int(sys.argv[1]) if len(sys.argv) > 1 else -1
    addon = xbmcaddon.Addon()
    color = get_color()
    xbmcplugin.setPluginCategory(_handle, label)
    if addon.getSetting('default_tv_view') == 'false':
        xbmcplugin.setContent(_handle, 'tvshows')
    channel_numbers = addon.getSetting('channel_numbers')        
    kodi_version = get_kodi_version()

    channels_list = Channels().get_channels_list('channel_number')
    epg, epg_next = get_live_epg()
    fmt_time = lambda ts: datetime.fromtimestamp(ts).strftime('%H:%M')
    for cnt, num in enumerate(sorted(channels_list.keys()), 1):
        channel = channels_list[num]
        channel_id = channel['id']
        if channel_numbers == 'číslo kanálu':
            channel_number = f"{num}. "
        elif channel_numbers == 'pořadové číslo':
            channel_number = f"{cnt}. "
        else:
            channel_number = ""
        list_item = xbmcgui.ListItem(label=f"{channel_number}{channel['name']}")
        list_item.setProperty('IsPlayable', 'true')
        list_item.setContentLookup(False)
        icon = channel['logo']
        epgId = None
        if channel_id in epg:
            item = epg[channel_id]
            time_range = f"{fmt_time(item['start'])} - {fmt_time(item['end'])}"
            label_text = f"{item['title']} | {time_range}"
            list_item.setLabel(f"{channel_number}{channel['name']} | {get_label_color(label_text, color)}")            
            list_item = epg_listitem(list_item=list_item, epg=item, icon=icon)
            plot = item.get('description', '')
            epgId = item.get('epgId')
            if channel_id in epg_next:
                nxt = epg_next[channel_id]
                nxt_range = f"{fmt_time(nxt['start'])} - {fmt_time(nxt['end'])}"
                plot += f"\n\n[COLOR=darkgray]Následuje:\n{nxt['title']} | {nxt_range}[/COLOR]"
            if kodi_version >= 20:
                infotag = list_item.getVideoInfoTag()
                infotag.setPlot(plot)
                infotag.setTitle(item['title'])
            else:
                list_item.setInfo('video', {'plot': plot, 'title': item['title']})
            menus = [('Přehrát od začátku', f"PlayMedia(plugin://{plugin_id}?action=play_stream&channelKey={channel_id}&epgId={epgId}&fromstart=True)"),
                    ( 'Přidat nahrávku', f'RunPlugin(plugin://{plugin_id}?action=add_recording&epgId={epgId})')]
            list_item.addContextMenuItems(menus)
        else: # pokud se nepodaří načíst data ke kanálu v EPG
            list_item.setArt({'thumb': icon, 'icon': icon})
            if kodi_version >= 20:
                list_item.getVideoInfoTag().setTitle(channel['name'])
            else:
                list_item.setInfo('video', {'mediatype': 'movie', 'title': channel['name']})
        if epgId is not None:
            url = get_url(action='play_stream', channelKey=channel_id, epgId=epgId)
        else: # bez EPG se pustí živý stream kanálu
            url = get_url(action='play_stream', channelKey=channel_id)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=True)
