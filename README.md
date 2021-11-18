# dqxclarity <a href="http://weblate.ethene.wiki/engage/dragon-quest-x/">
<img src="http://weblate.ethene.wiki/widgets/dragon-quest-x/en/svg-badge.svg" alt="Translation status" />
</a>

[Discord](https://discord.gg/M8cBZPUN7p)

Toolkit for translating various elements of the popular game "Dragon Quest X".

![#f03c15](https://via.placeholder.com/15/f03c15/000000?text=+)
**NOTE: I forfeit any responsibility if you receive a warning, a ban or a stern talking to while using this program. `dqxclarity` alters process memory, but only for the intent of allowing English-speaking players to read the game in their language. No malicious activities are being performed with `dqxclarity`. The goal of this application is simply to translate the game for non-Japanese speaking players to enjoy.**

In action:

https://user-images.githubusercontent.com/17505625/120054067-5e995f80-bff3-11eb-9bc6-77595985eb10.mp4

## What does this thing do?

- Translates a majority of the the game UI elements into English (menus, skills/spells, items, etc.) If you see something not translated, our translators are probably working on it
- Replaces NPC names with their Romaji counterpart
- Replaces Monster names with their Romaji counterpart
- Replaces Player names with their Romaji counterpart
- **EXPERIMENTAL**: Uses machine translation to translate game text and writes it back to the in-game window (a work-in-progress to replace `ahkmon`). Enable with the `-c` flag. Read below to see how to turn this flag on.
- Can log in-game dialog to a text file (also needs the `-c` flag enabled)

## Requirements

```diff
- MAKE SURE YOU READ THIS FIRST OR YOU WILL HAVE A BAD TIME.
```

- The below requirements are needed for `dqxclarity` to run. The `dqxclarity.exe` executable will handle the below for you, but if you prefer to do things manually, this is what you need to do.

- [Python 3.9.7 32-bit](https://www.python.org/ftp/python/3.9.7/python-3.9.7.exe) (just click this link to download the exe directly from python's website)
  - _How do I install Python?_ >> Click the link above. During the install, make sure you check "Add Python 3.9 to PATH" at the bottom. If you missed it, simply uninstall and re-install the executable to try again.
  - _Why 32-bit?_ >> The Dragon Quest X client is exclusively in 32-bit and the program needs to match the game's bitness.
  - _Why 3.9.7?_ >> I haven't made the switch to 3.9.10 yet.
  - _Why do I need to install Python?_ >> Maintaining an executable for this program has become too cumbersome with what it's doing, so I'm opting to have you run it the same way I develop it for an easier and more reproducible experience.
  - _But I don't know Python_ >> Zero expertise of Python is required. You simply need to know how to install a program and run a Powershell script.

- Change Powershell's execution policy
  - **Failure to do this will cause `dqxclarity` to open and then close**
  - Microsoft protects you from malicious scripts by revoking your ability to run unsigned Powershell scripts. You're free to do what you want, but if you want to use this program, you will need to allow unrestricted access to this execution policy by doing the following:
    - Search for "Powershell" on your computer. You can find this in the start menu
    - Right-click "Powershell" and click "Run as Administrator"
    - Type the following in the window: `Set-ExecutionPolicy Unrestricted`
    - Accept the changes that you're going to be making by typing 'A'
    - Nothing will return. This change has been saved.
    - Close Powershell as we don't need to run it as an administrator

- Windows 10. A user has reported this working on Windows 11. **This does not work on Windows 7. If you're still using Windows 7, [GO UPGRADE](https://support.microsoft.com/en-us/windows/windows-7-support-ended-on-january-14-2020-b75d4580-2cc7-895a-2c9c-1466d9a53962#:~:text=Microsoft%20made%20a%20commitment%20to,released%20on%20October%2022%2C%202009.).**
```diff
- MAKE SURE YOU READ THIS FIRST OR YOU WILL HAVE A BAD TIME.
```

## How to use

- Read the requirements section above and make sure you've met all the requirements
- Download the latest version of `dqxclarity` from the [releases](https://github.com/jmctune/dqxclarity/releases) section
- Open a fresh instance of Dragon Quest X. It's recommended to stay on the announcements screen when the game first launches.
- Double-click `dqxclarity.exe` to open the wizard. Configure and launch.
- Once installation is complete, the program will run and the game will be translated
- Minimize the window that opened as things will continue translating while you're playing

## EXPERIMENTAL: Enabling in-game dialog translations

```diff
- This is in beta and actively being tested and iterated on. The game might crash, freeze up or just not translate an in-game dialog window. I don't need to hear that it's buggy, crashing or anything of the sort. It does work in its current state, but I'm not comfortable calling it "stable". You have been warned.
```

- Check the "EXPERIMENTAL: Translate dialog?" box in the `dqxclarity.exe` launcher
- Open the translation settings and configure your API service and translation key

## Known bugs

- Running with the `-c` flag is experimental. Crashes may be seen. I'm still iterating on the functionality that this enables. I don't care if you crash while this is enabled as I'm likely already aware of it.
- Talking to the carriage NPCs may cause unknown results. If you talk to one and the game crashes, this is a known bug with the only workaround of not running `dqxclarity` if you want to use them.

### Advanced

`dqxclarity` was written as a command-line tool. There are several items you can toggle on and off using arguments if you please:

```txt
Usage: main.py [OPTIONS]

Options:
  -v, --debug                 Turns on additional logging to console.
  -w, --update-weblate        Grabs the latest files from the weblate branch  
                              and then translates.
  -c, --communication-window  VERY EXPERIMENTAL: Translates the text in the dialog 
                              window using a live translation service like DeepL or
                              Google Translate. Requires a valid account with an API 
                              key to use.
  -p, --player-names          Scans for player names and changes them to their
                              translated counterpart.
  -n, --npc-names             Scans for NPC names and changes them to their   
                              translated counterpart.
  -u, --disable-update-check  Disables checking for updates on each launch.
  -d, --dump-game-data        ADVANCED: Dumps all found game data and converts
                              each file into nested json. Output found in
                              `game_file_dumps` directory. Useful when the
                              game patches.
  -m, --migrate-game-data     ADVANCED: Migrates existing json files into new
                              dumped files. Make sure you dump the game files
                              first with `--dump-game-data`. Output can be
                              found in the `hyde_json_merge/out` directory.
                              You are responsible for reconciling differences.
  --help                      Show this message and exit.
```

## How does this thing work

In the `json\_lang\en` folder are several files with a structure of Japanese and English text. These files were hex dumped from game memory, then converted from hex -> utf-8, then formatted into a nested JSON structure for parsing. The values are then converted back into hex and written back to the same place it was dumped from in memory. Of course direct access to the game files would be preferential, but I lack the skills to reverse the encryption on the dats and haven't come across anyone that can unpack/repack these files.

## How to contribute to the translations

Thanks for considering to contribute. If you choose to, there is tons of work to do. If you can read Japanese, accurate translations are better. No coding experience is required -- you just need to be able to understand a few key rules as seen below.

With the way this script works, exact translations sometimes won't work -- and here's why:

Suppose I have the text "冒険をする". Each Japanese character consists of 3 bytes of text (冒, 険, を, す, る) equaling 15 bytes total. In the English alphabet, each character uses 1 byte of text (O, p, e, n, , A, d, v, e, n, t, u, r, e) equaling 14 bytes total. The number of English bytes cannot exceed the number of Japanese bytes or there will be trouble. When looking to translate, sometimes you may need to think of shorter or similar words to make the text fit.

When translating lines that have line breaks (sentences that may run on to the next line), the Japanese text will have a pipe ("|") character to announce this. If you see a pipe character in the Japanese text, it's guaranteed you are going to want to split up its English equivalent so the text fits. Here's an example:

```
{
    "フレンドや|チームメンバーに|かきおきを書く": "Write a note to|a friend or|team member."
}
```

In-game, "フレンドや", "チームメンバーに", and "かきおきを書く" are read top to bottom. We use the pipe character to tell `dqxclarity` to enter this text on the next line. This is important to understand for your text to look correct in game.

**Make sure you don't exceed the character limit using the system above (usually, you can take the number of Japanese characters and multiply it by 3. Don't exceed this many characters when typing it into English, but you can match it).** Failure to ignore this will cause errors in `dqxclarity` and the file won't translate.

Additionally, there are special tags that start with `clarity_` that should **never** be altered. If you're caught altering these, I may revoke your right to contribute. Leave them alone!

If you would like to contribute, please jump on our Discord (link seen at the top) and let's talk in #translation-coord.

## But what are those `clarity_` lines for?

When the loaded text is dumped from memory, some strings have additional null terminators ('00') or tab characters that are included in the json. As the text has to be put back with the **exact** number of characters, the extra null terminators and tab characters have to be accounted for. These are basically placeholder strings that are handled and converted appropriately when `dqxclarity` is run.

## `dqxclarity` is seen as a virus by Windows. What gives?

`dqxclarity` is scanning and writing process memory, which is similar behavior to what viruses may do, hence the auto flag from Windows. This program is not malicious and the alert can be safely disregarded. I'd suggest [whitelisting](https://support.microsoft.com/en-us/windows/add-an-exclusion-to-windows-security-811816c0-4dfd-af4a-47e4-c301afe13b26) your entire `dqxclarity` folder in this case.

## Contributing to development

This project is structured as a bunch of `.py` files. There's nothing to build other than a cleaner release package with the bulk cut out. If you want to get started:

- Create a virtual environment for yourself inside the `dqxclarity` folder
  - `python3 -m venv venv`
- Run `activate.ps1`
- Install dependencies with `pip install -r requirements.txt`
- Tear it apart

## FAQ

- _I'm running your program and it's instantly closing_
  - Make sure you followed **EVERYTHING** in the "Requirements" section at the top of this page
  - Check the `out.log` and `console.log` file for errors
  - Don't run DQX as admin. This is very unnecessary. This includes DQXGame as well as the launcher and other executables in the DQX folder
  - You can shift + right-click inside of the `dqxclarity` folder (in the empty white space of the folder), select "Open Powershell Window Here", type `.\run_clarity.ps1` and press enter. The program will run and you can see the error output in the console. If you aren't sure what to do from here, join the Discord and ask for help.
- _How do I update dqxclarity?_ >> For now, you will need to download the latest updates from the [releases](https://github.com/jmctune/dqxclarity/releases) page. Make sure you're creating a **new** folder and aren't just copy/pasting over your old installation.
- _I'm getting the error INVALID\_CALL\_1 in cutscenes/loading screens_ >> In the Powershell console, make sure you haven't clicked inside of the window. If you see "Select:" in the title bar of the program, the script is paused. This is a Powershell thing. Simply pressing enter after clicking inside of the Powershell console will resume the script. Though, if you got the error, you will need to relaunch the program anyways. Make sure Powershell doesn't say "Select:" in the title window.
- _What's all this stuff `dqxclarity` is installing on my computer?_ >> These are dependencies that `dqxclarity` need to run. Nothing is actually installed on your computer, but files are downloaded and places in a contained `venv` folder within the `dqxclarity` directory. If you don't want to use `dqxclarity` anymore, simply delete the `dqxclarity` folder and it's gone.
- _I'm running with the -c flag / using the dialog translate feature and `dqxclarity` pauses every time I talk to someone_ >> The `-c` flag is currently an expiremental feature that can still be considered buggy. This is still being iterated on with a group of testers. Don't expect stability if you intend on using this. When you talk to an NPC that needs to be translated, the game pauses for a brief period of time as it must reach out to perform the translation, get the translation back, write it to the game and finally release it back to you. Once the text has been translated once, it reads the text from a local database and the pause should be non-existant.
- _I'm getting the error EXCEPTION\_ACCESS\_VIOLATION from DQX_ >> This is a minor error that can be solved by simply restarting the game and restarting `dqxclarity`. These unfortunately happen as this program is altering live game memory. If it's very consistent, drop by the Discord and post your situation.
- _NPC/Player names take awhile for their name to change_ >> This is expected. There's a background process that is constantly scanning for these names and replacing them with their translated counterparts. Just keep the program running and `dqxclarity` will take care of the rest.
- _Why isn't the login screen translated?_ >> The v6 patch changed the way this screen functions. It's now cached, so if you're on this screen when you run `dqxclarity`, you will need to navigate away from the screen and come back to it. Or, just run `dqxclarity` on the announcement screen when you first launch the screen like I told you to above.