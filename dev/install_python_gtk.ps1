<#
 #
 # Run as post-install script for .exe package
 #
 #  - downloads Python + Gtk
 #  - some Python libraries
 #  - and runs their respective installers
 #  - crafts Streamtuner2 desktop shortcut
 #  - crafts Streamtuner2 shortcuts in Start menu
 #
 #>


#-- defaults / parameters
[CmdletBinding()]            
Param(
  [string]$reinstall = "ask",
  [string]$TEMP = $env:TEMP,
  [string]$PYTHON = "C:\Python27",
  [string]$StartMenu = "$env:USERPROFILE\AppData\Roaming\Microsoft\Windows\Start Menu\Programs",
 #[string]$UsrFolder = $MyInvocation.MyCommand.Path -replace ("([\\/][^\\/]+){4}$",""),
  [string]$ProgramFiles = "%ProgramFiles(x86)%",
  [string]$AboutLink = "http://freshcode.club/projects/streamtuner2",
  [string]$VERSION = "2.2.0"
)            

#-- paths
$UsrFolder = $MyInvocation.MyCommand.Path -replace ("([\\/][^\\/]+){4}$","")
$UninstallPath = "$UsrFolder\share\streamtuner2\dev\uninstall.cmd"
$ResetPrefsPath = $UninstallPath -replace ("uninstall", "resetprefs")
$ModifyPath = $MyInvocation.MyCommand.Path -replace ("[.]ps1$", ".bat")
$IconPath = "$UsrFolder\share\pixmaps\streamtuner2.ico"

#-- system configuration
$ErrorActionPreference = "SilentlyContinue"  # ignore all path/registry lookup errors
$OutputEncoding = [System.Text.Encoding]::UTF8
$regPathCU = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall"
$regPathLM = "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall" #64-Bit machine
if(!(Test-Path $regPathLM)) {                                                        #32-Bit machine
    $regPathLM = "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall"
    $ProgramFiles = "%ProgramFiles%"
}
New-Variable -Name STREAMRIPPER -Option AllScope -Value "$ProgramFiles\Streamripper" #can be changed in Check-Prerequisites

