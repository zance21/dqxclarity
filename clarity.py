# -*- coding: utf-8 -*-
'''
Functions used by main.py to perform various actions that manipulate memory.
'''

from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from alive_progress import alive_bar
from numpy import byte
import click
import pymem
import pandas as pd
import requests
from dialog import read_string

INDEX_PATTERN = bytes.fromhex('49 4E 44 58 10 00 00 00')    # INDX block start
TEXT_PATTERN = bytes.fromhex('54 45 58 54 10 00 00')        # TEXT block start
END_PATTERN = bytes.fromhex('46 4F 4F 54 10 00 00')         # FOOT block start
HEX_DICT = 'hex_dict.csv'

def instantiate(exe):
    '''Instantiates a pymem instance that attaches to an executable.'''
    global PY_MEM  # pylint: disable=global-variable-undefined
    global HANDLE  # pylint: disable=global-variable-undefined

    try:
        PY_MEM = pymem.Pymem(exe)
        HANDLE = PY_MEM.process_handle
    except pymem.exception.ProcessNotFound:
        sys.exit(
            input(
                click.secho(
                    'Cannot find DQX. Ensure the game is launched and try'
                    'again.\nIf you launched DQX as admin, this program must'
                    'also run as admin.\n\nPress ENTER or close this window.',
                    fg='red'
                )
            )
        )

def address_scan(
    handle: int, pattern: bytes, multiple: bool, *, index_pattern_list,
    start_address = 0, end_address = 0x7FFFFFFF
    ):
    '''
    Scans the entire virtual memory space for a handle and returns addresses
    that match the given byte pattern.
    '''
    next_region = start_address
    while next_region < end_address:
        next_region, found = pymem.pattern.scan_pattern_page(
                                handle, next_region, pattern,
                                return_multiple = multiple)
        if found and multiple:
            index_pattern_list.append(found)
        elif found and not multiple:
            return index_pattern_list.append(found)

def read_bytes(address, byte_count):
    '''Reads the given number of bytes starting at an address.'''
    return PY_MEM.read_bytes(address, byte_count)

def jump_to_address(handle, address, pattern):
    '''
    Jumps to the next matched address that matches a pattern. This function
    exists as `scan_pattern_page` errors out when attempting to read protected
    pages, instead of just ignoring the page.
    '''
    mbi = pymem.memory.virtual_query(handle, address)
    page_bytes = pymem.memory.read_bytes(handle, address, mbi.RegionSize)
    match = re.search(pattern, page_bytes, re.DOTALL)

    if match:
        return address + match.span()[0]
    return None

def generate_hex(file):
    '''Parses a nested json file to convert strings to hex.'''
    en_hex_to_write = ''
    data = __read_json_file(file, 'en')

    for item in data:
        key, value = list(data[item].items())[0]
        if re.search('^clarity_nt_char', key):
            en = '00'
        elif re.search('^clarity_ms_space', key):
            en = '00e38080'
        else:
            ja = '00' + key.encode('utf-8').hex()
            ja_raw = key
            ja_len = len(ja)

            if value:
                en = '00' + value.encode('utf-8').hex()
                en_raw = value
                en_len = len(en)
            else:
                en = ja
                en_len = ja_len

            if en_len > ja_len:
                print('\n')
                print('String too long. Please fix and try again.')
                print(f'File: {file}.json')
                print(f'JA string: {ja_raw} (byte length: {ja_len})')
                print(f'EN string: {en_raw} (byte length: {en_len})')
                print('\n')
                print('Press ENTER to exit the program.')
                print('(and ignore this loading bar - it is doing nothing.)')
                sys.exit(input())

            ja = ja.replace('7c', '0a')
            ja = ja.replace('5c74', '09')
            en = en.replace('7c', '0a')
            en = en.replace('5c74', '09')

            if ja_len != en_len:
                while True:
                    en += '00'
                    new_len = len(en)
                    if (ja_len - new_len) == 0:
                        break

        en_hex_to_write += en

    return en_hex_to_write

