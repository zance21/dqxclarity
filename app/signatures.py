'''
Signatures / addresses to known functions.
'''
########################################
# Python functions
########################################
# WHEN WILL THIS CHANGE?
# Never, unless the Python dll version gets updated.
# 55 8B EC 6A 00 FF 75 08 E8 43 CC FF FF 83 C4 08 5D
pyrun_simplestring = rb'\x55\x8B\xEC\x6A\x00\xFF\x75\x08\xE8\x43\xCC\xFF\xFF\x83\xC4\x08\x5D'

# WHEN WILL THIS CHANGE?
# Never, unless the Python dll version gets updated.
# 55 8B EC 83 E4 F8 81 EC 10 01 00 00
py_initialize_ex = rb'\x55\x8B\xEC\x83\xE4\xF8\x81\xEC\x10\x01\x00\x00'

########################################
# DQX functions
########################################
# takes you to the section of the function where you can read where dialog is stored before
# it's read. captures npc text as well as adhoc files loaded into memory.
# WHEN WILL THIS CHANGE?
# Hopefully never. This is a core game function.
# 8D 4F 04 56 89 02 E8 ? ? ? ? 8B
dialog_trigger = rb'\x8D\x4F\x04\x56\x89\x02\xE8....\x8B'

# takes you to the section of the function where cutscene text is read from. this just shows
# you immediately what's at the bottom of the screen before it's actually visible so it can be
# translated.
# WHEN WILL THIS CHANGE?
# Hopefully never. This is a core game function.
# 8B 45 18 8B CF 50 89 87 ? ? ? ? E8
cutscene_trigger = rb'\x8B\x45\x18\x8B\xCF\x50\x89\x87....\xE8'

# reading at this address will show you the adhoc file that's currently being read from. we use this
# to dump the adhoc file if we don't have it.
# WHEN WILL THIS CHANGE?
# Hopefully never. This is a core game function.
# 2B CF 8B C6 41 89 0A 5F 5E 5D
cutscene_adhoc_files = rb'\x2B\xCF\x8B\xC6\x41\x89\x0A\x5F\x5E\x5D'

########################################
# DQX addresses of interest
########################################
# WHEN WILL THIS CHANGE?
# On patches. A new pointer will need to be found.
# Captured in CE by going in and out of loading screens.
# Loading screens to check:
#  - In and out of zones
#  - In and out of cutscenes
#  - In and out of teleport orbs in town
# 0 should be active loading screen, 1 should be inactive loading screen

# WHEN WILL THIS CHANGE?
# asdsad
loading_screen_active = 0x01F15468  # DQXGame.exe+01F15468
loading_screen_offsets = [0x18, 0x20]

# WHEN WILL THIS CHANGE?
# On patches. The pattern shouldn't have to be adjusted, but the number of addresses to go backwards
# to see if a cutscene is active will probably need to change.
# x00x00x00x00 means no cutscene is active. anything else means it is active
# 6F 72 69 67 69 6E 00 00 00 00 00 00 00 00 00 00 6E 61 6D 65
cutscene_pattern = rb'\x6F\x72\x69\x67\x69\x6E\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x6E\x61\x6D\x65'

########################################
# DQX patterns of interest
########################################
index_pattern = b'\x49\x4E\x44\x58\x10\x00\x00\x00'   # INDX block start
text_pattern = b'\x54\x45\x58\x54\x10\x00\x00'        # TEXT block start
foot_pattern = b'\x46\x4F\x4F\x54\x10\x00\x00'        # FOOT block start
