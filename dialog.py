from clarity import *
import ctypes
import datetime
import configparser
import abbreviate
from itertools import groupby
from os.path import exists
import re
import time
import sqlite3
import textwrap

PROC_NAME = 'DQXGame.exe'

def scan_for_dialog(debug):
    '''
    Continuously scans the DQXGame process for known addresses
    that are related to a specific pattern for the comms window.
    '''
    instantiate(PROC_NAME)

    config_values = json.loads(determine_translation_service())
    enable_deepl_translate = config_values['EnableDeepLTranslate']
    enable_deepl_pro_apis = config_values['EnableDeepLProAPIs']
    deepl_translate_key = config_values['DeepLTranslateKey']
    enable_google_translate = config_values['EnableGoogleTranslate']
    google_translate_key = config_values['GoogleTranslateKey']
    enable_dialog_logging = config_values['EnableDialogLogging']
    region_code = config_values['RegionCode'].lower()

    if enable_deepl_translate == 'True':
        translation_service = 'deepl'
        api_key = deepl_translate_key
        is_pro = enable_deepl_pro_apis
    elif enable_google_translate == 'True':
        translation_service = 'google'
        api_key = google_translate_key
        is_pro = 'False'

    print('Starting dialog scanning.')

    while True:
        pattern = rb'\x90\x00\x00\x00....[\xE2\xE3\xE4\xE5\xE6\xE7\xE8\xE9\xEF]'
        #dialog_hex = bytes(b'\xFF\xFF\xFF\x7F\xFF\xFF\xFF\x7F\x00\x00\x00\x00\x00\x00\x00\x00\xFD.\xA8\x99')

        dialog_address = PY_MEM.base_address + 0x01FEF614
        dialog_offsets = [0x8, 0x24, 0x4, 0x58, 0x44, 0x8, 0xD0]
        
        full_comm_dialog_sig_list = []
        full_comm_dialog_sig_list = [get_ptr_address(dialog_address, dialog_offsets)]

        if full_comm_dialog_sig_list == [] or full_comm_dialog_sig_list == [208]:
            time.sleep(.1)
            continue

        comm_line_list = []
        address_scan(HANDLE, pattern, True, index_pattern_list = comm_line_list)

        if comm_line_list == []:
            continue

        jumbled_comm_line_list = []
        for address in full_comm_dialog_sig_list:
            full_comm_dialog_address = PY_MEM.read_int(address + 36)

            try:
                full_comm_dialog = read_string(full_comm_dialog_address).splitlines()
            except UnicodeDecodeError:
                continue

            # sanitize selection strings from dialog
            sanitized_full_comm_dialog = __strip_text_between_tags_and_format(full_comm_dialog)

            if debug:
                print('------------------------------------------')
                print(f'Signature scan address: {hex(address)}')
                print(f'Sentence address: {hex(full_comm_dialog_address)}')
                print('------------------------------------------')

            for address in __flatten(comm_line_list):
                # jump to the start of the text string
                comm_line_start = address + 8
                comm_line_end = address + 8
                while True:
                    comm_line_end = comm_line_end + 1
                    result = read_bytes(comm_line_end, 1)

                    if result == b'\x00':
                        bytes_to_read = (comm_line_end) - comm_line_start

                        try:
                            comm_line = read_bytes(comm_line_start, bytes_to_read).decode('utf-8')
                            if comm_line in sanitized_full_comm_dialog:
                                # when text falls off screen, either the 25th or 33rd byte from
                                # behind the sentence is marked as 80. we don't want this text.
                                if read_bytes(comm_line_start - 25, 1) != b'\x80':
                                    if read_bytes(comm_line_start - 33, 1) != b'\x80':
                                        jumbled_comm_line_list.append([comm_line_start, comm_line])
                        except UnicodeDecodeError:
                            break

        continue

        # no valid comms. window addresses were found, so start over
        if jumbled_comm_line_list == []:
            continue

        # see if we can figure out the order of the address. if not, we know the address used to be
        # in a previous comms window, but isn't in the active one.
        ordered_dialog_list = []
        for item in jumbled_comm_line_list:
            address = item[0]
            dialog = item[1]

            try:
                position = sanitized_full_comm_dialog.index(dialog)
                ordered_dialog_list.append([position, address, dialog])
                ordered_dialog_list.sort()

                if debug:
                    print(f'[{hex(address)}] {dialog}')
            except:
                continue

        if ordered_dialog_list == []:
            continue

        # before we write, we need to evaluate if we found all of the relevant addresses so we don't
        # partially write the translated text
        sanitized_list_of_lists = [list(g) for k, g in groupby(sanitized_full_comm_dialog, key=bool) if k]
        the_position = __get_list_of_lists_position(sanitized_list_of_lists, ordered_dialog_list)

        # check if the number of found dialog lines equals the number of found comms. window lines
        ordered_dialog_list_count = len(sanitized_list_of_lists[the_position])
        comm_line_count = len(ordered_dialog_list)

        # something isn't right if we get inside this block. we either found duplicate addresses 
        # or we didn't find them all yet.
        if comm_line_count != ordered_dialog_list_count:
            if debug:
                print('All addresses not yet found. Re-scanning.')
            continue

        # prep text to translate
        japanese_dialog_to_translate_list = []
        for item in sanitized_list_of_lists[the_position]:
            dialog = item
            japanese_dialog_to_translate_list.append(dialog)
        japanese_dialog_to_translate = ''.join(japanese_dialog_to_translate_list)
        
        # read from database to see if text exists
        db_result = sqlite_read(japanese_dialog_to_translate, region_code)
        if db_result is None:
            if debug:
                print('Sent to translation service.')
            stripped_japanese_dialog_to_translate = re.sub('「', '', japanese_dialog_to_translate)
            translated_text = translate(translation_service, is_pro, stripped_japanese_dialog_to_translate, api_key, region_code)
            sqlite_write(japanese_dialog_to_translate, translated_text, region_code)
            write_to_log(enable_dialog_logging, japanese_dialog_to_translate, translated_text, region_code)
        else:
            if debug:
                print('Found database entry!')
            translated_text = db_result
            write_to_log(enable_dialog_logging, japanese_dialog_to_translate, translated_text, region_code)
        
        # we're limited on the amount of text we can enter in a comms. window. 45 characters is a
        # good looking limit. if we exceed the maximum number of lines * 45, we use abbreviate to
        # truncate more common words to try to make the text fit inside the window.
        abbr = abbreviate.Abbreviate()
        wrapped_comm_line_text = abbr.abbreviate(translated_text, 45 * comm_line_count)
        wrapped_comm_line_text = textwrap.fill(wrapped_comm_line_text, 45)

        count = -1
        for item in ordered_dialog_list:
            count += 1
            address = item[1]

            # if the japanese was originally three lines, but the text returned from translation is
            # two lines, we need to clear the last line out so japanese doesn't remain after we've
            # written the text.
            if (ordered_dialog_list_count - 1) == count:
                try:
                    text_to_write = bytes.fromhex(wrapped_comm_line_text.split('\n')[count].encode('utf-8').hex() + '00')
                    pymem.memory.write_bytes(HANDLE, address, text_to_write, len(text_to_write))
                    break
                except:
                    text_to_write = bytes.fromhex('00')
                    pymem.memory.write_bytes(HANDLE, address, text_to_write, len(text_to_write))
                    break

            text_to_write = bytes.fromhex(wrapped_comm_line_text.split('\n')[count].encode('utf-8').hex() + '00')
            pymem.memory.write_bytes(HANDLE, address, text_to_write, len(text_to_write))

        continue

