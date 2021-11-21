import sys
import os
from json import dumps

def cutscene_shellcode(
    esi_address: str,
    api_service: str,
    api_key: str,
    api_pro: str,
    api_logging: str,
    api_region: str,
    debug: bool) -> str:
    '''
    Returns shellcode for the cutscene function hook.

    esi_address: Where text for cutscene triggers can be found.
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
sys.path = local_paths
chdir(working_dir)

try:
    import logging
    from hook import unpack_to_int
    from clarity import write_adhoc_entry
    from memory import (
        read_bytes,
        write_bytes,
        read_string,
        scan_backwards)
    from errors import AddressOutOfRange
    from translate import sanitized_dialog_translate, sqlite_read, sqlite_write_dynamic
    from signatures import index_pattern, foot_pattern

    def setup_logger(name, log_file, level=logging.INFO):
        formatter = logging.Formatter('%(asctime)s %(message)s')
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setFormatter(formatter)

        logger = logging.getLogger(name)
        if (logger.hasHandlers()):
            logger.handlers.clear()

        logger.setLevel(level)
        logger.addHandler(handler)

        return logger

    logger = setup_logger('out', 'out.log')
    if debug:
        logger.setLevel(logging.DEBUG)
    game_text_logger = setup_logger('gametext', 'game_text.log')

    # get address values where text can be identified
    ja_address = unpack_to_int({esi_address})[0]
    logger.debug('cutscene address found :: checking if translation is needed')
    ja_text = read_string(ja_address)
    logger.debug(ja_text)
    result = sqlite_read(ja_text, 'en')
    
    if api_logging:
        game_text_logger.info(ja_text)

    if result is not None:
        logger.debug('found database entry. no translation needed')
        write_bytes(ja_address, result.encode() + b'\x00')
    else:
        logger.debug('translation needed. sending to {api_service}')
        translated_text = sanitized_dialog_translate('{api_service}', '{api_pro}', ja_text, '{api_key}', '{api_region}')
        logger.debug(translated_text)
        sqlite_write_dynamic(ja_text, '', translated_text, 'en')
        logger.debug('database record inserted.')
        write_bytes(ja_address, translated_text.encode() + b'\x00')
except AddressOutOfRange:
    pass
except:
    with open('out.log', 'a+') as f:
        f.write(format_exc())
    """

    return str(shellcode)

def cutscene_file_dump_shellcode(
    ecx_address: str,
    api_service: str,
    api_key: str,
    api_pro: str,
    api_logging: str,
    api_region: str) -> str:
    '''
    Returns shellcode for the cutscene file dump function hook.

    ecx_address: Where adhoc text for cutscene can be found.
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
sys.path = local_paths
chdir(working_dir)

try:
    import logging
    from hook import unpack_to_int
    from clarity import write_adhoc_entry
    from memory import (
        read_bytes,
        write_bytes,
        read_string,
        scan_backwards)
    from errors import AddressOutOfRange
    from signatures import index_pattern, foot_pattern

    def setup_logger(name, log_file, level=logging.INFO):
        formatter = logging.Formatter('%(asctime)s %(message)s')
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setFormatter(formatter)

        logger = logging.getLogger(name)
        if (logger.hasHandlers()):
            logger.handlers.clear()

        logger.setLevel(level)
        logger.addHandler(handler)

        return logger

    logger = setup_logger('out', 'out.log')
    if debug:
        logger.setLevel(logging.DEBUG)

    # get address values where text can be identified
    ja_address = unpack_to_int({ecx_address})[0]

    logger.debug('adhoc cutscene file found :: checking if we have this file')
    adhoc_address = scan_backwards(ja_address, index_pattern)
    adhoc_bytes = read_bytes(adhoc_address, 64)
    adhoc_write = write_adhoc_entry(adhoc_address, str(adhoc_bytes.hex()))
    if adhoc_write['success']:
        logger.debug('Wrote adhoc file.')
    elif adhoc_write['file'] is not None:
        logger.debug('New cutscene adhoc file. Will write to new_adhoc_dumps if it does not already exist.')
    elif adhoc_write['file'] is None:
        logger.debug('This file already exists in new_adhoc_dumps. Needs merge into github.')
except:
    with open('out.log', 'a+') as f:
        f.write(format_exc())
    """

    return shellcode
