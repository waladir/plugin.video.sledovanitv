# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcgui
import xbmcplugin

from resources.lib.api import call_api
from resources.lib.utils import get_url, display_message, display_dialog_yn
from resources.lib.session import Session
import json

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

def list_devices(label):
    """Vypíše seznam zařízení"""  
    xbmcplugin.setPluginCategory(_handle, label)
    data = call_api(api = 'get-devices', data = {'PHPSESSID': Session().sessionid})
    if 'err' in data or data.get('status', 0) != 1:
        display_message('Problém při načtení zařízení')
        return
    for device in get_devices():
        name = f"[B]{device['title']} [{device['deviceId']}][/B]" if device.get('self') == True else f"{device['title']} [{device['deviceId']}]"
        list_item = xbmcgui.ListItem(label=name)
        url = get_url(action='delete_device', deviceId=device['deviceId'])
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    xbmcplugin.endOfDirectory(_handle)

def delete_device(deviceId):
    """Smazání zařízení""" 
    devices = get_devices()
    if not devices:
        return
    for device in devices:
        if str(device.get('deviceId')) == deviceId:
            if device.get('self') == True:
                display_message('Snažíte se odstranit toto zařízení. Nejprve udělejte nové párovaní.')
                return
            if display_dialog_yn('Smazání zařízení', 'Opravdu chcete zařízení ' + f"{device['title']} [{device['deviceId']}]" + ' smazat?') == True:
                data = call_api(api = 'remove-device', data = {'deviceId': deviceId, 'PHPSESSID': Session().sessionid})
                if 'err' in data or data.get('status', 0) != 1:
                    display_message('Problém při mazání zařízení')
                xbmc.executebuiltin('Container.Refresh')
            return
    display_message('Zařízení nebylo nalezeno')
       
def get_devices():
    data = call_api(api = 'get-devices', data = {'PHPSESSID': Session().sessionid})
    if 'err' in data or data.get('status', 0) != 1:
        display_message('Problém při načtení zařízení')
    devices = data.get('devices', [])
    return devices