#-- what and how to install (hash list as used by Run-Task and Check-Prerequisites)
$tasks = @(
  @{
    title  = "Python 2.7.12"
    url    = "https://www.python.org/ftp/python/2.7.12/python-2.7.12.msi"
    cmd    = ""
    iargs   = 'TARGETDIR="{PYTHON}" /qb-!'
    regkey = "$regPathLM\{9DA28CE5-0AA5-429E-86D8-686ED898C665}"
    testpth= "{PYTHON}\pythonw.exe"
    is_opt = ''
    prescn = ''
  },
  @{
    title  = "PyGtk 2.24.2"
    url    = "http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/pygtk-all-in-one-2.24.2.win32-py2.7.msi"
    cmd    = ""
    iargs   = 'TARGETDIR="{PYTHON}" ADDLOCAL=ALL REMOVE=PythonExtensionModulePyGtkSourceview2,PythonExtensionModulePyGoocanvas,PythonExtensionModulePyRsvg,DevelopmentTools /qb-!'
    regkey = "$regPathLM\{09F82967-D26B-48AC-830E-33191EC177C8}"
    testpth= "{PYTHON}\Lib\site-packages\gtk-2.0\pygtk-2.24.0-py2.7.egg-info"
  },
  @{
    title  = "Python requests"
    url    = "requests" # no download url, pip handles this
    cmd    = "easy_install"
    testpth= "{PYTHON}\Lib\site-packages\requests-2*py2.7.egg"
  },
  @{
    title  = "LXML 2.3"
    url    = "https://pypi.python.org/packages/d4/fa/e4e0c7a8fe971b10e275cdc20efd16f553a225e700c400c11da25276e4f4/lxml-2.3-py2.7-win32.egg"
    cmd    = "easy_install"
    testpth= "{PYTHON}\Lib\site-packages\lxml-2.3-py2.7-win32.egg"
  },
  @{
    title  = "PyQuery 1.2.1"
    url    = "https://pypi.python.org/packages/62/71/8ac1f5c0251e51714d20e4b102710d5eee1683c916616129552b0a025ba5/pyquery-1.2.17-py2.py3-none-any.whl"
    cmd    = "pip"
    iargs   = "--disable-pip-version-check"
    testpth= "{PYTHON}\Lib\site-packages\pyquery-1.2.17.dist-info"
  },
  @{
    title  = "PIL 1.1.7"
    url    = "http://effbot.org/downloads/PIL-1.1.7.win32-py2.7.exe"
    regkey = "$regPathCU\PIL-py2.7"
    testpth= "{PYTHON}\Lib\site-packages\PIL"
  },
  @{
    title  = "Streamripper 1.64.6"
    url    = "https://netcologne.dl.sourceforge.net/project/streamripper/streamripper%20%28current%29/1.64.6/streamripper-windows-installer-1.64.6.exe"
    cmd    = ""
    iargs   = "/S  /D={STREAMRIPPER}"  #NSIS does not use double quotes in /D parm
    regkey = "$regPathLM\Streamripper"
    testpth= "{STREAMRIPPER}\streamripper.exe"
    is_opt = '($optionalInstall)'     # ← could use '((Ask "Install streamripper too [y/N]") -match N)' instead
    prescn = 'if ($optionalInstall) {if ($_found = (Get-ITPV "Streamripper")) {$STREAMRIPPER = $_found}} else {$STREAMRIPPER=""; continue;}'
  },
  @{
    title  = "Uninstall script"
    cmd    = 'Create-Uninstallscript'
  },
  @{
    title  = "Desktop shortcut"
    cmd    = 'Make-Shortcut -dir $Home\Desktop -name Streamtuner2.lnk -target $PYTHON\pythonw.exe -arg $UsrFolder\bin\streamtuner2'
  },
  @{
    title  = "Startmenu shortcut"
    cmd    = 'Make-Shortcut -dir "$StartMenu\Streamtuner2" -name Streamtuner2.lnk -target $PYTHON\pythonw.exe -arg $UsrFolder\bin\streamtuner2'
  },
  @{
    title  = "Startmenu help.chm"
    cmd    = 'Make-Shortcut -dir "$StartMenu\Streamtuner2" -name Help.lnk -target $UsrFolder\share\streamtuner2\help\help.chm'
  },
  @{
    title  = "Startmenu uninstall"
    cmd    = 'Make-Shortcut -dir "$StartMenu\Streamtuner2" -name Uninstall.lnk -target $UninstallPath'
  },
  @{
    title  = "Startmenu Internet"
    cmd    = 'Make-Shortcut -dir "$StartMenu\Streamtuner2" -name "Streamtuner2 on the Web.lnk" -target "$AboutLink"'
  },
  @{
    title  = "Startmenu Reconfigure"
    cmd    = 'Make-Shortcut -dir "$StartMenu\Streamtuner2\Extra" -name "Reconfigure.lnk" -target $ModifyPath'
  },
  @{
    title  = "Startmenu RunDebug"
    cmd    = 'Make-Shortcut -dir "$StartMenu\Streamtuner2\Extra" -name "Run in debug mode (-D).lnk" -target $PYTHON\python.exe -arg "$UsrFolder\bin\streamtuner2" -parm "-D"'
  },
  @{
    title  = "Startmenu RunConsole"
    cmd    = 'Make-Shortcut -dir "$StartMenu\Streamtuner2\Extra" -name "Run with console.lnk" -target $PYTHON\python.exe -arg "$UsrFolder\bin\streamtuner2"'
  },
  @{
    title  = "Startmenu ResetPrefs"
    cmd    = 'Make-Shortcut @task'
       dir = "$StartMenu\Streamtuner2\Extra"
      name = "Reset preferences.lnk"
    target = "$ResetPrefsPath"
  },
  @{
    title  = "FINISHED"
  }
)



