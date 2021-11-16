import sys
import os
from json import dumps

def translate_shellcode(
    eax_address: int,
    ebx_address: int,
    api_service: str,
    api_key: str,
    api_pro: str,
    api_logging: str,
    api_region: str,
    debug: bool) -> str:
    '''
    Returns shellcode for the translate function hook.

    eax_address: Where text can be modified to be fed to the screen
    ebx_address: NPC name

    '''
    local_paths = dumps(sys.path).replace('\\', '\\\\')
    working_dir = dumps(os.getcwd()).replace('\\', '\\\\')

    shellcode = fr"""
import sys
import os
from traceback import format_exc
from os import chdir

local_paths = {local_paths}
working_dir = {working_dir}
debug = {debug}
api_logging = {api_logging}
sys.path = local_paths
chdir(working_dir)

try:
    from datetime import datetime
    import logging
    logging.basicConfig(
        filename='out.log',
        encoding='utf-8',
        level=logging.INFO,
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    from hook import unpack_to_int
    from clarity import write_adhoc_entry
    from memory import (
        read_bytes,
        write_bytes,
        read_string,
        scan_to_foot,
        scan_backwards)
    from errors import AddressOutOfRange
    from translate import sanitized_dialog_translate, sqlite_read, sqlite_write_dynamic
    from signatures import index_pattern, foot_pattern

    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # get address values where text can be identified
    npc_address = unpack_to_int({ebx_address})[0]
    ja_address = unpack_to_int({eax_address})[0]

    if scan_to_foot(ja_address) != False:
        logging.debug('adhoc address found :: checking if we have this file')
        adhoc_address = scan_backwards(ja_address, index_pattern)
        adhoc_bytes = read_bytes(adhoc_address, 64)
        success = write_adhoc_entry(adhoc_address, str(adhoc_bytes.hex()))
        if success:
            logging.debug('Wrote adhoc file.')
        else:
            logging.debug('New adhoc file. Will write to new_adhoc_dumps if it does not already exist.')
    else:
        logging.debug('dynamic address found :: checking if translation is needed')
        try:
            npc_name = read_string(npc_address)
        except:
            npc_name = ''
        ja_text = read_string(ja_address)
        logging.debug(ja_text)
        result = sqlite_read(ja_text, 'en')

        if result is not None:
            logging.debug('found database entry. no translation needed')
            write_bytes(ja_address, result.encode() + b'\x00')
        else:
            logging.debug('translation needed. sending to {api_service}')
            translated_text = sanitized_dialog_translate('{api_service}', '{api_pro}', ja_text, '{api_key}', '{api_region}')
            logging.debug(translated_text)
            sqlite_write_dynamic(ja_text, npc_name, translated_text, 'en')
            logging.debug('database record inserted.')
            write_bytes(ja_address, translated_text.encode() + b'\x00')

        if api_logging:
            date_format = datetime.now().strftime("[%Y-%m-%d %I:%M:%S %p]")
            with open('game_text.log', 'a+', encoding='utf-8') as f:
                f.write(date_format + '\n' + ja_text + '\n')
except AddressOutOfRange:
    pass
except:
    with open('out.log', 'a+') as f:
        f.write(format_exc())
    """

    return shellcode
