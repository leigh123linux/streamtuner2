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


# default paths
$TEMP = $env:TEMP
$PYTHON = "C:\Python27"
$OutputEncoding = [System.Text.Encoding]::UTF8
$StartMenu = "$env:USERPROFILE\AppData\Roaming\Microsoft\Windows\Start Menu\Programs"
$UsrFolder = $MyInvocation.MyCommand.Path -replace "([\\/][^\\/]+){4}$",""
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
    "TARGETDIR=C:\Python27 /qb",                                      # msi args
    "$regPathLM\{9DA28CE5-0AA5-429E-86D8-686ED898C665}",              # registry
    "$regPathLM\{9DA28CE5-0AA5-429E-86D8-686ED898C665}"               # installed check
  ),
  @(
    "PyGtk 2.24.2",
    "http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/pygtk-all-in-one-2.24.2.win32-py2.7.msi",
    "",
    "TARGETDIR=C:\Python27 ADDLOCAL=ALL REMOVE=PythonExtensionModulePyGtkSourceview2,PythonExtensionModulePyGoocanvas,PythonExtensionModulePyRsvg,DevelopmentTools /qb",
    "$regPathLM\{09F82967-D26B-48AC-830E-33191EC177C8}",
    "$regPathLM\{09F82967-D26B-48AC-830E-33191EC177C8}"
  ),
  @(
    "Python requests 2.12.1",
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
    "$PYTHON\Lib\site-packages\PIL"
  ),
  @(
    "ST2 relocatable start script patch",
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
    "FINISHED", "", '$true', "", "", ""
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
        $lnk.Arguments = """"$arg""""
        $lnk.IconLocation = "$UsrFolder\share\pixmaps\streamtuner2.ico"
        $lnk.WorkingDirectory = "$UsrFolder\bin"
    }
    $lnk.Save()
}


#-- modify ST2 wrapper script
function Rewrite-Startscript {
    [CmdletBinding()]
    param()
    $WrapperScript = Get-Content -Path "$UsrFolder\bin\streamtuner2"
    for ($i=0; $i -lt $WrapperScript.Length ; $i++) {
        $WrapperScript[$i] = $WrapperScript[$i].Replace("sys.path.insert(0, " + """" + "/usr/","sys.path.insert(0, " + """" + $UsrFolder)
        Out-File -FilePath "$UsrFolder\bin\streamtuner2.new" -Encoding ascii -Append -InputObject $WrapperScript[$i]
    }

    if (Test-Path -Path "$UsrFolder\bin\streamtuner2.bak") {
        Remove-Item -Path "$UsrFolder\bin\streamtuner2.bak" -Force
    }
    Rename-Item -NewName "streamtuner2.bak" -Path "$UsrFolder\bin\streamtuner2" #save old script
    Rename-Item -NewName "streamtuner2" -Path "$UsrFolder\bin\streamtuner2.new"
    Set-Acl "$UsrFolder\bin\streamtuner2" (Get-Acl "$UsrFolder\bin\streamtuner2.bak") # set file permissions 
}

#-- admin check
function Test-IsElevated {
    [CmdletBinding()]
    param()
    [Security.Principal.WindowsPrincipal] $Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $Identity.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

#-- check prereqs installation
function Check-Prerequisites {
    [CmdletBinding()]
    param()
    Check-Package
    $result = 1
    ForEach ($task in $tasks) {
        $title, $url, $cmd, $args, $regkey, $check = $task;
        if ($regkey) { 
            if (!(Test-Path -Path $regkey)) {     # avoid runtime error if not existent (not working in PS1)
                Write-Host "   - $title not found"
                $result = 0
            }
            else {
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
        Write-Host -f Green "`nAll required Python components are already installed. You can use 'none' or 'skip' or 'S' to skip them. Or just press ENTER on each following prompt. If you want to reinstall them though, use 'all' or 'reinstall' or 'R'.`n"
    }
}

#-- ensure ST2 startup script exists in relative path to this install script
function Check-Package {
    if (!(Test-Path -Path("$UsrFolder\bin\streamtuner2"))) {
        Write-Host -b DarkRed -f White @"
The Streamtuner2 start script could not be found. The installation cannot continue.
Please do not change the folder structure of the Streamtuner2 package!

[Press any key to exit ...]
"@
        $null = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit;
    }
}


#-- ask before running
Write-Host -f White -b Blue @"
–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
Do you want to install Python 2.7 and Gtk dependencies now?
–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
"@
if(!(Test-IsElevated)) {
    Write-Host -f red @"
/---------------------------------------------------------------------------\
| (!)  Since you run this script in non-elevated mode you will not be able  |
|      to uninstall Python and Gtk using the control panels´ software list. |
\---------------------------------------------------------------------------/
"@
}
if ((Read-Host "[Y/n]") -notmatch "[yYi123ar]|^$") {
    exit;
}


#-- process
$reinstall = "ask"
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
        echo " → Is already present."
        if ($reinstall -eq "none") { continue }
        $y = Read-Host "   Reinstall [y/N/all/none]?"
        if ($y -match "^all|always|re|^A") { $reinstall = "all" }
        elseif ($y -match "never|none|skip|^S") { $reinstall = "none"; continue }
        elseif ($y -match "^y|yes|1|go|^R") { } # YES
        else { continue } # everything else counts as NO
    }

    # get "filename" part from url
    $file = [regex]::match($url, "/([^/]+?)([\?\#]|$)").Groups[1].Value;

    # download
    if ($url -match "https?://.+") {
        Write-Host -f DarkGreen  " ← $url"
        $wget = New-Object System.Net.WebClient
        $wget.DownloadFile($url, "$TEMP\$file");
    }

    # run shorthand or custom command
    if ($cmd) {
        if (Test-Path $PYTHON) { chdir($PYTHON) }
        if ($cmd -eq "pip") {
            $cmd = "& $PYTHON\Scripts\pip.exe install $TEMP\$file"
        }
        elseif ($cmd -match "^(easy|easy_install|silent)$") {
             $cmd = "& $PYTHON\Scripts\easy_install.exe $url"
        }
        Write-Host -f DarkYellow   " → $cmd"
        Invoke-Expression "$cmd"
    }
    # msi
    elseif ($file -match ".+.msi$") {
        write-host -f DarkYellow " → msiexec /i $file $args"
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


