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
  [string]$UsrFolder = $MyInvocation.MyCommand.Path -replace ("([\\/][^\\/]+){4}$","")
)            

#-- system configuration
$OutputEncoding = [System.Text.Encoding]::UTF8
$regPathCU = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall"
$regPathLM = "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall" #64-Bit machine
if(!(Test-Path $regPathLM)) { $regPathLM = "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall" } #32-Bit machine

$pythonPathLM = (Get-ItemProperty -path ($regPathLM.substring(0,$regPathLM.indexOf("\Microsoft"))+ "\Python\PythonCore\2.7\InstallPath\")).'(default)' 2> $null
$pythonPathCU = (Get-ItemProperty -path ($regPathCU.substring(0,$regPathCU.indexOf("\Microsoft"))+ "\Python\PythonCore\2.7\InstallPath\")).'(default)' 2> $null


#-- what and how to install
#   each row is a list of (title,url,cmd,msi args,regkey,reghive,optional)
$tasks = @(
  <#
  @(
    "Package Dependencies",
    "",
    "Check-Prerequisites",
    "",
    "",
    "",
    ""
  ),
  #>
  @(
    "Python 2.7.12",                                                  # title
    "https://www.python.org/ftp/python/2.7.12/python-2.7.12.msi",     # url
    "",                                                               # custom cmd
    'TARGETDIR="#PYTHON#" /qb-!',                                 # msi args
    "$regPathLM\{9DA28CE5-0AA5-429E-86D8-686ED898C665}",              # registry
    "#PYTHON#\pythonw.exe",                                       # installed check
    ""                                                                # optional component
  ),
  @(
    "PyGtk 2.24.2",
    "http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/pygtk-all-in-one-2.24.2.win32-py2.7.msi",
    "",
    'TARGETDIR="#PYTHON#" ADDLOCAL=ALL REMOVE=PythonExtensionModulePyGtkSourceview2,PythonExtensionModulePyGoocanvas,PythonExtensionModulePyRsvg,DevelopmentTools /qb-!',
    "$regPathLM\{09F82967-D26B-48AC-830E-33191EC177C8}",
    "$regPathLM\{09F82967-D26B-48AC-830E-33191EC177C8}",
    ""
  ),
  @(
    "Python requests",
    "requests", # no download url, pip handles this
    "easy_install",
    "",
    "",
    "#PYTHON#\Lib\site-packages\requests-2.12.1-py2.7.egg",
    ""
  ),
  @(
    "LXML 2.3",
    "https://pypi.python.org/packages/3d/ee/affbc53073a951541b82a0ba2a70de266580c00f94dd768a60f125b04fca/lxml-2.3.win32-py2.7.exe",
    "",
    "",
    "$regPathCU\lxml-py2.7",
    "#PYTHON#\Lib\site-packages\lxml-2.3-py2.7.egg-info",
    ""
  ),
  @(
    "PyQuery 1.2.1",
    "https://pypi.python.org/packages/62/71/8ac1f5c0251e51714d20e4b102710d5eee1683c916616129552b0a025ba5/pyquery-1.2.17-py2.py3-none-any.whl",
    "pip",
    "--disable-pip-version-check",
    "",
    "#PYTHON#\Lib\site-packages\pyquery-1.2.17.dist-info",
    ""
  ),
  @(
    "PIL 1.1.7",
    "http://effbot.org/downloads/PIL-1.1.7.win32-py2.7.exe",
    "",
    "",
    "$regPathCU\PIL-py2.7",
    "#PYTHON#\Lib\site-packages\PIL",
    ""
  ),
  @(
    "Streamripper 1.64.6",
    "http://downloads.sourceforge.net/project/streamripper/streamripper%20%28current%29/1.64.6/streamripper-windows-installer-1.64.6.exe?r=https%3A%2F%2Fsourceforge.net%2Fprojects%2Fstreamripper%2Ffiles%2Fstreamripper%2520%2528current%2529%2F1.64.6%2F&ts=1480104543&use_mirror=kent"
    "",
    "",
    "$regPathLM\Streamripper",
    "#STREAMRIPPER#\streamripper.exe",
    '($true)'
  ),
  @(
    "Uninstall script",
    "",
    'Create-Uninstallscript',
    "",
    "",
    "",
    ""
  ),
  @(
    "Desktop shortcut",
    "",
    'Make-Shortcut -dir $Home\Desktop -name Streamtuner2.lnk -target $PYTHON\pythonw.exe -arg $UsrFolder\bin\streamtuner2',
    "",
    "",
    "" ,# always overwrite $Home\Desktop\Streamtuner2.lnk
    ""
  ),
  @(
    "Startmenu shortcut",
    "",
    'Make-Shortcut -dir "$StartMenu\Streamtuner2" -name Streamtuner2.lnk -target $PYTHON\pythonw.exe -arg $UsrFolder\bin\streamtuner2',
    "",
    "",
    "",
    ""
  ),
  @(
    "Startmenu help.chm",
    "",
    'Make-Shortcut -dir "$StartMenu\Streamtuner2" -name Help.lnk -target $UsrFolder\share\streamtuner2\help\help.chm',
    "",
    "",
    "",
    ""
  ),
  @(
    "Startmenu uninstall",
    "",
    'Make-Shortcut -dir "$StartMenu\Streamtuner2" -name Uninstall.lnk -target $UsrFolder\share\streamtuner2\dev\uninstall.cmd',
    "",
    "",
    "",
    ""
  ),
  @(
    "Startmenu Internet",
    "",
    'Make-Shortcut -dir "$StartMenu\Streamtuner2" -name "Streamtuner2 on the Web.lnk" -target "http://freshcode.club/projects/streamtuner2"',
    "",
    "",
    "",
    ""
  ),
  @(
    "Startmenu Reconfigure",
    "",
    'Make-Shortcut -dir "$StartMenu\Streamtuner2" -name "Reconfigure.lnk" -target $UsrFolder\share\streamtuner2\dev\install_python_gtk.bat',
    "",
    "",
    "",
    ""
  ),
  @(
    "FINISHED", "",  'Any-Key Green', "", "", "", ""
  )
)



#-- startup messages
function Display-Logo {
#    Clear-Host
#    Console-MaxHeight
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
|    Streamtuner2 for Windows                               Version 2.2.0     |
|                                                                             |
|    Installer for Python 2.7.12 & Gtk 2.24.2                                 |
 ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––– 
"@
}
<#
function Warn-NonElevated {
    if (Test-IsElevated) {
        return
    }
    Write-Host ""
    Write-Host -f red " ___________________________________________________________________________"
    Write-Host -f red "|   If you run this script in non-elevated mode you will not be able to     |"
    Write-Host -f red "|               uninstall Streamtuner2, Python and Gtk                      |" 
    Write-Host -f red "|              using the control panels´ software list.                     |"
    Write-Host -f red " ___________________________________________________________________________"
}
#>
function Ask-First {
    Write-Host ""
    Write-Host -f Yellow "Do you want to install Python 2.7.12 and Gtk dependencies now?"
    Write-Host -f Yellow "––––––––––––––––––––––––––––––––––––---–––––––––––––––––––––––"
    Write-Host ""
    if ((Read-Host "[Y/n]") -notmatch "^[yY]|^$") {
        exit;
        # or $tasks = $tasks[7..($tasks.length-1)]
    }
    Write-Host ""
    Write-Host -f Yellow "Do you want to reuse any cached setup files?"
    Write-Host -f Yellow "--------------------------------------------"
    $reuseCachedFiles = Read-Host "[r]euse/[I]gnore)" -match "^[Rr]"
    Write-Host ""
    Write-Host -f Yellow "Do you want to check optional components?"
    Write-Host -f Yellow "-----------------------------------------"
    $optionalInstall = Read-Host "[y/N]" -match "^[Yy]"
    Write-Host ""
    $reuseCachedFiles
    $optionalInstall
    return 
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
    [CmdletBinding()]
    param($dir, $name, $target, $arg=$false)
    if (!(Test-Path -Path $dir)) {
        New-Item -Path $dir -ItemType directory > $null
    }
    $wsh = New-Object -ComObject WScript.Shell
    $lnk = $wsh.CreateShortcut("$dir\$name")
    $lnk.TargetPath = $target
    if ($arg) {
        $lnk.Arguments = '"'+$arg+'"'
        $lnk.IconLocation = "$UsrFolder\share\pixmaps\streamtuner2.ico"
        $lnk.WorkingDirectory = "$UsrFolder\bin"
    }
    $lnk.Save()
}

#-- create uninstall script and registry key
function Create-Uninstallscript {
    [CmdletBinding()]
    param()
    #Write-Host " → Creating uninstall script"
    $UninstallScriptPath = "$UsrFolder\share\streamtuner2\dev\uninstall.cmd"
    $installFolder = $usrFolder.substring(0,$usrFolder.LastIndexOf('\'))
    $UninstallScript = Get-Content -Path $UninstallScriptPath
    Out-File -FilePath $UninstallScriptPath -Encoding ascii -InputObject "@set installFolder=$installFolder"
    Out-File -FilePath $UninstallScriptPath -Encoding ascii -Append -InputObject "@set usrFolder=$usrFolder"
    Out-File -FilePath $UninstallScriptPath -Encoding ascii -Append -InputObject "@set Python=$PYTHON"
    for ($i=3; $i -lt $UninstallScript.Length ; $i++) {
        Out-File -FilePath $UninstallScriptPath -Encoding ascii -Append -InputObject $UninstallScript[$i]
    }
    Out-File -FilePath "$UsrFolder\share\streamtuner2\dev\Y" -Encoding ascii -InputObject "Y"
    #if (Test-IsElevated) {
        #Write-Host "   Writing to registry"
        Remove-Item -Path $regPathCU\Streamtuner2 2> $null        
        New-Item $regPathCU -Name "Streamtuner2" > $null
        Set-Location -Path $regPathCU\Streamtuner2
        New-ItemProperty -Path . -Name DisplayName -PropertyType String -Value "Streamtuner2" > $null
        New-ItemProperty -Path . -Name DisplayVersion -PropertyType String -Value "2.2.0" > $null
        New-ItemProperty -Path . -Name DisplayIcon -PropertyType String -Value "$UsrFolder\share\pixmaps\streamtuner2.ico" > $null
        New-ItemProperty -Path . -Name UninstallString -PropertyType String -Value "$UsrFolder\share\streamtuner2\dev\uninstall.cmd" > $null
        New-ItemProperty -Path . -Name URLInfoAbout -PropertyType String -Value "http://freshcode.club/projects/streamtuner2" > $null
        New-ItemProperty -Path . -Name Publisher -PropertyType String -Value "Mario Salzer" > $null
        New-ItemProperty -Path . -Name NoModify -PropertyType DWord -Value 1 > $null
        New-ItemProperty -Path . -Name NoRepair -PropertyType DWord -Value 1 > $null
    #}
}

function Any-Key($color) {
    Write-Host -f $color "[Press any key]"
    $null = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

#-- ensure ST2 startup script exists in relative path to this install script
function Check-Package {
    if (!(Test-Path -Path("$UsrFolder\bin\streamtuner2"))) {
        Write-Host -b DarkRed -f White @"
The bin\streamtuner2 start script could not be found.
The installation cannot continue.
Do not change the folder structure of the Streamtuner2 package!
If you want to run the install_python_gtk.ps1 script post-install,
please use the -UsrFolder parameter.
"@
        Any-Key Red ; exit
    }
}


#-- Check if previous Python 2.7 installation exists
function Check-PythonInstall {
    if ($pythonPathLM) {$PythonInstalledPath = $PythonPathLM}
    else {$PythonInstalledPath = $PythonPathCU}

    #-- if Python 2.7.12 installed, reuse installation folder
    if (Get-Item -path "$regPathLM\{9DA28CE5-0AA5-429E-86D8-686ED898C665}" 2> $null ) {
        $PYTHON = $pythonInstalledPath.substring(0,$pythonInstalledPath.LastIndexOf('\'))
    }

    #-- older 2.7 version found
    else {
        if (($pythonPathLM) -or ($pythonPathCU)) {
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
            Write-Host "Do you want to continue with the setup anyway?"
            if ((Read-Host "[y/N]") -notmatch "[yY]") {
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
    Check-Package
    ForEach ($task in $tasks) {
        $title, $url, $cmd, $args, $regkey, $check, $optionalComp = $task;
        if ($optionalComp and $optionalInstall) {
                if ($title -match "Streamripper") {
                    $StreamripperPath = (get-itemproperty -path HKCU:\Software\Streamripper).'(default)' 2> $null
                    if (!(Test-Path -Path ($StreamripperPath + "\streamripper.exe"))) {
                        write-host "   - $title not found"
                    }
                    else {
                        Write-Host "   + $title found in $StreamripperPath"
                    }
            }
        }
        else {
            if ($regkey) { 
                if (!(Test-Path -Path $regkey)) {     # avoid runtime error if not existent (not working in PS2)
                    Write-Host "   - $title not found"
                    $result = 0
                }
                else {
                    #Write-Host (Get-ItemProperty -Path $regkey -Name "DisplayName".DisplayName).DisplayName " found"
                    Write-Host "   + $title found"
                }
            }
            elseif ($title -match "requests|PyQuery") {
                if (!(Test-Path -Path ($check -replace "#PYTHON#","$PYTHON"))) {
                    write-Host "   - $title not found"
                    $result = 0
                }
                else {
                    Write-Host "   + $title found"
                }
            }
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
    $streamripperPath
    return
}



#-- ask before running
Console-MaxHeight
Display-Logo
$UsrFolder = $MyInvocation.MyCommand.Path -replace ("([\\/][^\\/]+){4}$","") #temp fix for running on Windows 10
$PYTHON = Check-PythonInstall
$reuseCachedFiles, $optionalInstall = Ask-First
$STREAMRIPPER = Check-Prerequisites
Clear-Host
Display-Logo



#-- process
ForEach ($task in $tasks) {
    ForEach ($key in $task.keys()) { $task[$key] = [regex]::Replace($task[$key], "#(\w+)#", { param($m) Invoke-Expression ("$"+$m.Groups[1].Value) }) }
    $title, $url, $cmd, $args, $regkey, $testpath, $optional = $task;
    
    # options
    if ($optional -AND (Invoke-Expression $optional) -AND !$optionalInstall) {
        continue    # ↑ expression test
    }

    # print step
    if ($title -match "\d+\.\d+") { $title = "Installing $title" }
    Write-Host -b DarkBlue "`n $title `n"
    chdir($TEMP);

    # test if element (file path or registry key) already exists:
    if ($reinstall -eq "all") {
    }
    elseif ($testpath -AND (Test-Path -Path $testpath)) {
        if ($reinstall -eq "none") {Write-Host " → Kept as is."; continue }
        Write-Host -f Green -NoNewline " → Is already present."
        #if ($title -match "Python 2.7.12") {Write-Host -f Green " (in $PYTHON)"}
        #if ($title -match "Streamripper 1.64.6") {Write-Host -f Green " (in $STREAMRIPPER)"}
        Write-Host -f Yellow -NoNewline "   Reinstall [y/N/all/none]? " ; $y = Read-Host ; Write-Host ""
        if ($y -match "^all|always|re|^A") { $reinstall = "all" }
        elseif ($y -match "never|none|skip|^S") { $reinstall = "none"; continue }
        elseif ($y -match "^y|yes|1|go|^R") { } # YES
        else { continue } # everything else counts as NO
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
            $cmd = "& `"$PYTHON\Scripts\pip.exe`" install $TEMP\$file", $args #"
        }
        elseif ($cmd -match "^(easy|easy_install|silent)$") {
            $cmd = "& `"$PYTHON\Scripts\easy_install.exe`" $url" #"
        }
        if ($title -notmatch "FINISHED") {
            Write-Host -f DarkYellow   " → $cmd"
        }
        Invoke-Expression "$cmd"
    }
    # msi
    elseif ($file -match ".+.msi$") {
        $args = $args -replace "#PYTHON#","$PYTHON"
        Write-Host -f DarkYellow (" → msiexec /i " + "$file " + $args)
        Start-Process -Wait msiexec -ArgumentList /i,"$TEMP\$file", $args
        if ($regkey) {
            Set-ItemProperty -Path "$regkey" -Name "WindowsInstaller"  -Value "0" -ErrorAction SilentlyContinue
        }
    }
    # exe
    elseif ($file -match ".+.exe$") {
        write-host -f DarkYellow " → $file $args"
        if ($args) {
            Start-Process -Wait "$TEMP\$file" -ArgumentList $args
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

