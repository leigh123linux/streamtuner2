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

[CmdletBinding()]            
Param()            

# admin check            
function Test-IsElevated {
    [CmdletBinding()]
    param()
    [Security.Principal.WindowsPrincipal] $Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $Identity.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}


# prerequisites check
function Check-Prerequisites {
    [CmdletBinding()]
    param()

    ForEach ($task in $tasks) {
       $title, $url, $cmd, $args, $regkey, $check = $task;
        if ($regkey) { 
            if (!(Get-Item -Path $regkey)) {     # avoid runtime error if not existent (not working in PS1)
                Write-Host $title " not found"
                return 0
            }
            else {
                Write-Host (Get-ItemProperty -Path $regkey -Name "DisplayName".DisplayName).DisplayName " found"
            }
        }
        elseif ($title = "Python requests") {
            if (!(Get-Item -Path "$PYTHON\Lib\site-packages\requests-2.12.1-py2.7.egg")) {
                write-Host $title " not found"
                return 0
            }
            else {
                Write-Host $title " found"
            }
        }
    
        elseif ($title = "PyQuery 1.2.1") {
            if (!(Get-Item -Path "$PYTHON\Lib\site-packages\pyquery-1.2.17.dist-info")) {
                Write-Host $title " not found"
                return 0
            }
            else {
                Write-Host $title " found"
            }
        }
    }
    return 1
}

# default paths
$TEMP = $env:TEMP
$PYTHON = "C:\Python27"
$OutputEncoding = [System.Text.Encoding]::UTF8
$StartMenu = "$env:USERPROFILE\AppData\Roaming\Microsoft\Windows\Start Menu\Programs"