def get_latest_from_weblate():
    '''
    Downloads the latest zip file from the weblate branch and
    extracts the json files into the appropriate folder.
    '''
    filename = os.path.join(os.getcwd(), 'weblate.zip')
    url = 'https://github.com/jmctune/dqxclarity/archive/refs/heads/weblate.zip'

    try:
        github_request = requests.get(url)
        with open(filename, 'wb') as zip_file:
            zip_file.write(github_request.content)
    except requests.exceptions.RequestException as e:
        sys.exit(
            click.secho(
                f'Failed to get latest files from weblate.\nMessage: {e}',
                fg='red'
            )
        )

    __delete_folder('json/_lang/en/dqxclarity-weblate')
    __delete_folder('json/_lang/en/en')

    with zipfile.ZipFile('weblate.zip') as archive:
        for file in archive.namelist():
            if file.startswith('dqxclarity-weblate/json/_lang/en'):
                archive.extract(file, 'json/_lang/en/')
                name = os.path.splitext(os.path.basename(file))
                shutil.move(
                    f'json/_lang/en/{file}',
                    f'json/_lang/en/{name[0]}{name[1]}'
                )
            if file.startswith('dqxclarity-weblate/json/_lang/ja'):
                archive.extract(file, 'json/_lang/ja/')
                name = os.path.splitext(os.path.basename(file))
                shutil.move(
                    f'json/_lang/ja/{file}',
                    f'json/_lang/ja/{name[0]}{name[1]}'
                )
            if file.startswith(f'dqxclarity-weblate/{HEX_DICT}'):
                archive.extract(file, '.')
                name = os.path.splitext(os.path.basename(file))
                shutil.move(
                    f'{file}',
                    f'{name[0]}{name[1]}'
                )

    __delete_folder('json/_lang/en/dqxclarity-weblate')
    __delete_folder('json/_lang/en/en')
    __delete_folder('json/_lang/ja/dqxclarity-weblate')
    __delete_folder('json/_lang/ja/ja')
    __delete_folder('hex/files/dqxclarity-weblate')
    __delete_folder('dqxclarity-weblate')
    os.remove('weblate.zip')
    click.secho('Now up to date!', fg='green')

def translate():
    '''Executes the translation process.'''
    instantiate('DQXGame.exe')

    index_pattern_list = []
    address_scan(HANDLE, INDEX_PATTERN, True, index_pattern_list = index_pattern_list)
    data_frame = pd.read_csv(HEX_DICT, usecols = ['file', 'hex_string'])

    with alive_bar(len(__flatten(index_pattern_list)),
                                title='Translating..',
                                spinner='pulse',
                                bar='bubbles',
                                length=20) as increment_progress_bar:
        for address in __flatten(index_pattern_list):
            increment_progress_bar()
            hex_result = __split_string_into_spaces(read_bytes(address, 64).hex().upper())
            csv_result = __flatten(data_frame[data_frame.hex_string == hex_result].values.tolist())
            if csv_result != []:
                file = __parse_filename_from_csv_result(csv_result)
                hex_to_write = bytes.fromhex(generate_hex(file))
                start_addr = jump_to_address(HANDLE, address, TEXT_PATTERN)
                if start_addr:
                    start_addr = start_addr + 14
                    result = type(byte)
                    while True:
                        start_addr = start_addr + 1
                        result = read_bytes(start_addr, 1)
                        if result != b'\x00':
                            start_addr = start_addr - 1
                            break

                    pymem.memory.write_bytes(HANDLE, start_addr, hex_to_write, len(hex_to_write))

    click.secho('Done. Continuing to scan for changes. Minimize this window and enjoy!', fg='green')

