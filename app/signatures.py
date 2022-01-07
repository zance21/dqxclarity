'''
Signatures / addresses to known functions.
'''
#############################################
# Python functions. Will never change until
# Python dll version gets updated.
#############################################

# 55 8B EC 6A 00 FF 75 08 E8 43 CC FF FF 83 C4 08 5D
pyrun_simplestring = rb'\x55\x8B\xEC\x6A\x00\xFF\x75\x08\xE8\x43\xCC\xFF\xFF\x83\xC4\x08\x5D'

# 6A 00 E8 69 FF FF FF
py_initialize_ex = rb'\x6A[\x00\x01]\xE8\x69\xFF\xFF\xFF'

# 55 8B EC 83 E4 F8 83 EC 10 83 3D 6C 12
py_finalizer_ex = rb'\x55\x8B\xEC\x83\xE4\xF8\x83\xEC\x10\x83\x3D\x6C\x12'

#############################################
# DQX functions that shouldn't change much.
#############################################

# takes you to the section of the function where you can read where dialog is stored before
# it's read. captures npc text as well as adhoc files loaded into memory.
# 8D 4F 04 56 89 02 E8 ? ? ? ? 8B
dialog_trigger = rb'\x8D\x4F\x04\x56\x89\x02\xE8....\x8B'

# reading at this address will show you the adhoc file that's currently being read from. we use this
# to dump the adhoc file if we don't have it.
# 2B CF 8B C6 41 89 0A 5F 5E 5D
cutscene_trigger = rb'\x8B\xC6\x41\x89\x0A\x5F\x5E\x5D'

# function that is triggered when a quest window opens. used for translating quest text
# 8B 34 24 8D 64 24 04 8D 64 24 04 E9 ?? ?? ?? ?? 8D 64 24 FC 89 4C
# quest_text_trigger = rb'\x8B\x34\x24\x8D\x64\x24\x04\x8D\x64\x24\x04\xE9....\x8D\x64\x24\xFC\x89\x4C' // this works, but breaks because of AC in combat
quest_text_trigger = rb'\x8D\x8E\x78\x04\x00\x00\xE8....\x5F'

# function that is triggered when walkthrough text is displayed on the screen.
# read what's at esi here to get the address where the text is. overwrite to have it on the screen
# BF 01 00 00 00 E9 ?? ?? ?? ?? 8D 64 24 FC 8D
walkthrough_text = rb'\xBF\x01\x00\x00\x00\xE9....\x8D\x64\x24\xFC\x8D'

# function that is triggered when a cutscene is about to occur.
# 89 81 44 04 00 00 8B
cutscene_start = rb'\x89\x81\x44\x04\x00\x00\x8B'

#############################################
# DQX functions / addresses that will likely
# change after each patch.
#############################################
# Main walkthrough text that loads on login. I can't figure out what function loads this on login,
# so scanning for this for now. AC is also preventing this from just being accessible via hooks.
# A0 ?? ?? ?? 00 00 00 00 04 02 00 00 10 00 00 00 E?
walkthrough_pattern = rb'\xA0...\x00\x00\x00\x00\x04\x02\x00\x00\x10\x00\x00\x00[\xE3\xE4\xE5\xE6\xE7\xE8\xE9]'

# Byte at this address changes for loading screens only. Not able to determine if you're in a cutscene.
# You can figure out how to get *back* to this dynamic address by BP'ing at this AOB: 
#      88 08 E9 ?? ?? ?? ?? E9 ?? ?? ?? ?? 68 ?? ?? ?? ?? C3 CC E9 ?? ?? ?? ?? 8D 8F F8 03 00 00 E9 ?? ?? ?? ?? CC
# Read what's in [eax] and do a pointer scan against that address to get these values.
loading_pointer = 0x01EEE4F4
loading_offsets = [0x34, 0x158, 0x24, 0x68, 0x52C]

# The pattern shouldn't have to be adjusted, but the number of addresses to go backwards
# to see if a cutscene is active will probably need to change.
# x00 means no cutscene is active. anything else means it is active
# 6F 72 69 67 69 6E 00 00 00 00 00 00 00 00 00 00 6E 61 6D 65
cutscene_pattern = rb'\x6F\x72\x69\x67\x69\x6E\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x6E\x61\x6D\x65'

# pattern for npc/monsters to rename.
# Every byte marked below will change. The rest stay the same.
# monster: 8C 75 ?? ?? ?? ?? ?? ?? C8 75 ?? ?? E?
# npc:     90 87 ?? ?? ?? ?? ?? ?? C8 75 ?? ?? E?
npc_monster_byte_pattern = rb'[\x9C\x34][\x82\x94]......\x04\x9B..[\xE3\xE4\xE5\xE6\xE7\xE8\xE9]'
#                                ^ monster ^
#                                    ^   npc   ^

# pattern for player names to rename.
# 00 00 00 00 00 48 ?? ?? 01 ?? ?? ?? ?? ?? ?? ?? 01 E?
player_name_byte_pattern = rb'\x00\x00\x00\x00\x00\x58..\x01.......\x01[\xE3\xE4\xE5\xE6\xE7\xE8\xE9]'
#                                                   ^  only this byte changes

########################################
# DQX patterns of interest
########################################
index_pattern = b'\x49\x4E\x44\x58\x10\x00\x00\x00'   # INDX block start
text_pattern = b'\x54\x45\x58\x54\x10\x00\x00'        # TEXT block start
foot_pattern = b'\x46\x4F\x4F\x54\x10\x00\x00'        # FOOT block start