#-- startup messages
function Display-Logo {
    Write-Host -b DarkBlue @"
 _____________________________________________________________________________ 
|                                                                             |
|       _____/\\\\\\\\\\\____/\\\\\\\\\\\\\\\____/\\\\\\\\\_____              |
|        ___/\\\/////////\\\_\///////\\\/////___/\\\///////\\\___             |
|         __\//\\\______\///________\/\\\_______\///______\//\\\__            |
|          ___\////\\\_______________\/\\\_________________/\\\/___           |
|           ______\////\\\____________\/\\\______________/\\\//_____          |
|            _________\////\\\_________\/\\\___________/\\\//________         |
|             __/\\\______\//\\\________\/\\\_________/\\\/___________        |
|              _\///\\\\\\\\\\\/_________\/\\\________/\\\\\\\\\\\\\\\_       |
|               ___\///////////___________\///________\///////////////__      |
|                                                                             |
|                                                                             |
|    Streamtuner2 for Windows                               Version $VERSION     |
|                                                                             |
|    Installer for Python 2.7.12 & Gtk 2.24.2                                 |
 ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––– 
"@
}
function Ask-First {
    Write-Host ""
    if ((Ask "Do you want install Streamtuner2 and its Python dependencies now? [Y/n] ") -notmatch "^[yY]|^$") {
        #$tasks = $tasks[7..($tasks.length-1)]; return 0,0
        exit
    }
    $reuseCachedFiles = (Ask "Reuse any cached setup files or ignore them? [r/I] ") -match "^[Rr]"
    $optionalInstall =  (Ask "Install optional components? [y/N] ") -match "^[Yy]"
    Write-Host ""
    return $reuseCachedFiles, $optionalInstall
}

function Console-MaxHeight {
    if ($Host.Name -match "console") {
        $MaxHeight = $host.UI.RawUI.MaxPhysicalWindowSize.Height
        $MaxWidth = $host.UI.RawUI.MaxPhysicalWindowSize.Width
        $MyBuffer = $Host.UI.RawUI.BufferSize
        $MyWindow = $Host.UI.RawUI.WindowSize
        $MyWindow.Height = ($MaxHeight)
        $MyWindow.Width = (80)
        $MyBuffer.Height = (9999)
        #$MyBuffer.Width = (80)
        $host.UI.RawUI.set_bufferSize($MyBuffer)
        $host.UI.RawUI.set_windowSize($MyWindow)
    }
}

#-- create Desktop/Startmenu shortcuts
function Make-Shortcut {
    param($dir, $name, $target, $arg=$false, $parm=$false)
    if (!(Test-Path -Path $dir)) {
        New-Item -Path $dir -ItemType directory > $null
    }
    $wsh = New-Object -ComObject WScript.Shell
    if (!$wsh) { return }
    $lnk = $wsh.CreateShortcut("$dir\$name")
    $lnk.TargetPath = $target
    if ($arg) {
        ($lnk.Arguments =  '"'+$arg+'"') | %{if ($parm) {$lnk.Arguments += " $parm"}}
        $lnk.IconLocation = "$IconPath"
        $lnk.WorkingDirectory = "$UsrFolder\bin"
    }
    $lnk.Save()
}