def scan_for_ad_hoc_game_files(debug):
    '''
    Continuously scans the DQXGame process for known addresses
    that are only loaded 'on demand'. Will pass the found
    address to translate().
    '''
    instantiate('DQXGame.exe')
    print('Starting adhoc scanning.')
    
    while True:
        index_pattern_list = []
        address_scan(HANDLE, INDEX_PATTERN, True, index_pattern_list = index_pattern_list)
        data_frame = pd.read_csv(HEX_DICT, usecols = ['file', 'hex_string'])

        for address in __flatten(index_pattern_list):  # pylint: disable=too-many-nested-blocks
            hex_result = __split_string_into_spaces(read_bytes(address, 64).hex().upper())
            csv_result = __flatten(data_frame[data_frame.hex_string == hex_result].values.tolist())
            if csv_result != []:
                file = __parse_filename_from_csv_result(csv_result)
                if 'adhoc' in file:
                    hex_to_write = bytes.fromhex(generate_hex(file))
                    start_addr = jump_to_address(HANDLE, address, TEXT_PATTERN)
                    if start_addr:
                        start_addr = start_addr + 14
                        result = type(byte)
                        while True:
                            start_addr = start_addr + 1
                            result = read_bytes(start_addr, 1)
                            if result != b'\x00':
                                start_addr = start_addr - 1
                                break

                        pymem.memory.write_bytes(HANDLE, start_addr, hex_to_write, len(hex_to_write))
                        if debug:
                            print(f'Found adhoc file {file}')

def scan_for_npc_names(debug):
    '''
    Continuously scans the DQXGame process for known addresses
    that are related to a specific pattern to translate names.
    '''
    instantiate('DQXGame.exe')
    
    npc_data = __read_json_file('npc_names', 'en')
    monster_data = __read_json_file('monsters', 'en')
    
    print('Starting name scanning.')
    
    while True:
        byte_pattern = rb'[\x5C\x2C][\xBA\xCC]......\x68\xCC..[\xE3\xE4\xE5\xE6\xE7\xE8\xE9]'

        index_pattern_list = []
        address_scan(HANDLE, byte_pattern, True, index_pattern_list = index_pattern_list)

        if index_pattern_list == []:
            continue

        for address in __flatten(index_pattern_list):
            if read_bytes(address, 2) == b'\x5C\xBA':
                data = monster_data
                name_addr = address + 12  # jump to name
                end_addr = address + 12
            elif read_bytes(address, 2) == b'\x2C\xCC':
                data = npc_data
                name_addr = address + 12  # jump to name
                end_addr = address + 12
            else:
                continue

            name_hex = bytearray()
            result = ''
            while result != b'\x00':
                result = read_bytes(end_addr, 1)
                end_addr = end_addr + 1
                if result == b'\x00':
                    end_addr = end_addr - 1   # Remove the last 00
                    bytes_to_write = end_addr - name_addr

                name_hex += result

            name_hex = name_hex.rstrip(b'\x00')
            try:
                name = name_hex.decode('utf-8')
            except UnicodeDecodeError:
                continue
            for item in data:
                key, value = list(data[item].items())[0]
                if re.search(f'^{name}+$', key):
                    if value:
                        pymem.memory.write_bytes(HANDLE, name_addr, str.encode(value), bytes_to_write)
                        if debug:
                            print(f'{value} found.')

def scan_for_player_names(debug):
    '''
    Continuously scans the DQXGame process for known addresses
    that are related to a specific pattern to translate player names.
    '''
    instantiate('DQXGame.exe')

    with open(f'json/player_names.json', 'r', encoding='utf-8') as json_data:
        player_names = json.loads(json_data.read())

    byte_pattern = rb'\x00\x00\x00\x00\x00[\x90\xBC]..\x01.......\x01[\xE3\xE4\xE5\xE6\xE7\xE8\xE9]'
    print('Starting player name scanning..')

    while True:
        player_pattern_list = []
        address_scan(HANDLE, byte_pattern, True, index_pattern_list = player_pattern_list)
        if player_pattern_list == []:
            continue

        for address in __flatten(player_pattern_list): #17 
            player_name_address = address + 17
            try:
                ja_player_name = read_string(player_name_address)
            except UnicodeDecodeError:
                continue

            for item in player_names:
                key, value = list(player_names[item].items())[0]
                if re.search(f'^{ja_player_name}+$', key):
                    if value:
                        # add bullet to beginning of name so it doesn't turn red, which would
                        # indicate a GM name. Shows up in game as a space.
                        player_bytes = b'\x04' + value.encode('utf-8') + b'\x00'
                        pymem.memory.write_bytes(HANDLE, player_name_address, player_bytes, len(player_bytes))
                        if debug:
                            print(f'Replaced {key} with {value}')

