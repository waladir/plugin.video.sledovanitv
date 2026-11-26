# -*- coding: utf-8 -*-
import os
import sys 
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

from urllib.parse import parse_qsl

from resources.lib.utils import get_url, check_settings
from resources.lib.live import list_live
from resources.lib.archive import list_archive, list_archive_days, list_program
from resources.lib.iptvsc import generate_playlist, generate_epg, iptv_sc_rec
from resources.lib.stream import play_stream, play_recording, play_catchup
from resources.lib.channels import Channels, manage_channels, list_channels_list_backups, list_channels_edit, edit_channel, delete_channel, change_channels_numbers
from resources.lib.channels import list_channels_groups, add_channel_group, edit_channel_group, edit_channel_group_list_channels, edit_channel_group_add_channel, edit_channel_group_add_all_channels, edit_channel_group_delete_channel, select_channel_group, delete_channel_group
from resources.lib.recordings import list_recordings, delete_recording, list_planning_recordings, list_rec_days, future_program, add_recording
from resources.lib.search import list_search, delete_search, program_search
from resources.lib.profiles import list_profiles, set_active_profile
from resources.lib.devices import list_devices, delete_device
from resources.lib.settings import list_settings
from resources.lib.session import Session

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

def main_menu():
    addon = xbmcaddon.Addon()
    icons_dir = os.path.join(addon.getAddonInfo('path'), 'resources', 'images')
    menu_items = [
        ('Živé vysílání', 'list_live', 'livetv.png'),
        ('Archiv', 'list_archive', 'archive.png'),
        ('Nahrávky', 'list_recordings', 'recordings.png'),
        ('Vyhledávání', 'list_search', 'search.png'),
    ]
    if addon.getSetting('hide_settings_menu') != 'true':
        menu_items.append(('Nastavení SledováníTV', 'list_settings', 'settings.png'))
    for label, action, icon in menu_items:
        url = get_url(action=action, label=label)
        list_item = xbmcgui.ListItem(label=label)
        icon_path = os.path.join(icons_dir, icon)
        list_item.setArt({'thumb': icon_path, 'icon': icon_path})
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    check_settings() 
    if not params:
        main_menu()
        return
    action = params.get('action')

    if action == 'list_live':
        list_live(params.get('label'))
    elif action == 'list_archive':
        list_archive(params.get('label'))
    elif action == 'list_archive_days':
        list_archive_days(params.get('id'), params.get('label'))
    elif action == 'list_program':
        list_program(params.get('id'), params.get('day_min'), params.get('label'))
    elif action == 'future_program':
        future_program(params.get('id'), params.get('day'), params.get('label'))

    elif action == 'list_recordings':
        list_recordings(params.get('label'))
    elif action == 'list_planning_recordings':
        list_planning_recordings(params.get('label'))
    elif action == 'delete_recording':
        delete_recording(params.get('recordId'))
    elif action == 'add_recording':
        add_recording(params.get('epgId'))
    elif action == 'list_rec_days':
        list_rec_days(params.get('id'), params.get('label'))

    elif action == 'list_search':
        list_search(params.get('label'))
    elif action == 'program_search':
        program_search(params.get('query'), params.get('label'))
    elif action == 'delete_search':
        delete_search(params.get('query'))

    elif action == 'play_stream':
        play_stream(params.get('channelKey'), params.get('epgId'), 'fromstart' in params)
    elif action == 'play_recording':
        play_recording(params.get('recordId'))


    elif action == 'list_profiles':
        list_profiles(params.get('label'))                      
    elif action == 'set_active_profile':
        set_active_profile(params.get('id'))     

    elif action == 'list_devices':
        list_devices(params.get('label'))                      
    elif action == 'delete_device':
        delete_device(params.get('deviceId'))                             

    elif action == 'manage_channels':
        manage_channels(params.get('label'))
    elif action == 'reset_channels_list':
        Channels().reset_channels()   
    elif action == 'restore_channels':
        Channels().restore_channels(params.get('backup'))        
    elif action == 'list_channels_list_backups':
        list_channels_list_backups(params.get('label'))
    elif action == 'list_channels_edit':
        list_channels_edit(params.get('label'))
    elif action == 'edit_channel':
        edit_channel(params.get('id'))
    elif action == 'delete_channel':
        delete_channel(params.get('id'))
    elif action == 'change_channels_numbers':
        change_channels_numbers(params.get('from_number'), params.get('direction'))
    elif action == 'list_channels_groups':
        list_channels_groups(params.get('label'))
    elif action == 'add_channel_group':
        add_channel_group()
    elif action == 'edit_channel_group':
        edit_channel_group(params.get('group'), params.get('label'))
    elif action == 'delete_channel_group':
        delete_channel_group(params.get('group'))
    elif action == 'select_channel_group':
        select_channel_group(params.get('group'))
    elif action == 'edit_channel_group_list_channels':
        edit_channel_group_list_channels(params.get('group'), params.get('label'))
    elif action == 'edit_channel_group_add_channel':
        edit_channel_group_add_channel(params.get('group'), params.get('channel'))
    elif action == 'edit_channel_group_add_all_channels':
        edit_channel_group_add_all_channels(params.get('group'))
    elif action == 'edit_channel_group_delete_channel':
        edit_channel_group_delete_channel(params.get('group'), params.get('channel'))

    elif action == 'generate_playlist':
        generate_playlist(params.get('output_file'))
        if 'output_file' in params:
            xbmcplugin.addDirectoryItem(_handle, '1', xbmcgui.ListItem())
            xbmcplugin.endOfDirectory(_handle, succeeded=True)
    elif action == 'generate_epg':
        if 'output_file' in params:
            generate_epg(params.get('output_file'), False)
            xbmcplugin.addDirectoryItem(_handle, '1', xbmcgui.ListItem())
            xbmcplugin.endOfDirectory(_handle, succeeded=True)
        else:
            generate_epg(show_progress=True)

    elif action == 'iptsc_play_stream':
        if 'catchup_start_ts' in params and 'catchup_end_ts' in params:
            play_catchup(id=params.get('id'), start_ts=params.get('catchup_start_ts'), end_ts=params.get('catchup_end_ts'))
        else:
            play_stream(channelKey=params.get('id'), epgId=None, fromstart='fromstart' in params)
    elif action == 'iptv_sc_rec':
        iptv_sc_rec(params.get('channel'), params.get('startdatetime'))

    elif action == 'list_settings':
        list_settings(params.get('label'))
    elif action == 'addon_settings':
        xbmcaddon.Addon().openSettings()
    elif action == 'reset_session':
        Session().remove_session()
    elif action == 'pair_device':
        Session().pair_device()

    else:
        xbmc.log(f"SledováníTV: Neznámá akce {action}")

if __name__ == '__main__':
    router(sys.argv[2][1:])
