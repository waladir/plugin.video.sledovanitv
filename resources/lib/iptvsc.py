# -*- coding: utf-8 -*-
import os

import xbmcgui
import xbmcaddon
import xbmcvfs

from datetime import datetime, timezone, timedelta
import time

from resources.lib.channels import Channels
from resources.lib.utils import plugin_id, replace_by_html_entity, display_message, log_message
from resources.lib.epg import get_epg_date
from resources.lib.recordings import add_recording

def save_file_test():
    """Otestuje uložení souboru do output_dir"""
    addon = xbmcaddon.Addon()
    output_dir = addon.getSetting('output_dir')
    if not output_dir:
        return 0
    test_file = os.path.join(output_dir, 'test.fil')
    try:
        file = xbmcvfs.File(test_file, 'w')
        try:
            file.write('test') # xbmcvfs v K19+ bere string přímo
        finally:
            file.close()
        file = xbmcvfs.File(test_file, 'r')
        try:
            content = file.read()
            success = (content == 'test')
        finally:
            file.close()
        xbmcvfs.delete(test_file)
        return 1 if success else 0
    except Exception:
        if xbmcvfs.exists(test_file):
            xbmcvfs.delete(test_file)
        return 0

def generate_playlist(output_file=''):
    """Generování playlistu"""
    addon = xbmcaddon.Addon()
    output_dir = addon.getSetting('output_dir')
    if not output_dir:
        display_message('Nastav adresář pro playlist a EPG!')
        return
    if save_file_test() == 0:
        display_message('Chyba při uložení playlistu (test zápisu selhal)')
        return
    if not output_file:
        ext = 'm3u' if addon.getSetting('playlist_filename') == 'playlist.m3u' else 'txt'
        output_file = os.path.join(output_dir, f'playlist.{ext}')
    channels = Channels()
    channels_list = channels.get_channels_list('channel_number')
    catchup_mode = addon.getSetting('catchup_mode')
    playlist_lines = ['#EXTM3U']
    for number in sorted(channels_list.keys()):
        ch = channels_list[number]
        name = ch['name']
        logo = ch.get('logo') or ''
        ch_id = ch['id']
        catchup_str = ""
        if not ch.get('liveOnly'):
            if catchup_mode == 'default':
                catchup_str = (f'catchup="default" catchup-days="7" '
                               f'catchup-source="plugin://{plugin_id}/?action=iptsc_play_stream&id={ch_id}'
                               '&catchup_start_ts={utc}&catchup_end_ts={utcend}" ')
            else:
                catchup_str = 'catchup="append" catchup-days="7" catchup-source="&catchup_start_ts={utc}&catchup_end_ts={utcend}" '
        playlist_lines.append(f'#EXTINF:-1 {catchup_str}tvg-chno="{number}" tvg-id="{name}" tvh-epg="0" tvg-logo="{logo}",{name}')
        if not ch.get('liveOnly'):
            playlist_lines.append('#KODIPROP:inputstream=inputstream.ffmpegdirect')
            playlist_lines.append('#KODIPROP:inputstream.ffmpegdirect.stream_mode=timeshift')
            playlist_lines.append('#KODIPROP:inputstream.ffmpegdirect.is_realtime_stream=true')
        
        playlist_lines.append('#KODIPROP:mimetype=video/mp2t')
        playlist_lines.append(f'plugin://{plugin_id}/?action=iptsc_play_stream&id={ch_id}')
    try:
        f = xbmcvfs.File(output_file, 'w')
        content = '\n'.join(playlist_lines) + '\n'
        success = f.write(content)
        f.close()
        if success:
            display_message('Playlist byl uložený', 'info')
        else:
            raise IOError("Zápis do souboru selhal")
    except Exception:
        display_message('Chyba při uložení playlistu')

