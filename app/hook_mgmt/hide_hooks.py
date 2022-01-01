import struct
import time
import sys
from loguru import logger
from memory import (
    read_bytes,
    write_bytes,
    pattern_scan,
    get_base_address,
    get_ptr_address
)
from signatures import (
    loading_pointer,
    loading_offsets,
    cutscene_pattern
)

def unpack_to_int(address: int):
    '''
    Unpacks the address from little endian and returns the appropriate bytes.
    '''
    unpacked_address = struct.unpack('<i', address)

    return unpacked_address

def unpack_address_to_int(address: int):
    '''
    Reads the first four bytes of memory and unpacks it into an address.
    '''
    value = read_bytes(address, 4)
    
    return struct.unpack('<i', value)[0]

def load_unload_hooks(hook_list: list, debug: bool):
    '''
    Load/unload hooks based on conditionals.

    DQX does a check against what's in memory against what's in the binary. If it doesn't match,
    the client will crash with INVALID_CALL_1. This function will unload active hooks in the event
    of a loading screen and load them back when the game returns.

    All hooks being passed to this function should be in a dict.
    '''
    if not debug:
        logger.remove()
        logger.add(sys.stderr, level="INFO")

    state = 1
    base_address = get_base_address()
    loading_addr = get_ptr_address(base_address + loading_pointer, loading_offsets)
    cutscene_addr = pattern_scan(cutscene_pattern, module='DQXGame.exe') - 212
    
    logger.debug(f'Loading address: {hex(loading_addr)}')
    logger.debug(f'Cutscene address: {hex(cutscene_addr)}')

    while True:
        time.sleep(0.01)
        state_byte = read_bytes(loading_addr, 1)
        cutscene_byte = read_bytes(cutscene_addr, 1)

        try:
            if state_byte == b'\x00' and state == 1:  # loading screen. unhook
                for hook in hook_list:
                    write_bytes(hook['detour_address'], hook['original_bytes'])
                logger.debug('Hooks unloaded.')
                state = 0
            elif state_byte != b'\x00' and state == 0:  # we're ok to hook now
                for hook in hook_list:
                    write_bytes(hook['detour_address'], hook['hook_bytes'])
                logger.debug('Hooks loaded.')
                state = 1

            # cutscene logic
            if cutscene_byte != b'\x00':  # separate check as state byte can't see we're in a cutscene
                for i in range(300):  # check for 1~ seconds to finish loading and account for user skipping
                    time.sleep(0.01)
                    cutscene_byte = read_bytes(cutscene_addr, 1)
                    if i == 299:
                        for hook in hook_list:
                            if hook['hook_name'] != 'walkthrough_detour':
                                write_bytes(hook['detour_address'], hook['hook_bytes'])
                        state = 1
                        logger.debug('Hooks loaded for cutscene.')
                    elif cutscene_byte != b'\x00':
                        continue
                    else:
                        logger.debug('Cutscene skip was detected.')
                        time.sleep(3)
                        break
                while True:
                    time.sleep(0.01)
                    cutscene_byte = read_bytes(cutscene_addr, 1)
                    if cutscene_byte == b'\x00':
                        logger.debug('Hooks unloaded as cutscene finished.')
                        for hook in hook_list:
                            write_bytes(hook['detour_address'], hook['original_bytes'])
                        state = 0
                        break
        except:
            for hook in hook_list:
                write_bytes(hook['detour_address'], hook['original_bytes'])
            sys.exit()
