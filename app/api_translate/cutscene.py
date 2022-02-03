import sys
import os
from json import dumps

def cutscene_shellcode(
    edi_address: str) -> str:
    '''
    Returns shellcode for the cutscene file dump function hook.

    edi_address: Where adhoc text for cutscene can be found.
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
    from clarity import write_adhoc_entry, setup_logger
    from memory import (
        read_bytes,
        write_bytes,
        scan_backwards)
    from errors import AddressOutOfRange
    from signatures import index_pattern, foot_pattern

    logger = setup_logger('out', 'out.log', 'cutscene')

    # get address values where text can be identified
    ja_address = unpack_to_int({edi_address})[0]
    logger.info('Cutscene address found @ ' + str(hex(ja_address)))
    adhoc_address = scan_backwards(ja_address, index_pattern)
    if read_bytes(adhoc_address - 2, 1) != b'\x69':
        adhoc_bytes = read_bytes(adhoc_address, 64)
        adhoc_write = write_adhoc_entry(adhoc_address, str(adhoc_bytes.hex()))
        if adhoc_write['success']:
            logger.debug('Wrote cutscene file (' + str(adhoc_write['file']) + ')')
        elif adhoc_write['file'] is not None:
            logger.debug('New cutscene file. Will write to new_adhoc_dumps if it does not already exist.')
        elif adhoc_write['file'] is None:
            logger.debug('This file already exists in new_adhoc_dumps. Needs merge into github.')
        write_bytes(adhoc_address - 2, b'\x69')  # write our state byte so we know we already wrote this. nice.
except:
    with open('out.log', 'a+') as f:
        f.write(format_exc())
    """

    return str(shellcode)
