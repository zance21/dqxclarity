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
    debug: bool,
) -> str:
    """
    Returns shellcode for the translate function hook.
    eax_address: Where text can be modified to be fed to the screen
    ebx_address: NPC name
    """
    local_paths = dumps(sys.path).replace("\\", "\\\\")
    working_dir = dumps(os.getcwd()).replace("\\", "\\\\")

    shellcode = fr"""
import sys
from traceback import format_exc
from os import chdir

local_paths = {local_paths}
working_dir = {working_dir}
debug = {debug}
api_logging = {api_logging}

sys.path = local_paths
chdir(working_dir)

try:
    from hook import unpack_to_int
    from clarity import write_adhoc_entry, setup_logger
    from memory import (
        read_bytes,
        write_bytes,
        read_string,
        find_first_match,
        scan_backwards)
    from translate import (
        sanitized_dialog_translate,
        sqlite_read,
        sqlite_write,
        detect_lang
    )
    from errors import AddressOutOfRange
    from signatures import index_pattern, foot_pattern

    logger = setup_logger('out', 'out.log', 'translate')
    game_text_logger = setup_logger('gametext', 'game_text.log', 'game_text')

    # get address values where text can be identified
    npc_address = unpack_to_int({ebx_address})[0]
    ja_address = unpack_to_int({eax_address})[0]

    ja_text = read_string(ja_address)

    if api_logging:
        game_text_logger.info(ja_text)

    if detect_lang(ja_text):
        if find_first_match(ja_address, foot_pattern) != False:
            logger.info('Adhoc address found @ ' + str(hex(ja_address)))
            adhoc_address = scan_backwards(ja_address, index_pattern)
            if adhoc_address:
                if read_bytes(adhoc_address - 2, 1) != b'\x69':
                    adhoc_bytes = read_bytes(adhoc_address, 64)
                    if adhoc_bytes:
                        adhoc_write = write_adhoc_entry(adhoc_address, str(adhoc_bytes.hex()))
                        if adhoc_write['success']:
                            logger.info('Wrote adhoc file (' + str(adhoc_write['file']) + ')')
                        elif adhoc_write['file'] is not None:
                            logger.info('New adhoc file. Writing to new_adhoc_dumps.')
                        elif adhoc_write['file'] is None:
                            logger.info('This file already exists in new_adhoc_dumps. Needs merge into github.')
                        write_bytes(adhoc_address - 2, b'\x69')  # leave our mark to let us know we wrote this. nice.
        else:
            logger.info('Dynamic address found @ ' + str(hex(ja_address)))
            try:
                npc = read_string(npc_address)
            except:
                npc = ''
            result = sqlite_read(ja_text, '{api_region}', 'dialog')
            if result is not None:
                logger.info('Found database entry. No translation was needed.')
                write_bytes(ja_address, result.encode() + b'\x00')
            else:
                logger.info('Translation is needed for ' + str(len(ja_text) / 3) + ' characters. Sending to {api_service}')
                translated_text = sanitized_dialog_translate('{api_service}', '{api_pro}', ja_text, '{api_key}', '{api_region}')
                sqlite_write(ja_text, 'dialog', translated_text, '{api_region}', npc_name=npc)
                write_bytes(ja_address, translated_text.encode() + b'\x00')
    else:
        logger.info('English detected. Doing nothing.')
except AddressOutOfRange:
    pass
except:
    with open('out.log', 'a+') as f:
        f.write(format_exc())
    """

    return str(shellcode)


def load_evtx_shellcode(ecx_address: int) -> str:
    """
    Returns shellcode for the evtx load hook.
    ecx_address: Address where INDX starts
    """
    local_paths = dumps(sys.path).replace("\\", "\\\\")
    working_dir = dumps(os.getcwd()).replace("\\", "\\\\")

    shellcode = fr"""
import sys
from traceback import format_exc
from os import chdir

local_paths = {local_paths}
working_dir = {working_dir}
sys.path = local_paths
chdir(working_dir)

try:
    from hook import unpack_to_int
    from clarity import write_adhoc_entry, setup_logger
    from memory import read_bytes

    logger = setup_logger('out', 'out.log', 'load_evtx')

    indx_address = unpack_to_int({ecx_address})[0]
    adhoc_bytes = read_bytes(indx_address, 64)
    adhoc_write = write_adhoc_entry(indx_address, str(adhoc_bytes.hex()))
    if adhoc_write['success']:
        logger.info('Wrote adhoc file (' + str(adhoc_write['file']) + ')')
    elif adhoc_write['file'] is not None:
        logger.info('New cutscene file. Will write to new_adhoc_dumps if it does not already exist.')
    elif adhoc_write['file'] is None:
        logger.info('This file already exists in new_adhoc_dumps. Needs merge into github.')
except:
    with open('out.log', 'a+') as f:
        f.write(format_exc())
    """

    return str(shellcode)