#-- create uninstall script and registry key
function Create-Uninstallscript {
    [CmdletBinding()]
    param()
    # update uninstall.cmd with current values
    $installFolder = $usrFolder.substring(0,$usrFolder.LastIndexOf('\'))
    $UninstallScript = Get-Content -Path $UninstallPath
    Out-File -FilePath $UninstallPath -Encoding ascii -InputObject @"
@set installFolder=$installFolder
@set usrFolder=$usrFolder
@set Python=$PYTHON
@set StreamripperFolder=$STREAMRIPPER
"@
    $UninstallScript | %{if ($_ -notmatch "@set") {Out-File -FilePath $UninstallPath -Encoding ascii -Append -InputObject $_}} 
    # registry entry for ST2
    Remove-Item -Path $regPathCU\Streamtuner2 2> $null        
    New-Item $regPathCU -Name "Streamtuner2" > $null
    Set-Location -Path $regPathCU\Streamtuner2
    @(
        @("DisplayName",     "String",  "Streamtuner2"),
        @("DisplayVersion",  "String",  "$VERSION"),
        @("DisplayIcon",     "String",  "$IconPath"),
        @("UninstallString", "String",  "$UninstallPath"),
        @("URLInfoAbout",    "String",  "$AboutLink"),
        @("Publisher",       "String",  "Mario Salzer"),
        @("NoModify",        "DWord",   0x00000000),
        @("ModifyPath",      "String",  "$ModifyPath"),
        @("NoRepair",        "DWord",   0x00000001),
        @("HelpLink",        "String",  "http://fossil.include-once.org/streamtuner2/wiki/windows")
    ) | % {
        New-ItemProperty -Path . -Name $_[0] -PropertyType $_[1] -Value $_[2] > $null
    }
}

#-- wait for keypress
function Any-Key($color) {
    Write-Host -f $color "[Press any key]"
    $null = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

#-- colorized Read-Host
function Ask($str) {
    if ($str -cmatch "^(.+?)(\[[a-z/]*)([A-Z]+)([\w/]*\])(.*)$") {
        Write-Host -n -f Yellow     $matches[1] # Want to install
        Write-Host -n -f Gray       $matches[2] # [n/
        Write-Host -n -f Green      $matches[3] # Y
        Write-Host -n -f Gray       $matches[4] # /a]
        Write-Host -n -f Yellow     $matches[5] # ?
    }
    else {
        Write-Host -n -f Yellow $str
    }
    Read-Host ; Write-Host ""
}

#-- ensure ST2 startup script exists in relative path to this install script
function Check-Package {
    if (!(Test-Path -Path("$UsrFolder\bin\streamtuner2"))) {
        Write-Host -b DarkRed -f White "`nThe bin\streamtuner2 start script could not be found.`nThe installation cannot continue.`nDo not change the folder structure of the Streamtuner2 package!`nIf you want to run the install_python_gtk.ps1 script post-install,`nplease use the -UsrFolder parameter.`n"
        Any-Key Red ; exit
    }
}

#-- shortcut Get-ItemPropertyValue over multiple registry hives
function Get-ITPV($regpath, $value="(default)") {
    @('HKLM:\Software\WOW6432Node', 'HKLM:\Software', 'HKCU:\Software') | % { 
        if (($val = (Get-ItemProperty -path "$_\$regpath" 2>$null).$value) -AND (Test-Path $val)) { return $val }
    }
}

#-- Check if previous Python 2.7 installation exists
function Check-PythonInstall {
    $PythonInstalledPath = Get-ITPV('Python\PythonCore\2.7\InstallPath\')
    
    #-- if Python 2.7.12 installed, reuse installation folder
    if (Get-Item -path "$regPathLM\{9DA28CE5-0AA5-429E-86D8-686ED898C665}" 2> $null ) {
        $PYTHON = $pythonInstalledPath -replace "\\$", ""
    }

    #-- older 2.7 version found
    else {
        if ($PythonInstalledPath) {
            Write-Host ""
            Write-Host -b Red -f White @"
Setup has detected an older version of Python 2.7 
in $PythonInstalledPath.

It is strongly recommended to exit this setup now and uninstall 
the previous Python version before installing Streamtuner2.

Continuing this setup might result in loss of functionality 
for other Python applications on your computer!
"@
            Write-Host ""
            if ((Ask "Do you want to continue with the setup anyway? [y/N]") -notmatch "[yY]") {
                exit;
            }
        }
    }
    return $PYTHON
}

#-- check prereqs installation
function Check-Prerequisites {
    [CmdletBinding()]
    param($result = 1)
    ForEach ($t in $tasks) {
        $t.found = 0
        $t.testpth = $t.testpth -replace "{PYTHON}","$PYTHON"
        if (!$t.regkey -and !$t.testpth) {
            continue
        }
        if ($t.prescn) {  # expression for e.g. registry → path lookup
            Invoke-Expression $t.prescn  # should set $_found + global $PLACEHOLDER variable
        }
        elseif ($t.testpth) {
            if (Test-Path $t.testpth) {
                $t.found = $t.testpth
            }
            elseif ($t.regkey -and (Test-Path $t.regkey)) {
                $t.found = "installer/registry"
            }
        }
        if (!$t.found) {
            Write-Host "   - $($t.title) not found"
            $result = 0;
        }
        else {
            Write-Host -n "   + $($t.title) found "  # and display shortened path:
            Write-Host -f DarkGray "($($t.found -replace '(?<!^.{1,4})(\\[^\\]+(?=\\)){2,5}(?!.?$)', '...'))"
        }
    }
    if ($result) {
        Write-Host -f Yellow @"
`nAll required Python components are already installed.
Use 'none', 'skip' or 'S' to skip them. Or just press ENTER on each prompt.
If you want to reinstall them though, use 'all' or 'reinstall' or 'R'.`n
"@
    }
    else {
        Write-Host ""
        Write-Host -f Yellow "Setup is ready for installation now."
    }
    Any-Key Green
}

#-- Operates on parameters of each hash from `$tasks`
#
#  · $title   → print current step
#  · $url     → download from given link, keep as local `$file`
#  · $cmd     → instead of running file, run a custom command
#  · $iargs    → used for MSI installation
#  · $testpth → check for exisiting dir/file
#  · $regkey  → set registry key if successful
#  · $is_opt  → run as expression
#  · $prescn  → used in check-prereq()
#
filter Run-Task {
    # extract flags/vars from $tasks pipe
    $title=""; $cmd=""; $url=""; $iargs=""; $testpth=""; $regkey=""; $is_opt=""; $prescn=""; $_found=""
    ($task = $_).GetEnumerator() | % { Set-Variable -Scope Local -Name $_.key -Value ([regex]::Replace($_.value, "[#{](\w+)[}#]", { param($m) Invoke-Expression ("$"+$m.Groups[1].Value) })) }

    # skip optionals
    if ($is_opt -AND !(Invoke-Expression $is_opt)) { return }

    # print step
    if ($title -match "\d+\.\d+") { $title = "Installing $title" }
    Write-Host -b DarkBlue "`n $title `n"
    chdir($TEMP);

    # test if element (file path or registry key) already exists:
    if ($testpth -AND ($reinstall -ne "all") -AND (Test-Path -Path $testpth)) {
        Write-Host -f DarkGreen -NoNewline " → Is already present."
        if ($reinstall -eq "none") { return }
        Switch -regex ( Ask "   Reinstall [y/N/all/none]? " ) {
            "^all|always|re|^A" { $reinstall = "all"; break }
            "never|none|skip|^S" { $reinstall = "none"; return }
            "^y|yes|1|go|^R" { break } # YES
            ".*" { return } # everything else counts as NO
        }
    }

    # get "filename" part from url
    $file = [regex]::match($url, "/([^/]+?)([\?\#]|$)").Groups[1].Value;

    # download
    if (($url -match "https?://.+") -AND ((!$reuseCachedFiles) -OR !(Test-Path "$TEMP\$file"))) {
        Write-Host -f DarkGreen  " ← $url"
        $wget = New-Object System.Net.WebClient
        $wget.DownloadFile($url, "$TEMP\$file");
    }

    # run shorthand or custom command
    if ($cmd) {
        if (Test-Path $PYTHON) { chdir($PYTHON) }
        if ($cmd -eq "pip") {
            $cmd = "& `"$PYTHON\Scripts\pip.exe`" install $TEMP\$file", $iargs #"
        }
        elseif ($cmd -match "^(easy|easy_install|silent)$") {
            if (!($file)) {
                $cmd = "& `"$PYTHON\Scripts\easy_install.exe`" $url" #"
            }
            else {
                $cmd = "& `"$PYTHON\Scripts\easy_install.exe`" $TEMP\$file" #"
            }
        }
        Write-Host -f DarkGray " → $cmd"
        Invoke-Expression "$cmd"
    }
    # msi
    elseif ($file -match ".+.msi$") {
        Write-Host -f DarkGray (" → msiexec /i " + "$file " + $iargs)
        Start-Process -Wait msiexec -ArgumentList /i,"$TEMP\$file", $iargs
        if ($regkey) {
            Set-ItemProperty -Path "$regkey" -Name "WindowsInstaller"  -Value "0"
        }
    }
    # exe
    elseif ($file -match ".+.exe$") {
        Write-Host -f DarkGray " → $file $iargs"
        if ($iargs) {
            Start-Process -Wait "$TEMP\$file" -ArgumentList $iargs
        }
        else {
            Start-Process -Wait "$TEMP\$file"
        }
    }
    # other files
    elseif ($file) {
        echo " → $file"
        & "$TEMP\$file"
    }
}



#-- run through tasks
Clear-Host
$host.ui.RawUI.BackgroundColor = ($bckgrnd = 'Black')
Console-MaxHeight
Display-Logo
Check-Package
$PYTHON = Check-PythonInstall
$reuseCachedFiles, $optionalInstall = Ask-First
Check-Prerequisites
$tasks | Run-Task  # <-- main loop: process all commands
Any-Key Green