def __flatten(list_of_lists):
    '''Takes a list of lists and flattens it into one list.'''
    return [item for sublist in list_of_lists for item in sublist]

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

def read_bytes(address, byte_count):
    '''Reads the given number of bytes starting at an address.'''
    return PY_MEM.read_bytes(address, byte_count)

def read_string(address):
    '''Reads a string from memory at the given address.'''
    instantiate(PROC_NAME)

    end_addr = address

    if end_addr is not None:
        while True:
            result = PY_MEM.read_bytes(end_addr, 1)
            end_addr = end_addr + 1
            if result == b'\x00':
                bytes_to_read = end_addr - address
                break

        return PY_MEM.read_string(address, bytes_to_read)

def deep_index(lst, w):
    '''
    Gets the index of a list in a list.
    Credit: https://stackoverflow.com/a/15233895/4560741
    '''
    return [(i, sub.index(w)) for (i, sub) in enumerate(lst) if w in sub]

def deepl_translate(dialog_text, is_pro, api_key, region_code):
    '''Uses DeepL Translate to translate text to the specified language.'''
    if is_pro == 'True':
        api_url = 'https://api.deepl.com/v2/translate'
    else:
        api_url = 'https://api-free.deepl.com/v2/translate'

    payload = {'auth_key': api_key, 'text': dialog_text, 'target_lang': region_code}
    r = requests.post(api_url, data=payload)
    translated_text = r.content

    return json.loads(translated_text)['translations'][0]['text']

