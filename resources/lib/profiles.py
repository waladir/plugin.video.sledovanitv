# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcgui
import xbmcplugin

from resources.lib.api import call_api
from resources.lib.utils import get_url, display_message
from resources.lib.session import Session

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

def list_profiles(label):
    """Vypíše seznam profilů se zvýrazněným aktivním profilem"""  
    xbmcplugin.setPluginCategory(_handle, label)
    data = call_api(api = 'get-user-profile', data = {'PHPSESSID': Session().sessionid})
    active_profile_id = data.get('info', {}).get('id')
    for profile in get_profiles():
        name = f"[B]{profile['name']}[/B]" if profile.get('id') == active_profile_id else profile['name']
        list_item = xbmcgui.ListItem(label=name)
        url = get_url(action='set_active_profile', id=profile['id'])
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    xbmcplugin.endOfDirectory(_handle)

def set_active_profile(profile_id):
    """Nastavení profilu jako aktivního"""  
    data = call_api(api = 'switch-profile', data = {'profile': profile_id, 'PHPSESSID': Session().sessionid})
    if 'err' in data or data.get('status', 0) != 1:
        display_message('Problém při nastavení aktivního profilu')
    xbmc.executebuiltin('Container.Refresh')

def get_profiles():
    """Načtení profilů"""  
    profiles = []
    data = call_api(api = 'user-profiles', data = {'PHPSESSID': Session().sessionid})
    if 'err' in data or data.get('status', 0) != 1 or not data.get('profiles'):
        display_message('Problém při načtení profilů')
    else:
        for profile in data.get('profiles', {}):
            profiles.append({'id': profile.get('id'), 'name': profile.get('name')})
    return profiles
