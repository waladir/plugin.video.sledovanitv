# -*- coding: utf-8 -*-
import xbmcaddon

from urllib.request import urlopen, Request
from urllib.parse import quote, urlencode
import json
import re

from resources.lib.utils import log_message

HEADERS = {'User-Agent': 'Dalvik/2.1.0', 'Content-Type': 'application/json'}
API_URL = 'https://sledovanitv.cz/api/'

def call_api(api, data):
    """Volání API"""
    if api.startswith('https'):
        url = api
    else:
        url = API_URL + api
    addon = xbmcaddon.Addon()
    if data:
        url = url + '?' + urlencode(data, quote_via=quote)
    request = Request(url = url , data = None, headers = HEADERS)
    if addon.getSetting('log_request') == 'true':
        log_message(re.sub(r'((?:PHPSESSID|password)=)[^&]+', r'\1*****', url))
    try:
        html = urlopen(request, timeout=30).read()
        if addon.getSetting('log_response') == 'true':
            if len(html) > 5000 and addon.getSetting('skip_long') == 'true':
                log_message(f"Odpověď obržena ({len(html)})")
            else:
                log_message(re.sub(r'("PHPSESSID"\s*:\s*")[^"]+', r'\1*****', str(html)))
        if html:
            data = json.loads(html)
            return data
        else:
            return {}
    except Exception as error:
        log_message(f"Chyba při volání API: {error}")
        return {'err': str(error) }