def google_translate(dialog_text, api_key, region_code):
    '''Uses Google Translate to translate text to the specified language.'''
    uri = '&source=ja&target=' + region_code + '&q=' + dialog_text
    api_url = 'https://www.googleapis.com/language/translate/v2?key=' + api_key + uri
    headers = {'Content-Type': 'application/json'}

    r = requests.post(api_url, headers=headers)
    translated_text = r.content
    
    return json.loads(translated_text)['data']['translations'][0]['translatedText']

def translate(translation_service, is_pro, dialog_text, api_key, region_code):
    if translation_service == 'deepl':
        return deepl_translate(dialog_text, is_pro, api_key, region_code)
    elif translation_service == 'google':
        return google_translate(dialog_text, api_key, region_code)

def write_to_log(is_enabled, source_text, translated_text, language):
    '''Logs text to a file.'''
    if is_enabled == 'True':
        data = logger_timestamp() + '\n' + 'ja: ' + source_text + '\n' + language + ': ' + translated_text  + '\n\n'
        with open('dqx_text_log.txt', 'a', encoding='utf-8') as open_file:
            open_file.write(data)

def sqlite_read(text_to_query, language):
    '''Reads text from the database.'''
    escaped_text = text_to_query.replace("'","''")

    try:
        conn = sqlite3.connect('clarity_dialog.db')
        cursor = conn.cursor()
        selectQuery = f'SELECT {language} FROM dialog WHERE ja = \'{escaped_text}\''
        cursor.execute(selectQuery)
        results = cursor.fetchone()
        
        if results is not None:
            return results[0].replace("''", "'")
        else:
            return None
        
    except sqlite3.Error as error:
        print(f'[DEBUG] Failed to query SQLite: {error}')
    finally:
        if conn:
            conn.close()

def sqlite_write(source_text, translated_text, language):
    '''Writes or updates text to the database.'''
    escaped_text = translated_text.replace("'","''")

    try:
        conn = sqlite3.connect("clarity_dialog.db")
        selectQuery = f'SELECT ja FROM dialog WHERE ja = \'{source_text}\''
        insertQuery = f'INSERT INTO dialog (ja, {language}) VALUES (\'{source_text}\', \'{escaped_text}\')'
        updateQuery = f'UPDATE dialog SET {language} = \'{escaped_text}\' WHERE ja = \'{source_text}\''

        cursor = conn.cursor()
        results = cursor.execute(selectQuery)

        if results.fetchone() is None:
            cursor.execute(insertQuery)
        else:
            cursor.execute(updateQuery)

        conn.commit()
        cursor.close()
    except sqlite3.Error as error:
        print(f'[DEBUG] Failed to add data to SQLite: {error}')
    finally:
        if conn:
            conn.close()

def get_ptr_address(base, offsets):
    '''Obtains the address a pointer is pointing to.'''
    instantiate('DQXGame.exe')
    
    addr = PY_MEM.read_int(base)
    for offset in offsets:
        if offset != offsets[-1]:
            addr = PY_MEM.read_int(addr + offset)
            
    return addr + offsets[-1]

def check_deepl_remaining_char_count(key, is_pro):
    if is_pro == 'True':
        url = "https://api.deepl.com/v2"
    else:
        url = "https://api-free.deepl.com/v2"
    url += "/usage?auth_key=" + key
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to validate.")
        return False
    else:
        json = response.json()
        char_left = json['character_limit'] - json['character_count']
        print(f'{char_left} characters remaining.')
        return True

def test_google_translate_api_key(key):
    body = "&source=ja" + "&target=" + 'en' + "&q="
    url = "https://www.googleapis.com/language/translate/v2?key=" + key + body
    response = requests.get(url)
    if response.status_code == 200:
        print("Key validated successfully!")
        return True
    else:
        print("Failed to validate.")
        return False

