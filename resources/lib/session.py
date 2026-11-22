# -*- coding: utf-8 -*-
import sys
import xbmcaddon

import json
import time
import uuid

from resources.lib.api import call_api
from resources.lib.utils import Settings, display_message

class Session:
    SESSION_FILE = {'filename': 'session.txt', 'description': 'session'}
    TOKEN_VALIDITY = 60*60*24

    def __init__(self):
        self.valid_to = -1
        self.load_session()

    def pair_device(self):
        """Párování zařízení"""
        addon = xbmcaddon.Addon()
        mac_num = hex(uuid.getnode()).replace('0x', '').upper()
        mac = ':'.join(mac_num[i : i + 2] for i in range(0, 11, 2))
        data = call_api(api='create-pairing', data={'username': addon.getSetting("username"), 'password': addon.getSetting("password"), 'type': 'xbmc', 'product' : 'Kodi', 'serial' : mac})
        if 'err' in data or data.get('status', 0) != 1:
            display_message('Problém při párování')
            sys.exit()
        else:
            addon.setSetting(id='deviceid', value=str(data["deviceId"]))
            addon.setSetting(id='devicepassword', value=str(data["password"]))
            self.create_session(after_pair=True)

    def create_session(self, after_pair=False):
        """Nové přihlášení"""
        addon = xbmcaddon.Addon()
        if addon.getSetting('deviceid') and addon.getSetting('devicepassword'):
            data = call_api(api='device-login', data={'deviceId': addon.getSetting('deviceid'), 'password': addon.getSetting("devicepassword"), 'version' : '3.2.004', 'land' : 'cz', 'unit' : 'default'})
            if 'err' in data or data.get('status', 0) != 1 or not data.get('PHPSESSID'):
                display_message('Problém při přihlášení')
                sys.exit()
            else:
                self.sessionid = data['PHPSESSID']
                self.save_session()
        else:
            if after_pair:
                sys.exit()
            display_message('Nespárované zařízení. Zkouším spárovat ...', 'info')
            self.pair_device()

    def load_session(self):
        """Načte session, kontroluje integritu a expiraci"""
        settings = Settings()
        data = settings.load_json_data(file_info=self.SESSION_FILE)
        if data:
            try:
                data = json.loads(data) or {}
                sessionid = data.get('sessionid')
                valid_to = data.get('valid_to', 0)
                if sessionid and int(valid_to) > int(time.time()):
                    self.sessionid = sessionid
                    return
            except (AttributeError, TypeError, json.JSONDecodeError, ValueError):
                pass
        self.create_session()

    def save_session(self):
        """Uloží aktuální token"""
        settings = Settings()
        valid_to = int(time.time() + self.TOKEN_VALIDITY)
        data = json.dumps({'sessionid': self.sessionid, 'valid_to': valid_to})
        settings.save_json_data(file_info=self.SESSION_FILE, data=data)

    def remove_session(self):
        """Smaže session a vytvoří novou session"""
        settings = Settings()
        settings.reset_json_data(file_info=self.SESSION_FILE)
        self.create_session()
        display_message('Byla vytvořena nová session', 'info')