def dump_all_game_files():  # pylint: disable=too-many-locals
    '''
    Searches for all INDEX entries in memory and dumps
    the entire region, then converts said region to nested json.
    '''
    instantiate('DQXGame.exe')
    __delete_folder('game_file_dumps')

    directories = [
        'game_file_dumps/known/en',
        'game_file_dumps/known/ja',
        'game_file_dumps/unknown/en',
        'game_file_dumps/unknown/ja'
    ]

    unknown_file = 1

    for folder in directories:
        Path(folder).mkdir(parents=True, exist_ok=True)

    data_frame = pd.read_csv(HEX_DICT, usecols = ['file', 'hex_string'])

    index_pattern_list = []
    address_scan(HANDLE, INDEX_PATTERN, True, index_pattern_list = index_pattern_list)

    with alive_bar(len(__flatten(index_pattern_list)),
                                title='Dumping..',
                                spinner='pulse',
                                bar='bubbles',
                                length=20) as bar:

        for address in __flatten(index_pattern_list):
            bar()
            
            hex_result = __split_string_into_spaces(read_bytes(address, 64).hex().upper())
            start_addr = jump_to_address(HANDLE, address, TEXT_PATTERN)
            if start_addr is not None:
                end_addr = []
                address_scan(HANDLE, END_PATTERN, False, index_pattern_list = end_addr, start_address = start_addr)
                end_addr = end_addr[0]
                if end_addr is not None:
                    bytes_to_read = end_addr - start_addr

                    game_data = read_bytes(
                        start_addr, bytes_to_read).hex()[24:].strip('00')
                    if len(game_data) % 2 != 0:
                        game_data = game_data + '0'

                    game_data = bytes.fromhex(game_data).decode('utf-8')
                    game_data = game_data.replace('\x0a', '\x7c')
                    game_data = game_data.replace('\x00', '\x0a')
                    game_data = game_data.replace('\x09', '\x5c\x74')

                    jsondata_ja = {}
                    jsondata_en = {}
                    number = 1

                    for line in game_data.split('\n'):
                        json_data_ja = __format_to_json(jsondata_ja, line, 'ja', number)
                        json_data_en = __format_to_json(jsondata_en, line, 'en', number)
                        number += 1

                    json_data_ja = json.dumps(
                        jsondata_ja,
                        indent=4,
                        sort_keys=False,
                        ensure_ascii=False
                    )
                    json_data_en = json.dumps(
                        jsondata_en,
                        indent=4,
                        sort_keys=False,
                        ensure_ascii=False
                    )

                    # Determine whether to write to consider file or not
                    csv_result = __flatten(
                        data_frame[data_frame.hex_string == hex_result].values.tolist())
                    if csv_result != []:
                        file = os.path.splitext(
                            os.path.basename(
                                csv_result[0]))[0].strip() + '.json'
                        json_path_ja = 'game_file_dumps/known/ja'
                        json_path_en = 'game_file_dumps/known/en'
                    else:
                        file = str(unknown_file) + '.json'
                        unknown_file += 1
                        json_path_ja = 'game_file_dumps/unknown/ja'
                        json_path_en = 'game_file_dumps/unknown/en'
                        print(f'Unknown file found: {file}')
                        __write_file(
                            'game_file_dumps',
                            'consider_master_dict.csv',
                            'a',
                            f'json\\_lang\\en\\{file},{hex_result}\n'
                        )

                    __write_file(json_path_ja, file, 'w+', json_data_ja)
                    __write_file(json_path_en, file, 'w+', json_data_en)

