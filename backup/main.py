"""
Python program used to translate various game UI elements for the game "Dragon Quest X".
"""

from multiprocessing import Process
import sys
import time
import click
from loguru import logger
from pymem.exception import WinAPIError
from clarity import (
    translate,
    get_latest_from_weblate,
    scan_for_player_names,
    scan_for_npc_names,
    check_for_updates,
    scan_for_adhoc_files,
    scan_for_walkthrough,
)
from hook import activate_hooks


@click.command()
@click.option(
    "-v", "--debug", is_flag=True, help="""Turns on additional logging to console."""
)
@click.option(
    "-w",
    "--update-weblate",
    is_flag=True,
    help="""Grabs the latest files from the weblate branch and then translates.""",
)
@click.option(
    "-c",
    "--communication-window",
    is_flag=True,
    help="""THIS IS EXPERIMENTAL. DO NOT REPORT BUGS. I PROBABLY ALREADY KNOW.
                        Translates the text in the dialog window using a live
                        translation service like DeepL or Google Translate.
                        Requires a valid account with an API key to use.""",
)
@click.option(
    "-p",
    "--player-names",
    is_flag=True,
    help="""Scans for player names and changes them to their translated counterpart.""",
)
@click.option(
    "-n",
    "--npc-names",
    is_flag=True,
    help="""Scans for NPC names and changes them to their translated counterpart.""",
)
@click.option(
    "-u",
    "--disable-update-check",
    is_flag=True,
    help="""Disables checking for updates on each launch.""",
)
def blast_off(
    update_weblate=False,
    disable_update_check=False,
    communication_window=False,
    player_names=False,
    npc_names=False,
    debug=False,
):
    logger.warning("Getting started. DO NOT TOUCH THE GAME OR REMOVE YOUR MEMORY CARD.")
    if update_weblate:
        click.secho("Getting latest files...", fg="green")
        get_latest_from_weblate()
    if not disable_update_check:
        check_for_updates()
    if not debug:
        logger.remove()
        logger.add(sys.stderr, level="INFO")

    translate()

    try:
        if communication_window:
            Process(name="Hook loader", target=activate_hooks, args=(debug,)).start()
            Process(
                name="Walkthrough scanner", target=scan_for_walkthrough, args=()
            ).start()
        if player_names:
            Process(
                name="Player name scanner", target=scan_for_player_names, args=()
            ).start()
        if npc_names:
            Process(name="NPC scanner", target=scan_for_npc_names, args=()).start()
        Process(name="Adhoc scanner", target=scan_for_adhoc_files, args=()).start()
    except WinAPIError:
        sys.exit(click.secho("Can't find DQX process. Exiting.", fg="red"))

    time.sleep(2)
    logger.info(
        "Done! Keep this window open (minimize it) and have fun on your adventure!"
    )


if __name__ == "__main__":
    blast_off()
