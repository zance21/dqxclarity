import sys
import os
from json import dumps

def quest_text_shellcode(
    ebx_address: int,
    esi_address: int,
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
    import logging
    from hook import unpack_to_int
    from memory import (
        write_bytes,
        read_string)
    from translate import (
        query_string_from_file,
        detect_lang,
        clean_up_and_return_items,
        quest_translate
    )

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

    quest_file = 'adhoc_quests_requests'

    quest_names_addr = unpack_to_int({esi_address})[0]
    quest_desc_addr = unpack_to_int({ebx_address})[0]

    subquest_name_addr = quest_names_addr + 20
    quest_name_addr = quest_names_addr + 76
    quest_desc_addr = quest_desc_addr + 132
    quest_rewards_addr = quest_desc_addr + 508
    quest_repeat_rewards_addr = quest_desc_addr + 612

    subquest_name_ja = read_string(subquest_name_addr)
    logger.debug('Subquest: ' + str(subquest_name_ja))
    quest_name_ja = read_string(quest_name_addr)
    logger.debug('Quest Name: ' + str(quest_name_ja))
    quest_desc_ja = read_string(quest_desc_addr)
    logger.debug('Quest Description: ' + str(quest_desc_ja))
    quest_rewards_ja = read_string(quest_rewards_addr)
    logger.debug('Quest Rewards: ' + str(quest_rewards_ja))
    quest_repeat_rewards_ja = read_string(quest_repeat_rewards_addr)
    logger.debug('Quest Repeat Rewards: ' + str(quest_repeat_rewards_ja))

    if detect_lang(quest_desc_ja):
        if subquest_name_ja:
            subquest_name_en = query_string_from_file(subquest_name_ja, quest_file)
            if subquest_name_en:
                write_bytes(subquest_name_addr, str.encode(subquest_name_en) + b'\x00')
        if quest_name_ja:
            quest_name_en = query_string_from_file(quest_name_ja, quest_file)
            if quest_name_en:
                write_bytes(quest_name_addr, str.encode(quest_name_en) + b'\x00')
        if quest_rewards_ja:
            quest_rewards_en = clean_up_and_return_items(quest_rewards_ja)
            if quest_rewards_en:
                write_bytes(quest_rewards_addr, str.encode(quest_rewards_en) + b'\x00')
        if quest_repeat_rewards_ja:
            quest_repeat_rewards_en = clean_up_and_return_items(quest_repeat_rewards_ja)
            if quest_repeat_rewards_en:
                write_bytes(quest_repeat_rewards_addr, str.encode(quest_repeat_rewards_en) + b'\x00')
        if quest_desc_ja:
            quest_desc_en = quest_translate('{api_service}', '{api_pro}', quest_desc_ja, '{api_key}', '{api_region}')
            if quest_desc_en:
                write_bytes(quest_desc_addr, str.encode(quest_desc_en) + b'\x00')
except:
    with open('out.log', 'a+') as f:
        f.write(format_exc())
    """

    return str(shellcode)