def determine_translation_service():
    '''Parses the user config file to get information needed to make translation calls.'''
    filename = 'user_settings.ini'
    config = configparser.ConfigParser()
    if not exists(filename):
        config['translation'] = {'EnableDeepLTranslate': 'False',
                                'EnableDeepLProAPIs': 'False',
                                'DeepLTranslateKey': 'null',
                                'EnableGoogleTranslate': 'False',
                                'GoogleTranslateKey': 'null',
                                'RegionCode': 'EN'
                                }
        config['behavior'] = {}
        config['behavior']['EnableDialogLogging'] = 'False'
        with open(filename, 'w') as configfile:
            config.write(configfile)

    config.read(filename)
    if 'translation' in config:
        if 'EnableDeepLTranslate' in config['translation']:
            deepl_translate_choice = config['translation']['EnableDeepLTranslate']
        if 'EnableDeepLProAPIs' in config['translation']:
            deepl_pro = config['translation']['EnableDeepLProAPIs']
        if 'DeepLTranslateKey' in config['translation']:
            deepl_translate_key = config['translation']['DeepLTranslateKey']
        if 'EnableGoogleTranslate' in config['translation']:
            google_translate_choice = config['translation']['EnableGoogleTranslate']
        if 'GoogleTranslateKey' in config['translation']:
            google_translate_key = config['translation']['GoogleTranslateKey']
        if 'RegionCode' in config['translation']:
            region_code = config['translation']['RegionCode']
    if 'behavior' in config:
        if 'EnableDialogLogging' in config['behavior']:
            enable_dialog_logging = config['behavior']['EnableDialogLogging']

    if (deepl_translate_choice == 'False' and google_translate_choice == 'False'):
        ctypes.windll.user32.MessageBoxW(0, f"You need to enable a translation service in user_settings.ini. Open the file in Notepad and set it up.\n\nCurrent values:\n\nEnableDeepLTranslate: {config['translation']['EnableDeepLTranslate']}\nEnableGoogleTranslate: {config['translation']['EnableGoogleTranslate']}", "[dqxclarity] No translation service enabled", 0x10)
        sys.exit()

    if (deepl_translate_choice == 'True' and google_translate_choice == 'True'):
        ctypes.windll.user32.MessageBoxW(0, f"Only enable one translation service in user_settings.ini. Open the file in Notepad and set it up.\n\nCurrent values:\n\nEnableDeepLTranslate: {config['translation']['EnableDeepLTranslate']}\nEnableGoogleTranslate: {config['translation']['EnableGoogleTranslate']}", "[dqxclarity] Too many translation serviced enabled", 0x10)
        sys.exit()
        
    if (deepl_translate_choice != 'True' and deepl_translate_choice != 'False'):
        ctypes.windll.user32.MessageBoxW(0, f"Invalid value detected for EnableDeepLTranslate. Open user_settings.ini in Notepad and fix it.\n\nValid values are: True, False\n\nCurrent values:\n\nEnableDeepLTranslate: {config['translation']['EnableDeepLTranslate']}", "[dqxclarity] Misconfigured boolean", 0x10)
        sys.exit()
        
    if (google_translate_choice != 'True' and google_translate_choice != 'False'):
        ctypes.windll.user32.MessageBoxW(0, f"Invalid value detected for EnableGoogleTranslate. Open user_settings.ini in Notepad and fix it.\n\nValid values are: True, False\n\nCurrent values:\n\nEnableGoogleTranslate: {config['translation']['EnableGoogleTranslate']}", "[dqxclarity] Misconfigured boolean", 0x10)
        sys.exit()
        
    if (deepl_translate_key == 'null' and google_translate_key == 'null'):
        ctypes.windll.user32.MessageBoxW(0, f"You need to configure an API key in user_settings.ini. Open the file in Notepad and set it up.\n\nCurrent values:\n\nDeepLTranslateKey: {config['translation']['DeepLTranslateKey']}\nGoogleTranslateKey: {config['translation']['GoogleTranslateKey']}", "[dqxclarity] No API key configured", 0x10)
        sys.exit()
        
    if (deepl_pro != 'True' and deepl_pro != 'False'):
        ctypes.windll.user32.MessageBoxW(0, f"Invalid value detected for EnableDeepLProAPIs. Open user_settings.ini in Notepad and fix it.\n\nValid values are: True, False\n\nCurrent values:\n\nEnableDeepLProAPIs: {config['translation']['EnableDeepLProAPIs']}", "[dqxclarity] Misconfigured boolean", 0x10)
        sys.exit()
        
    if (enable_dialog_logging != 'True' and enable_dialog_logging != 'False'):
        ctypes.windll.user32.MessageBoxW(0, f"Invalid value detected for EnableDialogLogging. Open user_settings.ini in Notepad and fix it.\n\nValid values are: True, False\n\nCurrent values:\n\nEnableDialogLogging: {config['translation']['EnableDialogLogging']}", "[dqxclarity] Misconfigured boolean", 0x10)
        sys.exit()

    if deepl_translate_choice == 'True':
        if not check_deepl_remaining_char_count(deepl_translate_key, deepl_pro):
            ctypes.windll.user32.MessageBoxW(0, f"Your DeepL API key did not validate successfully. Check the key and region code then try again.\n\nCurrent values:\n\nRegionCode: {config['translation']['RegionCode']}\nDeepLTranslateKey: {config['translation']['DeepLTranslateKey']}", "[dqxclarity] API key failed to validate", 0x10)
            sys.exit()
            
    if google_translate_choice == 'True':
        if not test_google_translate_api_key(google_translate_key):
            ctypes.windll.user32.MessageBoxW(0, f"Your Google Translate API key did not validate successfully. Check the key and region code then try again.\n\nCurrent values:\n\nRegionCode: {config['translation']['RegionCode']}\nGoogleTranslateKey: {config['translation']['GoogleTranslateKey']}", "[dqxclarity] API key failed to validate", 0x10)
            sys.exit()

    return json.dumps({'EnableDeepLTranslate': deepl_translate_choice, 
                       'EnableDeepLProAPIs': deepl_pro,
                       'DeepLTranslateKey': deepl_translate_key,
                       'EnableGoogleTranslate': google_translate_choice,
                       'GoogleTranslateKey': google_translate_key,
                       'EnableDialogLogging': enable_dialog_logging,
                       'RegionCode': region_code
                       })

