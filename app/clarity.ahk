#Persistent
#NoEnv
#SingleInstance force
SendMode Input

;=== Load Start GUI settings from file ======================================
IniRead, updateweblate, user_settings.ini, flags, updateweblate, 1
IniRead, translateplayernames, user_settings.ini, flags, translateplayernames, 1
IniRead, translatenpcnames, user_settings.ini, flags, translatenpcnames, 1
IniRead, translatedialog, user_settings.ini, flags, translatedialog, 0
IniRead, debug, user_settings.ini, flags, debug, 0

IniRead, enabledeepltranslate, user_settings.ini, config_translation, enabledeepltranslate, 0
IniRead, enabledeeplproapis, user_settings.ini, config_translation, enabledeeplproapis, 0
IniRead, deepltranslatekey, user_settings.ini, config_translation, deepltranslatekey, EMPTY
IniRead, enablegoogletranslate, user_settings.ini, config_translation, enablegoogletranslate, 0
IniRead, googletranslatekey, user_settings.ini, config_translation, googletranslatekey, EMPTY
IniRead, regioncode, user_settings.ini, config_translation, regioncode, EN

IniRead, enabledialoglogging, user_settings.ini, behavior_config, enabledialoglogging, 0

;=== Create Start GUI =====================================================
Gui, 1:Font, s10, Segoe UI
Gui, 1:Add, Link,, <a href="https://github.com/jmctune/dqxclarity/blob/main/README.md">Not sure what to do? Read the README!</a>
Gui, 1:Add, Checkbox, vupdateweblate Checked%updateweblate%, Pull latest files from weblate?
Gui, 1:Add, Checkbox, vtranslateplayernames Checked%translateplayernames%, Translate player names?
Gui, 1:Add, Checkbox, vtranslatenpcnames Checked%translatenpcnames%, Translate NPC names?
Gui, 1:Add, Checkbox, vdebug Checked%debug%, Enable debug logs?
Gui, 1:Add, Checkbox, vtranslatedialog Checked%translatedialog%, EXPERIMENTAL: Translate dialog?
Gui, 1:Add, Button, gOpenTranslationSettings w+300, Open Translation Settings
Gui, 1:Add, CheckBox, venabledialoglogging Checked%enabledialoglogging%, (Requires Translate Dialog) Log game text to file?
Gui, 1:Add, Button, gSave w+300 h+50, Run dqxclarity

;=== Open Translation Settings ============================================
Gui, 2:Font, s10, Segoe UI
Gui, 2:Add, Text, cRed, Configure one or the other - not both!
Gui, 2:Add, Text,, DeepL Configuration:
Gui, 2:Add, CheckBox, venabledeepltranslate Checked%enabledeepltranslate%, Use DeepL Translate
Gui, 2:Add, CheckBox, venabledeeplproapis Checked%enabledeeplproapis%, Use DeepL Pro APIs
Gui, 2:Add, Text,, DeepL API Key:
Gui, 2:Add, Edit, r1 vdeepltranslatekey w+300, %deepltranslatekey%
Gui, 2:Add, Text,, Google Translate Configuration:
Gui, 2:Add, CheckBox, venablegoogletranslate Checked%enablegoogletranslate%, Use Google Translate
Gui, 2:Add, Text,, Google Translate API Key:
Gui, 2:Add, Edit, r1 vgoogletranslatekey w+300, %googletranslatekey%
Gui, 2:Add, Button, gCloseTranslationSettings w+300 h+50, Close Translation Settings

;=== Misc Start GUI =======================================================
Gui, 1:Show, Autosize
Return

OpenTranslationSettings:
  Gui, 2:Show, Autosize
  Return

;=== Save Start GUI settings to ini ==========================================
CloseTranslationSettings:
  Gui, 2:Submit
  Return

Save:
  Gui, 1:Submit
  IniWrite, %updateweblate%, user_settings.ini, flags, updateweblate
  IniWrite, %translateplayernames%, user_settings.ini, flags, translateplayernames
  IniWrite, %translatenpcnames%, user_settings.ini, flags, translatenpcnames
  IniWrite, %translatedialog%, user_settings.ini, flags, translatedialog
  IniWrite, %debug%, user_settings.ini, flags, debug
  IniWrite, %enabledialoglogging%, user_settings.ini, behavior_config, enabledialoglogging

  IniWrite, %enabledeepltranslate%, user_settings.ini, config_translation, enabledeepltranslate
  IniWrite, %enabledeeplproapis%, user_settings.ini, config_translation, enabledeeplproapis
  IniWrite, %deepltranslatekey%, user_settings.ini, config_translation, deepltranslatekey
  IniWrite, %enablegoogletranslate%, user_settings.ini, config_translation, enablegoogletranslate
  IniWrite, %googletranslatekey%, user_settings.ini, config_translation, googletranslatekey

  IniWrite, EN, user_settings.ini, config_translation, regioncode

  ; These exist because Python uses True/False, not 0/1, so we make a new config block for clarity
  if (enabledeepltranslate = 1)
    IniWrite, True, user_settings.ini, translation, enabledeepltranslate
  else
    IniWrite, False, user_settings.ini, translation, enabledeepltranslate

  if (enabledeeplproapis = 1)
    IniWrite, True, user_settings.ini, translation, enabledeeplproapis
  else
    IniWrite, False, user_settings.ini, translation, enabledeeplproapis

  if (enablegoogletranslate = 1)
    IniWrite, True, user_settings.ini, translation, enablegoogletranslate
  else
    IniWrite, False, user_settings.ini, translation, enablegoogletranslate
  if (enabledialoglogging = 1)
    IniWrite, True, user_settings.ini, behavior, enabledialoglogging
  else
    IniWrite, False, user_settings.ini, behavior, enabledialoglogging
  if (debug = 1)
    IniWrite, True, user_settings.ini, behavior, debug
  else
    IniWrite, False, user_settings.ini, behavior, debug

  IniWrite, %deepltranslatekey%, user_settings.ini, translation, deepltranslatekey
  IniWrite, %googletranslatekey%, user_settings.ini, translation, googletranslatekey
  IniWrite, EN, user_settings.ini, translation, regioncode

flags := ""

if (translateplayernames = 1)
  flags .= "p"

if (translatenpcnames = 1)
  flags .= "n"

if (updateweblate = 1)
  flags .= "w"

if (translatedialog = 1)
  flags .= "c"

if (debug = 1)
  flags .= "v"

if (flags != "")
  c_flags := "$ClarityFlags = " . """" . "-" .  flags . """"
else
  c_flags := "$ClarityFlags = " . """" . """"

FileRead, fileChanges, run_clarity.ps1
UpdatedFile := RegExReplace(fileChanges, "^\$ClarityFlags = ""(.*?)""", c_flags)
FileDelete, run_clarity.ps1
FileAppend, %UpdatedFile%, run_clarity.ps1, UTF-8

Run, powershell.exe -ep Unrestricted -File .\run_clarity.ps1

ExitApp