#-- Get ST installation folder
$ScriptPath = (Split-Path $MyInvocation.MyCommand.Path -Parent).Split("\") #PS1/2 compatibility"
$UsrFolder=$ScriptPath[0]+"\"
for ($i=1; $i -le $ScriptPath.Length - 4; $i++) {
    $UsrFolder = $UsrFolder+$ScriptPath[$i]+"\"
}
if (!(Test-Path -Path("..\..\..\bin\streamtuner2"))) {
    Write-Host -foregroundcolor Red "The Streamtuner2 start script could not be found. The installation cannot continue."
    Write-Host -foregroundcolor Red "Please do not change the folder structure of the Streamtuner2 package!"
    Write-Host -foregroundcolor Red "Press any key to exit ..."
    $null = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit;
}    

# prepare registry lookup
$regPathCU = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall"
$regPathHK = "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
if(!(Test-Path $regPathHK)) {
    $regPathHK = "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall"
}


#-- what and how to install
#   each row is a list of (title,url,cmd,msi args,regkey,reghive)
$tasks = @(
  @(
    "Python 2.7.12",                                                  # title
    "https://www.python.org/ftp/python/2.7.12/python-2.7.12.msi",     # url
    "",                                                               # custom cmd
    "TARGETDIR=C:\Python27 /qb",                                      # msi args
    "$regPathHK\{9DA28CE5-0AA5-429E-86D8-686ED898C665}",              # registry
    "$regPathHK\{9DA28CE5-0AA5-429E-86D8-686ED898C665}"               # installed check
  ),
  @(
    "PyGtk 2.24.2",
    "http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/pygtk-all-in-one-2.24.2.win32-py2.7.msi",
    "",
    "TARGETDIR=C:\Python27 ADDLOCAL=ALL REMOVE=PythonExtensionModulePyGtkSourceview2,PythonExtensionModulePyGoocanvas,PythonExtensionModulePyRsvg,DevelopmentTools /qb",
    "$regPathHK\{09F82967-D26B-48AC-830E-33191EC177C8}",
    "$regPathHK\{09F82967-D26B-48AC-830E-33191EC177C8}"
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
    "$regPathCU\lxml-py2.7"
  ),
  @(
    "PyQuery 1.2.1",
    "https://pypi.python.org/packages/62/71/8ac1f5c0251e51714d20e4b102710d5eee1683c916616129552b0a025ba5/pyquery-1.2.17-py2.py3-none-any.whl",
    "pip",
    "",
    "",
    "$PYTHON\Lib\site-packages\pyquery-1.2.17.dist-info"
  ),
  @(
    "PIL 1.1.7",
    "http://effbot.org/downloads/PIL-1.1.7.win32-py2.7.exe",
    "",
    "",
    "$regPathCU\PIL-py2.7",
    "$regPathCU\PIL-py2.7"
  ),
  @(
    "ST2 invocation (relocatability)",
    "",
    'Rewrite-Startscript',
    "",
    "",
    "$UsrFolder\bin\streamtuner2.bak"
  ),
  @(
    "Desktop shortcut",
    "",
    'Make-Shortcut -dir $Home\Desktop -name Streamtuner2.lnk -target $PYTHON\pythonw.exe -arg $UsrFolder\bin\streamtuner2',
    "",
    "",
    "$Home\Desktop\Streamtuner2.lnk"
  ),
  @(
    "Startmenu shortcut",
    "",
    'Make-Shortcut -dir "$StartMenu\Streamtuner2" -name Streamtuner2.lnk -target $PYTHON\pythonw.exe -arg $UsrFolder\bin\streamtuner2',
    "",
    "",
    ""
  ),
  @(
    "Startmenu help.chm",
    "",
    'Make-Shortcut -dir "$StartMenu\Streamtuner2" -name Help.lnk -target $UsrFolder\share\streamtuner2\help\help.chm -arg $false',
    "",
    "",
    ""
  ),
  @(
    "**FINISHED**.", "", '$true', "", "", ""
  )
)

#-- create Desktop/Startmenu shortcuts
function Make-Shortcut {
    [CmdletBinding()]
    param($dir, $name, $target, $arg)
    if (!(Test-Path -Path $dir)) {
        New-Item -Path $dir -ItemType directory
    }
    $wsh = New-Object -ComObject WScript.Shell
    $lnk = $wsh.CreateShortcut("$dir\$name")
    $lnk.TargetPath = $target
    if ($arg) {
        $lnk.Arguments = $arg
        $lnk.IconLocation = $UsrFolder + "share\pixmaps\streamtuner2.ico"
        $lnk.WorkingDirectory = $UsrFolder + "bin"
    }
    $lnk.Save()
}


#-- modify ST2 wrapper script
function Rewrite-Startscript {
    [CmdletBinding()]
    param()
    $WrapperScript = Get-Content -Path $UsrFolder"\bin\streamtuner2"
    for ($i=0; $i -lt $WrapperScript.Length ; $i++) {
        $WrapperScript[$i] = $WrapperScript[$i].Replace("sys.path.insert(0, " + """" + "/usr/","sys.path.insert(0, " + """" + $UsrFolder)
        Out-File -FilePath $UsrFolder"\bin\streamtuner2.new" -Encoding ascii -Append -InputObject $WrapperScript[$i]
    }

    if (Test-Path -Path $UsrFolder"\bin\streamtuner2.bak") {
        Remove-Item -Path $UsrFolder"\bin\streamtuner2.bak" -Force
    }
    Rename-Item -NewName "streamtuner2.bak" -Path $UsrFolder"\bin\streamtuner2" #save old script
    Rename-Item -NewName "streamtuner2" -Path $UsrFolder"\bin\streamtuner2.new"
    Set-Acl $UsrFolder"\bin\streamtuner2" (Get-Acl $UsrFolder"\bin\streamtuner2.bak") # set file permissions 
}



#-- ask before running
Write-Host ""
Write-Host -foregroundcolor Yellow "Do you want to install Python 2.7 and Gtk dependencies now?"
Write-Host -foregroundcolor Yellow "–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––"
Write-Host -foregroundcolor Yellow " → This will install 32-bit versions of Python and Gtk."
Write-Host -foregroundcolor Yellow " → Downloads will remain in $TEMP"
if(!(Test-IsElevated)) {
    Write-Host ""
    Write-Host -foregroundcolor red "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
    Write-Host -foregroundcolor red "┃ ⚠ ⛔  If you run this script in non-elevated mode you will not be able to  ┃"
    Write-Host -foregroundcolor red "┃      uninstall Python and Gtk using the control panels´ software list.    ┃"
    Write-Host -foregroundcolor red "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
}
Write-Host ""
if ((Read-Host "y/n") -notmatch "[yY123ar]") {
    exit;
}
Write-Host ""


#-- check prereqs installation
<#
Write-Host ""
Write-Host "Checking installation"
Write-Host "------------------------"
Write-Host ""
$prereqs = (Check-Prerequisites)
if ($prereqs -match 1) {
    Write-Host ""
    Write-Host -foregroundcolor Yellow "All required Python components are already installed."
    Write-Host -foregroundcolor Yellow "Do you want to (R)einstall them or (S)kip the installation?"
    $y = Read-Host "R/S"
    if ($y -match "s|S|2") {
        exit
    }
}
#>

#-- process
$reinstall = "ask"
ForEach ($task in $tasks) {
    $title, $url, $cmd, $args, $regkey, $testpath = $task;

    Write-Host ""
    Write-Host "Installing $title"
    Write-Host "------------------------"
    Write-Host ""
    chdir($TEMP);
    
    # test if element (directory/file or registry key) already exists:
    if ($reinstall -eq "all") {
    }
    elseif ($testpath -AND (Test-Path -Path $testpath)) {
        echo " → Is already present."
        if ($reinstall -eq "none") { continue }
        $y = Read-Host "   Reinstall [y/N/all/none]?"
        if ($y -match "all|always|re|A") { $reinstall = "all" }
        elseif ($y -match "never|none|skipall|S") { $reinstall = "none"; continue }
        elseif ($y -match "y|yes|1|go|R") { } # YES
        else { continue } # everything else counts as NO
    }

    # get "filename" part from url
    $file = [regex]::match($url, "/([^/]+?)([\?\#]|$)").Groups[1].Value;

    # download
    if ($url -match "https?://.+") {
        Write-Host -foregroundcolor DarkGreen  " → download( $url )"
        $wget = New-Object System.Net.WebClient
        $wget.DownloadFile($url, "$TEMP\$file");
    }

    # run shorthand or custom command
    if ($cmd) {
        chdir($PYTHON)
        if ($cmd -eq "pip") {
            $cmd = "$PYTHON\Scripts\pip.exe install $TEMP\$file"
        }
        elseif ($cmd -match "^(easy|easy_install|silent)$") {
             $cmd = "$PYTHON\Scripts\easy_install.exe $url"
        }
        Write-Host -foregroundcolor DarkYellow   " → exec( $cmd )"
        Invoke-Expression "$cmd"
    }
    # msi
    elseif ($file -match ".+.msi$") {
        write-host -foregroundcolor DarkYellow " → exec( msiexec /i $file $args )"
        Start-Process -Wait msiexec -ArgumentList /i,"$TEMP\$file",$args
        if ($regkey) { Try {
            Set-ItemProperty -Path "$regkey" -Name "WindowsInstaller"  -Value "0"
        } Catch {} }
    }
    # exe
    elseif ($file -match ".+.exe$") {
        write-host -foregroundcolor DarkYellow " → exec( $file $args )"
        if ($args) {
            Start-Process -Wait "$TEMP\$file" -ArgumentList $args
        }
        else {
            Start-Process -Wait "$TEMP\$file"
        }
    }
    # other files
    elseif ($file) {
      echo " → exec( $file )"
      & "$TEMP\$file"
    }
}