def logger_timestamp():
    return '[' + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + ']'

def __strip_text_between_tags_and_format(comm_dialog):
    sanitized = comm_dialog
    try:
        sanitized = (sanitized[:sanitized.index('<select>')] + sanitized[sanitized.index('<select_end>')+1:])
    except:
        pass
    try:
        sanitized = (sanitized[:sanitized.index('<select_se_off>')] + sanitized[sanitized.index('<select_end><break>')+1:])
    except:
        pass
    try:
        sanitized = (sanitized[:sanitized.index('<select_se_off>')] + sanitized[sanitized.index('<select_end>')+1:])
    except:
        pass
    try:
        sanitized = (sanitized[:sanitized.index('<open_irai>')] + sanitized[sanitized.index('<select_end><close>')+1:])
    except:
        pass
    try:
        sanitized = (sanitized[:sanitized.index('<select_se_off>')] + sanitized[sanitized.index('<select_end><close>')+1:])
    except:
        pass
    
    sanitized = '\n'.join(str(e) for e in sanitized)

    # replace all <br> tags with '', which we'll use for splitting off of
    sanitized = re.sub('<br>', '', sanitized)
    sanitized = re.sub('(<.+?>)', '', sanitized)
    sanitized = sanitized.splitlines()
    
    return sanitized

def __get_list_of_lists_position(full_dialog, ordered_dialog_list):
    '''
    Dialog may look like the following:
    
    それでは　さっそく　くわしい説明を　させていただきましょう。
    ドレスアップ屋の　看板だ。
    <br>
    ただし　カラーが　元のままの時は　ツヤを変更することが　できません。
    カラーリングする説明を聞く
    ありがとうございました。　またのご来店を　お待ちしております。
    <br>
    この旅の扉からは
    いくつかの場所に移動できそうだ。
    どこへ　移動しますか？
    <break>
    
    This function lets us know which position of the dialog we're in so we know what 
    text we're looking for to ensure a match.
    '''
    get_index = deep_index(full_dialog, ordered_dialog_list[0][2])
    get_index_of_index = [x for x,_ in get_index]
    
    return get_index_of_index[0]