def generate_epg(output_file='', show_progress=True):
    """Generování EPG"""
    addon = xbmcaddon.Addon()
    channels = Channels()
    channels_list = channels.get_channels_list('channel_number')
    channels_list_by_id = channels.get_channels_list('id')
    if not channels_list:
        display_message('Nevrácena žádná data!')
        return
    if save_file_test() == 0:
        display_message('Chyba při uložení EPG (test zápisu selhal)')
        return
    if not output_file:
        output_dir = addon.getSetting('output_dir')
        output_file = os.path.join(output_dir, 'sledovanitv_epg.xml')
    dialog = None
    f = None
    def safe_write(handle, text):
        try:
            handle.write(text.encode('utf-8'))
        except (TypeError, AttributeError):
            handle.write(text)
    try:
        f = xbmcvfs.File(output_file, 'w')
        safe_write(f, '<?xml version="1.0" encoding="UTF-8"?>\n')
        safe_write(f, '<tv generator-info-name="EPG grabber">\n')
        for number in sorted(channels_list.keys()):
            ch = channels_list[number]
            name = replace_by_html_entity(ch['name'])
            logo = replace_by_html_entity(ch.get('logo') or '')
            safe_write(f, f'  <channel id="{name}">\n')
            safe_write(f, f'    <display-name lang="cs">{name}</display-name>\n')
            safe_write(f, f'    <icon src="{logo}" />\n')
            safe_write(f, f'  </channel>\n')
        now = datetime.now()
        today_start_dt = datetime(now.year, now.month, now.day)
        epg_from = int(addon.getSetting('epg_from') or 1)
        epg_to = int(addon.getSetting('epg_to') or 7)
        days_range = range(-epg_from, epg_to)
        total_days = len(days_range)
        if show_progress:
            dialog = xbmcgui.DialogProgressBG()
            dialog.create('Stahování EPG dat', 'Probíhá generování XML...')
        formatted_tz = "+0000"
        written = set() # (kanál, start) - pořady přes půlnoc vrací API v obou dnech
        for idx, day_offset in enumerate(days_range):
            current_day_dt = today_start_dt + timedelta(days=day_offset)
            date_str = current_day_dt.strftime('%d.%m.%Y')
            if show_progress and dialog:
                percent = int((idx / max(1, total_days)) * 100)
                dialog.update(percent, message=f"Zpracovávám den: {date_str}")
            epg_data = get_epg_date(channelKey=None, date=current_day_dt.strftime('%Y-%m-%d'))
            buffer = []
            for item_key in epg_data:
                item = epg_data[item_key]
                channelKey = item_key.split(';')[0]
                channel = channels_list_by_id.get(channelKey)
                if channel and (channelKey, item['start']) not in written:
                    written.add((channelKey, item['start']))
                    ch_name = replace_by_html_entity(channel['name'])
                    start = datetime.fromtimestamp(item['start'], timezone.utc).strftime('%Y%m%d%H%M%S')
                    stop = datetime.fromtimestamp(item['end'], timezone.utc).strftime('%Y%m%d%H%M%S')
                    title = replace_by_html_entity(item['title'])
                    desc = replace_by_html_entity(item.get('description', ''))
                    icon = replace_by_html_entity(item.get('poster') or '')
                    buffer.append(f'  <programme start="{start} {formatted_tz}" stop="{stop} {formatted_tz}" channel="{ch_name}">\n')
                    buffer.append(f'    <title lang="cs">{title}</title>\n')
                    if desc:
                        buffer.append(f'    <desc lang="cs">{desc}</desc>\n')
                    if icon:
                        buffer.append(f'    <icon src="{icon}"/>\n')
                    buffer.append('  </programme>\n')
                    if len(buffer) > 250:
                        safe_write(f, "".join(buffer))
                        buffer = []
            if buffer:
                safe_write(f, "".join(buffer))
        safe_write(f, '</tv>\n')
        f.close()
        if show_progress:
            dialog.close()
            display_message('EPG bylo uložené', 'info')
        elif addon.getSetting('epg_info') == 'true':
            display_message('EPG bylo uložené', 'info')
    except Exception as e:
        log_message(f"Chyba při generování EPG: {e!r}")
        if f: f.close()
        if dialog: dialog.close()
        display_message('Chyba při generování EPG!')

def iptv_sc_rec(channelName, startdatetime):
    """Zpracování nahrávek z IPTV SC"""
    channels = Channels()
    channels_list = channels.get_channels_list('name', visible_filter = False)
    from_ts = int(time.mktime(time.strptime(startdatetime, '%d.%m.%Y %H:%M')))
    den = datetime.fromtimestamp(from_ts).strftime('%Y-%m-%d')
    epg = get_epg_date(channelKey=channels_list[channelName]['id'], date=den)
    if len(epg) > 0 and from_ts in epg:
        add_recording(epg[from_ts]['epgId'])
    else:
        display_message('Pořad ve SledováníTV nenalezen! Používáte EPG z doplňku SledováníTV?')
