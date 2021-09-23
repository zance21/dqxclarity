'''
Python program used to translate various game UI elements for the game "Dragon Quest X".
'''

from multiprocessing import Process, freeze_support
import sys
import click
import pymem
from clarity import (scan_for_player_names, translate, get_latest_from_weblate,
    scan_for_ad_hoc_game_files, dump_all_game_files, scan_for_player_names,
    migrate_translated_json_data, scan_for_npc_names,
    check_for_updates)
from dialog import scan_for_dialog

@click.command()
@click.option('-v', '--debug', is_flag=True,
                help='''Turns on additional logging to console.''')
@click.option('-w', '--update-weblate', is_flag=True,
                help='''Grabs the latest files from the weblate branch and then translates.''')
@click.option('-c', '--communication-window', is_flag=True,
                help='''Translates the text in the dialog window using a live
                        translation service like DeepL or Google Translate.
                        Requires a valid account with an API key to use.''')
@click.option('-n', '--names', is_flag=True,
                help='''Scans for player names and changes them to their translated counterpart.
                        Names can be configured in the json/player_names.json file.''')
@click.option('-u', '--disable-update-check', is_flag=True,
                help='''Disables checking for updates on each launch.''')
@click.option('-d', '--dump-game-data', is_flag=True,
                help='''ADVANCED: Dumps all found game data and converts each file into nested json.
                        Output found in `game_file_dumps` directory. Useful when the game patches.''')
@click.option('-m', '--migrate-game-data', is_flag=True,
                help='''ADVANCED: Migrates existing json files into new dumped files.
                        Make sure you dump the game files first with `--dump-game-data`.
                        Output can be found in the `hyde_json_merge/out` directory.
                        You are responsible for reconciling differences.''')

def blast_off(update_weblate=False, dump_game_data=False,
                migrate_game_data=False, disable_update_check=False, 
                communication_window=False, names=False, debug=False):
    if dump_game_data:
        dump_all_game_files()
        sys.exit('Finished!')
    if migrate_game_data:
        migrate_translated_json_data()
        sys.exit('Migrated!')
    if update_weblate:
        click.secho('Getting latest files...', fg='green')
        get_latest_from_weblate()
    if not disable_update_check:
        check_for_updates()
    if debug:
        debug = True

    translate()

    try:
        if communication_window:
            Process(name='Dialog scanner', target=scan_for_dialog, args=(debug,)).start()
        # if names:
        #     Process(name='Player name scanner', target=scan_for_player_names, args=(debug,)).start()
        #Process(name='NPC scanner', target=scan_for_npc_names, args=(debug,)).start()
        Process(name='Adhoc scanner', target=scan_for_ad_hoc_game_files, args=(debug,)).start()

    except pymem.exception.WinAPIError:
        sys.exit(click.secho('Can\'t find DQX process. Exiting.', fg='red'))

if __name__ == '__main__':
    freeze_support()    # Needed for multiprocessing support with PyInstaller
    blast_off()
