<#
 #
 # Run as post-install script for .exe package
 #
 #  - downloads Python + Gtk
 #  - some python libraries
 #  - and runs their respective installers
 #  - crafts streamtuner2 desktop shortcut
 #  - crafts streamtuner2 shortcuts in Start menu
 #
 #>


#-- defaults / parameters
[CmdletBinding()]            
Param(
  [string]$reinstall = "ask",
  [switch]$keepdownloads = $false,
  [string]$TEMP = $env:TEMP,
  [string]$PYTHON = "C:\Python27",
  [string]$StartMenu = "$env:USERPROFILE\AppData\Roaming\Microsoft\Windows\Start Menu\Programs",
  [string]$UsrFolder = $MyInvocation.MyCommand.Path -replace ("([\\/][^\\/]+){4}$","")
)            
$OutputEncoding = [System.Text.Encoding]::UTF8
$OSVersion = $env:OSVersion.Version
$regPathCU = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall"
$regPathLM = "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
if(!(Test-Path $regPathLM)) { $regPathLM = "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall" }


#-- what and how to install
#   each row is a list of (title,url,cmd,msi args,regkey,reghive)
$tasks = @(
  @(
    "Package Dependencies",
    "",
    "Check-Prerequisites",
    "",
    "",
    ""
  ),
  @(
    "Python 2.7.12",                                                  # title
    "https://www.python.org/ftp/python/2.7.12/python-2.7.12.msi",     # url
    "",                                                               # custom cmd
    "TARGETDIR=C:\Python27 /qb-!",                                    # msi args
    "$regPathLM\{9DA28CE5-0AA5-429E-86D8-686ED898C665}",              # registry
    "$regPathLM\{9DA28CE5-0AA5-429E-86D8-686ED898C665}"               # installed check
  ),
  @(
    "PyGtk 2.24.2",
    "http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/pygtk-all-in-one-2.24.2.win32-py2.7.msi",
    "",
    "TARGETDIR=C:\Python27 ADDLOCAL=ALL REMOVE=PythonExtensionModulePyGtkSourceview2,PythonExtensionModulePyGoocanvas,PythonExtensionModulePyRsvg,DevelopmentTools /qb-!",
    "$regPathLM\{09F82967-D26B-48AC-830E-33191EC177C8}",
    "$regPathLM\{09F82967-D26B-48AC-830E-33191EC177C8}"
  ),
  @(
    "Python requests",
    "requests", # no download url, pip handles this
    "easy_install",
    "",
    "",
    "$PYTHON\Lib\site-packages\requests-2.12.1-py2.7.egg"
  ),
  @(
    "LXML 2.3",
    "https://pypi.python.org/packages/3d/ee/affbc53073a951541b82a0ba2a70de266580c00f94dd768a60f125b04fca/lxml-2.3.win32-py2.7.exe",
    "",
    "",
    "$regPathCU\lxml-py2.7",
    "$PYTHON\Lib\site-packages\lxml-2.3-py2.7.egg-info"
  ),
  @(
    "PyQuery 1.2.1",
    "https://pypi.python.org/packages/62/71/8ac1f5c0251e51714d20e4b102710d5eee1683c916616129552b0a025ba5/pyquery-1.2.17-py2.py3-none-any.whl",
    "pip",
    "--disable-pip-version-check",
    "",
    "$PYTHON\Lib\site-packages\pyquery-1.2.17.dist-info"
  ),
  @(
    "PIL 1.1.7",
    "http://effbot.org/downloads/PIL-1.1.7.win32-py2.7.exe",
    "",
    "",
    "$regPathCU\PIL-py2.7",
    "$PYTHON\Lib\site-packages\PIL"
  ),
  #@(
  #  "ST2 invocation (relocatability)",
  #  "",
  #  'Rewrite-Startscript',
  #  "",
  #  "",
  #  "$UsrFolder\bin\streamtuner2.bak"
  #),
  @(
    "Uninstall script",
    "",
    'Create-Uninstallscript',
    "",
    "",
    ""
  ),
  @(
    "Desktop shortcut",
    "",
    'Make-Shortcut -dir $Home\Desktop -name Streamtuner2.lnk -target $PYTHON\pythonw.exe -arg "$UsrFolder\bin\streamtuner2"',
    "",
    "",
    "" # always overwrite $Home\Desktop\Streamtuner2.lnk
  ),
  @(
    "Startmenu shortcut",
    "",
    'Make-Shortcut -dir "$StartMenu\Streamtuner2" -name Streamtuner2.lnk -target $PYTHON\pythonw.exe -arg "$UsrFolder\bin\streamtuner2"',
    "",
    "",
    ""
  ),
  @(
    "Startmenu help.chm",
    "",
    'Make-Shortcut -dir "$StartMenu\Streamtuner2" -name Help.lnk -target "$UsrFolder\share\streamtuner2\help\help.chm"',
    "",
    "",
    ""
  ),
  @(
    "FINISHED", "", 'Any-Key Green', "", "", ""
  )
)


