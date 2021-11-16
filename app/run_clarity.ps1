$ClarityFlags = "-wpn"

function LogWrite($string) {
   Write-Host $string -ForegroundColor "Yellow"
   $TimeStamp = (Get-Date -Format yyyy-MM-dd) + " " + (Get-Date -Format HH:MM:ss) 
   $TimeStamp + " " + $string | Out-File -Filepath "out.log" -Append -Force -Encoding utf8
}

$PythonRegKey = "Registry::HKEY_CURRENT_USER\SOFTWARE\Python\PythonCore\3.9-32\InstallPath"
$PythonInstallPath = (Get-ItemProperty -Path $PythonRegKey -Name "(default)")."(default)"

if (!$PythonInstallPath) {
    LogWrite "Could not find Python installation for Python 3.9-32. Exiting."
    Exit
}

try {
    $CheckIfPythonOnPath = &{python -V}
} catch {
    LogWrite "Python found, but unable to execute from PATH. When installing Python, make sure you check 'Add Python 3.9 to PATH' before continuing through the install. Exiting."
    Exit
}

if (Test-Path -Path "venv") {
    LogWrite "Virtual environment exists. Activating."
    & .\venv\Scripts\activate
} else {
    LogWrite "Creating virtual environment (venv)."
    $PythonExe = "$PythonInstallPath" + "python.exe"
    & $PythonExe -m venv venv
    LogWrite "Activating virtual environment."
    & .\venv\Scripts\activate

    $AreWeInAVirtualEnvironment = & .\venv\Scripts\python.exe -c "import sys; print('False') if sys.prefix == sys.base_prefix else print('True')"

    if ("$AreWeInAVirtualEnvironment" -eq "False") {
        LogWrite "Failed to activate virtual environment. Try deleting the 'venv' folder and running this again. Exiting."
        Exit
    }

    if (Test-Path -Path "requirements.txt") {
        LogWrite "Installing requirements."
        & .\venv\Scripts\pip.exe install -r requirements.txt
    }
}

LogWrite "Running clarity."
& .\venv\Scripts\python.exe main.py $ClarityFlags
