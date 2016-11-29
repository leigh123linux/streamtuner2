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
 #[string]$UninstallPath = "$UsrFolder\share\streamtuner2\dev\uninstall.cmd",
 #[string]$IconPath = "$UsrFolder\share\pixmaps\streamtuner2.ico",
  [string]$AboutLink = "http://freshcode.club/projects/streamtuner2"
 #[string]$ModifyPath = $MyInvocation.MyCommand.Path -replace (".ps1", ".bat")
)            

#-- paths
$UsrFolder = $MyInvocation.MyCommand.Path -replace ("([\\/][^\\/]+){4}$","")
$UninstallPath = "$UsrFolder\share\streamtuner2\dev\uninstall.cmd"
$ModifyPath = $MyInvocation.MyCommand.Path -replace (".ps1", ".bat")
$IconPath = "$UsrFolder\share\pixmaps\streamtuner2.ico"

#-- system configuration
$OutputEncoding = [System.Text.Encoding]::UTF8
$regPathCU = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall"
$regPathLM = "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall" #64-Bit machine
if(!(Test-Path $regPathLM)) {                                                        #32-Bit machine
    $regPathLM = "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall"
    $ProgramFiles = "%ProgramFiles%"
}
$STREAMRIPPER = "$ProgramFiles\Streamripper"
$pythonPathLM = (Get-ItemProperty -path ($regPathLM.substring(0,$regPathLM.indexOf("\Microsoft"))+ "\Python\PythonCore\2.7\InstallPath\")).'(default)' 2> $null
$pythonPathCU = (Get-ItemProperty -path ($regPathCU.substring(0,$regPathCU.indexOf("\Microsoft"))+ "\Python\PythonCore\2.7\InstallPath\")).'(default)' 2> $null


#-- what and how to install
#   each row is a list of (title,url,cmd,msi args,regkey,optional)
$tasks = @(
  @(
    "Python 2.7.12",                                                  # title
    "https://www.python.org/ftp/python/2.7.12/python-2.7.12.msi",     # url
    "",                                                               # custom cmd
    'TARGETDIR="{PYTHON}" /qb-!',                                     # msi args
    "$regPathLM\{9DA28CE5-0AA5-429E-86D8-686ED898C665}",              # registry
    "{PYTHON}\pythonw.exe",                                           # installed check
    ""                                                                # is optional?
  ),
  @(
    "PyGtk 2.24.2",
    "http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/pygtk-all-in-one-2.24.2.win32-py2.7.msi",
    "",
    'TARGETDIR="{PYTHON}" ADDLOCAL=ALL REMOVE=PythonExtensionModulePyGtkSourceview2,PythonExtensionModulePyGoocanvas,PythonExtensionModulePyRsvg,DevelopmentTools /qb-!',
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
    "{PYTHON}\Lib\site-packages\requests-2.12.1-py2.7.egg",
    ""
  ),
  @(
    "LXML 2.3",
    "https://pypi.python.org/packages/d4/fa/e4e0c7a8fe971b10e275cdc20efd16f553a225e700c400c11da25276e4f4/lxml-2.3-py2.7-win32.egg",
    "easy_install",
    "",
    "",
    "{PYTHON}\Lib\site-packages\lxml-2.3-py2.7-win32.egg",
    ""
  ),
  @(
    "PyQuery 1.2.1",
    "https://pypi.python.org/packages/62/71/8ac1f5c0251e51714d20e4b102710d5eee1683c916616129552b0a025ba5/pyquery-1.2.17-py2.py3-none-any.whl",
    "pip",
    "--disable-pip-version-check",
    "",
    "{PYTHON}\Lib\site-packages\pyquery-1.2.17.dist-info",
    ""
  ),
  @(
    "PIL 1.1.7",
    "http://effbot.org/downloads/PIL-1.1.7.win32-py2.7.exe",
    "",
    "",
    "$regPathCU\PIL-py2.7",
    "{PYTHON}\Lib\site-packages\PIL",
    ""
  ),
  @(
    "Streamripper 1.64.6",
    "http://downloads.sourceforge.net/project/streamripper/streamripper%20%28current%29/1.64.6/streamripper-windows-installer-1.64.6.exe?r=https%3A%2F%2Fsourceforge.net%2Fprojects%2Fstreamripper%2Ffiles%2Fstreamripper%2520%2528current%2529%2F1.64.6%2F&ts=1480104543&use_mirror=kent"
    "",
    "/S  /D={STREAMRIPPER}"  #NSIS does not use double quotes in /D parm,
    "$regPathLM\Streamripper",
    "{STREAMRIPPER}\streamripper.exe",
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
    'Make-Shortcut -dir "$StartMenu\Streamtuner2" -name Uninstall.lnk -target $UninstallPath',
    "",
    "",
    "",
    ""
  ),
  @(
    "Startmenu Internet",
    "",
    'Make-Shortcut -dir "$StartMenu\Streamtuner2" -name "Streamtuner2 on the Web.lnk" -target "$AboutLink"',
    "",
    "",
    "",
    ""
  ),
  @(
    "Startmenu Reconfigure",
    "",
    'Make-Shortcut -dir "$StartMenu\Streamtuner2" -name "Reconfigure.lnk" -target $ModifyPath',
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
function Ask-First {
    Write-Host ""
    if ((Ask "Do you want to install Python 2.7.12 and Gtk dependencies now? [Y/n] ") -notmatch "^[yY]|^$") {
        exit;  # or $tasks = $tasks[7..($tasks.length-1)]
    }
    $reuseCachedFiles = (Ask "Do you want to reuse any cached setup files? [r]euse/[I]gnore) ") -match "^[Rr]"
    $optionalInstall =  (Ask "Do you want to check optional components? [y/N] ") -match "^[Yy]"
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
        $lnk.IconLocation = "$IconPath"
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
    Out-File -FilePath $UninstallScriptPath -Encoding ascii -Append -InputObject "@set StreamripperFolder=$STREAMRIPPER"
    <#
    if ($STREAMRIPPER) {
        Out-File -FilePath $UninstallScriptPath -Encoding ascii -Append -InputObject "@set StreamripperFolder=$STREAMRIPPER"
    }
    #>
    for ($i=4; $i -lt $UninstallScript.Length ; $i++) {
        Out-File -FilePath $UninstallScriptPath -Encoding ascii -Append -InputObject $UninstallScript[$i]
    }
    #Out-File -FilePath "$UsrFolder\share\streamtuner2\dev\Y" -Encoding ascii -InputObject "Y"
    #if (Test-IsElevated) {
    #Write-Host "   Writing to registry"
    Remove-Item -Path $regPathCU\Streamtuner2 2> $null        
    New-Item $regPathCU -Name "Streamtuner2" > $null
    Set-Location -Path $regPathCU\Streamtuner2
    New-ItemProperty -Path . -Name DisplayName -PropertyType String -Value "Streamtuner2" > $null
    New-ItemProperty -Path . -Name DisplayVersion -PropertyType String -Value "2.2.0" > $null
    New-ItemProperty -Path . -Name DisplayIcon -PropertyType String -Value "$IconPath" > $null
    New-ItemProperty -Path . -Name UninstallString -PropertyType String -Value "$UninstallPath" > $null
    New-ItemProperty -Path . -Name URLInfoAbout -PropertyType String -Value "$AboutLink" > $null
    New-ItemProperty -Path . -Name Publisher -PropertyType String -Value "Mario Salzer" > $null
    New-ItemProperty -Path . -Name NoModify -PropertyType DWord -Value 0 > $null
    New-ItemProperty -Path . -Name ModifyPath -PropertyType String -Value "$ModifyPath" > $null
    New-ItemProperty -Path . -Name NoRepair -PropertyType DWord -Value 1 > $null
    New-ItemProperty -Path . -Name HelpLink -PropertyType String -Value "http://fossil.include-once.org/streamtuner2/wiki?name=windows" > $null
    #}
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
        Write-Host -n -f DarkCyan   $matches[3] # Y
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
    Check-Package
    ForEach ($task in $tasks) {
        $title, $url, $cmd, $args, $regkey, $check, $optional = $task;
        if ($optional) {
            if ($optionalInstall) {
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
        }
        
        else {
            if ($regkey) { 
                if (!(Test-Path -Path $regkey)) {     # avoid runtime error if not existent (not working in PS2)
                    Write-Host "   - $title not found"
                    $result = 0
                }
                else {
                    #Write-Host (Get-ItemProperty -Path $regkey -Name "DisplayName".DisplayName).DisplayName " found"
                    if ($title -match "Python 2.7.12") {
                        Write-Host "   + $title found in $PYTHON"
                    }
                    else {
                        Write-Host "   + $title found"
                    }
                }
            }
            elseif ($title -match "requests|PyQuery|LXML") {
                if (!(Test-Path -Path ($check -replace "{PYTHON}","$PYTHON"))) {
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
Clear-Host
Console-MaxHeight
Display-Logo
$PYTHON = Check-PythonInstall
$reuseCachedFiles, $optionalInstall = Ask-First
if ($SR = Check-Prerequisites) {$STREAMRIPPER = $SR}
#Clear-Host
#Display-Logo


#-- process
:tasks ForEach ($task in $tasks) {
    $title, $url, $cmd, $args, $regkey, $testpath, $optional = $task | 
       % { [regex]::Replace($_, "[#{](\w+)[}#]", { param($m) Invoke-Expression ("$"+$m.Groups[1].Value) }) }

    # options
    if ($optional -AND (Invoke-Expression $optional) -AND !$optionalInstall) {
        continue    # optional expression test
    }

    # print step
    if ($title -match "\d+\.\d+") { $title = "Installing $title" }
    Write-Host -b DarkBlue "`n $title `n"
    chdir($TEMP);

    # test if element (file path or registry key) already exists:
    if ($testpath -AND ($reinstall -ne "all") -AND (Test-Path -Path $testpath)) {
        Write-Host -f Green -NoNewline " → Is already present."
        if ($reinstall -eq "none") { continue tasks }
        Switch -regex ( Ask "   Reinstall [y/N/all/none]? " ) {
            "^all|always|re|^A" { $reinstall = "all" }
            "never|none|skip|^S" { $reinstall = "none"; continue tasks }
            "^y|yes|1|go|^R" { } # YES
            ".*" { continue tasks } # everything else counts as NO
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
            $cmd = "& `"$PYTHON\Scripts\pip.exe`" install $TEMP\$file", $args #"
        }
        elseif ($cmd -match "^(easy|easy_install|silent)$") {
            if (!($file)) {
                $cmd = "& `"$PYTHON\Scripts\easy_install.exe`" $url" #"
            }
            else {
                $cmd = "& `"$PYTHON\Scripts\easy_install.exe`" $TEMP\$file" #"
            }
        }
        if ($title -notmatch "FINISHED") {
            Write-Host -f DarkYellow   " → $cmd"
        }
        Invoke-Expression "$cmd"
    }
    # msi
    elseif ($file -match ".+.msi$") {
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