def migrate_translated_json_data():
    '''
    Runs _HyDE_'s json migration tool to move a populated nested
    json file to a file that was made with dump_all_game_files().
    '''
    old_directories = [
        'json/_lang/en'
    ]

    new_directories = [
        'game_file_dumps/known/en'
    ]

    # Don't reorganize these
    destination_directories = [
        'hyde_json_merge/src',
        'hyde_json_merge/dst',
        'hyde_json_merge/out'
    ]

    for folder in destination_directories:
        for filename in os.listdir(folder):
            os.remove(os.path.join(folder, filename))

    for folder in old_directories:
        src_files = os.listdir(folder)
        for filename in src_files:
            full_file_name = os.path.join(folder, filename)
            if os.path.isfile(full_file_name):
                shutil.copy(full_file_name, destination_directories[0])

    for folder in new_directories:
        src_files = os.listdir(folder)
        for filename in src_files:
            full_file_name = os.path.join(folder, filename)
            if os.path.isfile(full_file_name):
                shutil.copy(full_file_name, destination_directories[1])

    for filename in os.listdir('hyde_json_merge/src'):
        os.system(f'hyde_json_merge\json-conv.exe -s hyde_json_merge/src/{filename} -d hyde_json_merge/dst/{filename} -o hyde_json_merge/out/{filename}')  # pylint: disable=anomalous-backslash-in-string,line-too-long

def check_for_updates():
    url = 'https://raw.githubusercontent.com/jmctune/dqxclarity/main/sha'

    exe_sha = __get_sha('dqxclarity.exe')
    if exe_sha is False:
        click.secho(f'You must be debugging. Hello! ^^;', fg='green')
        return

    try:
        github_request = requests.get(url)
    except requests.exceptions.RequestException as e:
        click.secho(f'Failed to check latest version. Running anyways.\nMessage: {e}', fg='red')
        return
    
    if github_request.text != exe_sha:
        click.secho(f'An update is available at https://github.com/jmctune/dqxclarity/releases', fg='green')
    else:
        click.secho(f'Up to date!')
        
    return

def __read_json_file(base_filename, region_code):
    with open(f'json/_lang/{region_code}/{base_filename}.json', 'r', encoding='utf-8') as json_data:
        return json.loads(json_data.read())

def __write_file(path, filename, attr, data):
    '''Writes a string to a file.'''
    with open(f'{path}/{filename}', attr, encoding='utf-8') as open_file:
        open_file.write(data)

def __format_to_json(json_data, data, lang, number):
    '''Accepts data that is used to return a nested json.'''
    json_data[number]={}
    if data == '':
        json_data[number][f'clarity_nt_char_{number}']=f'clarity_nt_char_{number}'
    elif data == '　':
        json_data[number][f'clarity_ms_space_{number}']=f'clarity_ms_space_{number}'
    else:
        if lang == 'ja':
            json_data[number][data]=data
        else:
            json_data[number][data]=''

    return json_data

def __flatten(list_of_lists):
    '''Takes a list of lists and flattens it into one list.'''
    return [item for sublist in list_of_lists for item in sublist]

def __split_string_into_spaces(string):
    '''
    Breaks a string up by putting spaces between every two characters.
    Used to format a hex string.
    '''
    return " ".join(string[i:i+2] for i in range(0, len(string), 2))

def __delete_folder(folder):
    '''Deletes a folder and all subfolders.'''
    shutil.rmtree(folder, ignore_errors=True)

def __parse_filename_from_csv_result(csv_result):
    '''Parse the filename from the supplied csv result.'''
    return os.path.splitext(os.path.basename(csv_result[0]))[0].strip()

def __get_sha(file):
    try:
        with open(file,"rb") as f:
            bytes = f.read()
            return hashlib.sha256(bytes).hexdigest()
    except:
        return False