#-- startup messages
function Display-Logo {
    Clear-Host
    Console-MaxHeight
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
function Ask-First {
    Write-Host ""
    Write-Host -f Yellow "Do you want to install Python 2.7 and Gtk dependencies now?"
    Write-Host -f Yellow "–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––"
    Write-Host ""
    if ((Read-Host "[Y/n]") -notmatch "[yYi123ar]|^$") {
        exit;
        # or $tasks = $tasks[7..($tasks.length-1)]
    }
}
function Console-MaxHeight {
  if ($Host.Name -match "console") {
    $MaxHeight = $host.UI.RawUI.MaxPhysicalWindowSize.Height
    $MaxWidth = $host.UI.RawUI.MaxPhysicalWindowSize.Width
    $MyBuffer = $Host.UI.RawUI.BufferSize
    $MyWindow = $Host.UI.RawUI.WindowSize
    $MyWindow.Height = ($MaxHeight)
    #$MyWindow.Width = ($Maxwidth-2)
    $MyBuffer.Height = (9999)
    #$MyBuffer.Width = ($Maxwidth-2)
    $host.UI.RawUI.set_bufferSize($MyBuffer)
    $host.UI.RawUI.set_windowSize($MyWindow)
  }
}

#-- create Desktop/Startmenu shortcuts
function Make-Shortcut {
    [CmdletBinding()]
    param($dir, $name, $target, $arg=$false)
    if (!(Test-Path -Path $dir)) {
        New-Item -Path $dir -ItemType directory
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
    Write-Host " → Creating uninstall script"
    $UninstallScriptPath = "$UsrFolder\share\streamtuner2\dev\uninstall.cmd"
    $installFolder = $usrFolder.substring(0,$usrFolder.LastIndexOf("\")) #"
    $UninstallScript = Get-Content -Path $UninstallScriptPath
    Out-File -FilePath $UninstallScriptPath -Encoding ascii -InputObject "@set installFolder=$installFolder"
    Out-File -FilePath $UninstallScriptPath -Encoding ascii -Append -InputObject "@set usrFolder=$usrFolder"
    Out-File -FilePath $UninstallScriptPath -Encoding ascii -Append -InputObject "@set Python=$PYTHON"
    for ($i=3; $i -lt $UninstallScript.Length ; $i++) {
        Out-File -FilePath $UninstallScriptPath -Encoding ascii -Append -InputObject $UninstallScript[$i]
    }
    Out-File -FilePath "$UsrFolder\share\streamtuner2\dev\Y" -Encoding ascii -InputObject "Y"
    if (Test-IsElevated) {
        Write-Host "   Writing registry"
        if (Test-Path $regPathLM\Streamtuner2) {
            Remove-Item -Path $regPathLM\Streamtuner2 | out-null        
        }
        New-Item $regPathLM -Name "Streamtuner2" | out-null
        Set-Location -Path $regPathLM\Streamtuner2
        New-ItemProperty -Path . -Name DisplayName -PropertyType String -Value "Streamtuner2" | out-null
        New-ItemProperty -Path . -Name DisplayVersion -PropertyType String -Value "2.2.0" | out-null
        New-ItemProperty -Path . -Name DisplayIcon -PropertyType String -Value "$UsrFolder\share\pixmaps\streamtuner2.ico" | out-null
        New-ItemProperty -Path . -Name UninstallString -PropertyType String -Value "$UsrFolder\share\streamtuner2\dev\uninstall.cmd" | out-null
        New-ItemProperty -Path . -Name URLInfoAbout -PropertyType String -Value "http://freshcode.club/projects/streamtuner2" | out-null
        New-ItemProperty -Path . -Name Publisher -PropertyType String -Value "Mario Salzer" | out-null
        New-ItemProperty -Path . -Name NoModify -PropertyType DWord -Value 1 | out-null
        New-ItemProperty -Path . -Name NoRepair -PropertyType DWord -Value 1 | out-null
    }
    if (!(([environment]::OSVersion.Version.Major -match 10) -AND ($name -match "Uninstall.lnk"))) {  # no Uninstall.lnk on Windows 10
        Make-Shortcut -dir "$StartMenu\Streamtuner2" -name Uninstall.lnk -target "$UsrFolder\share\streamtuner2\dev\uninstall.cmd"
    }    
}

#-- modify ST2 wrapper script
function Rewrite-Startscript {
    [CmdletBinding()]
    param()
    $WrapperScript = Get-Content -Path "$UsrFolder\bin\streamtuner2"
    for ($i=0; $i -lt $WrapperScript.Length ; $i++) {
        $WrapperScript[$i] = $WrapperScript[$i].Replace("sys.path.insert(0, " + """" + "/usr/","sys.path.insert(0, " + """" + $UsrFolder + "\\")
        Out-File -FilePath $UsrFolder"\bin\streamtuner2.new" -Encoding ascii -Append -InputObject $WrapperScript[$i]
    }

    if (Test-Path -Path "$UsrFolder\bin\streamtuner2.bak") {
        Remove-Item -Path "$UsrFolder\bin\streamtuner2.bak" -Force
    }
    Rename-Item -NewName "streamtuner2.bak" -Path "$UsrFolder\bin\streamtuner2" #save old script
    Rename-Item -NewName "streamtuner2" -Path "$UsrFolder\bin\streamtuner2.new"
    Set-Acl $UsrFolder"\bin\streamtuner2" (Get-Acl "$UsrFolder\bin\streamtuner2.bak") # set file permissions 
}

#-- admin check
function Test-IsElevated {
    [Security.Principal.WindowsPrincipal] $Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    return $Identity.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Any-Key($color) {
    Write-Host -f $color "[Press any key]"
    $null = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

#-- ensure ST2 startup script exists in relative path to this install script
function Check-Package {
    if (!(Test-Path -Path("$UsrFolder\bin\streamtuner2"))) {
        Write-Host -b DarkRed -f White "The bin\streamtuner2 start script could not be found. The installation cannot continue. Do not change the folder structure of the Streamtuner2 package! If you want to run the install_python_gtk.ps1 script post-install, please use the -UsrFolder parameter."
        Any-Key Red ; exit
    }
}

#-- check prereqs installation
function Check-Prerequisites {
    [CmdletBinding()]
    param($result = 1)
    Check-Package
    ForEach ($task in $tasks) {
        $title, $url, $cmd, $args, $regkey, $check = $task;
        if ($regkey) { 
            if (!(Test-Path -Path $regkey)) {     # avoid runtime error if not existent (not working in PS1)
                Write-Host "   - $title not found"
                $result = 0
            }
            else {
               #Write-Host (Get-ItemProperty -Path $regkey -Name "DisplayName".DisplayName).DisplayName " found"
                Write-Host "   + $title found"
            }
        }
        elseif ($title -match "requests|PyQuery") {
            if (!(Test-Path -Path $check)) {
                write-Host "   - $title not found"
                $result = 0
            }
            else {
                Write-Host "   + $title found"
            }
        }
    }
    if ($result) {
        Write-Host -f Yellow "`nAll required Python components are already installed. You can use 'none' or 'skip' or 'S' to skip them. Or just press ENTER on each following prompt. If you want to reinstall them though, use 'all' or 'reinstall' or 'R'.`n"
    }
}



#-- ask before running
Display-Logo
Warn-NonElevated
Ask-First


#-- process
ForEach ($task in $tasks) {
    $title, $url, $cmd, $args, $regkey, $testpath = $task;

    # print step
    if ($title -match "\d+\.\d+") { $title = "Installing $title" }
    Write-Host -b DarkBlue "`n $title `n"
    chdir($TEMP);
    
    # test if element (file path or registry key) already exists:
    if ($reinstall -eq "all") {
    }
    elseif ($testpath -AND (Test-Path -Path $testpath)) {
        echo -f Yellow " → Is already present."
        if ($reinstall -eq "none") { continue }
        Write-Host -f Yellow -NoNewline "   Reinstall [y/N/all/none]? " ; $y = Read-Host ; Write-Host ""
        if ($y -match "^all|always|re|^A") { $reinstall = "all" }
        elseif ($y -match "never|none|skip|^S") { $reinstall = "none"; continue }
        elseif ($y -match "^y|yes|1|go|^R") { } # YES
        else { continue } # everything else counts as NO
    }

    # get "filename" part from url
    $file = [regex]::match($url, "/([^/]+?)([\?\#]|$)").Groups[1].Value;

    # download
    if (($url -match "https?://.+") -AND ($keepdownloads -OR !(Test-Path "$TEMP\$file"))) {
        Write-Host -f DarkGreen  " ← $url"
        $wget = New-Object System.Net.WebClient
        $wget.DownloadFile($url, "$TEMP\$file");
    }

    # run shorthand or custom command
    if ($cmd) {
        if (Test-Path $PYTHON) { chdir($PYTHON) }
        if ($cmd -eq "pip") {
            $cmd = "& $PYTHON\Scripts\pip.exe install $TEMP\$file", $args
        }
        elseif ($cmd -match "^(easy|easy_install|silent)$") {
             $cmd = "& $PYTHON\Scripts\easy_install.exe $url"
        }
        Write-Host -f DarkYellow   " → $cmd"
        Invoke-Expression "$cmd"
    }
    # msi
    elseif ($file -match ".+.msi$") {
        Write-Host -f DarkYellow " → msiexec /i $file $args"
        Start-Process -Wait msiexec -ArgumentList /i,"$TEMP\$file",$args
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

