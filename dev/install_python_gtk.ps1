<#
 #
 # Run as post-install script for .exe package
 #
 #  - downloads Python + Gtk
 #  - some python libraries
 #  - and runs their respective installers
 #  - crafts streamtuner2 desktop shortcut
 #
 #>

[CmdletBinding()]            
Param(            
)            

# admin check            
function Test-IsElevated {
    [CmdletBinding()]
    param(
    )
    [Security.Principal.WindowsPrincipal] $Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $Identity.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}


# default paths
$TEMP = $env:TEMP
$PYTHON = "C:\Python27"
$OutputEncoding = [System.Text.Encoding]::UTF8

#-- what and how to install
#   each row is a list of (title,url,cmd,msi args,regkey)
$tasks = @(
  @(
    "Python 2.7.12",                                                  # title
    "https://www.python.org/ftp/python/2.7.12/python-2.7.12.msi",     # url
    "",                                                               # custom cmd
    "/qb",                                                            # msi args
    "{9DA28CE5-0AA5-429E-86D8-686ED898C665}"                          # registry
  ),
  @(
    "PyGtk 2.24.2",
    "http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/pygtk-all-in-one-2.24.2.win32-py2.7.msi",
    "",
    "TARGETDIR=C:\Python27 ADDLOCAL=ALL REMOVE=PythonExtensionModulePyGtkSourceview2,PythonExtensionModulePyGoocanvas,PythonExtensionModulePyRsvg,DevelopmentTools /qb",
    "{09F82967-D26B-48AC-830E-33191EC177C8}"
  ),
  @(
    "Python requests",
    "requests", # no download url, pip handles this
    "pip",
    "",
    ""
  ),
  @(
    "LXML 2.3",
    "https://pypi.python.org/packages/3d/ee/affbc53073a951541b82a0ba2a70de266580c00f94dd768a60f125b04fca/lxml-2.3.win32-py2.7.exe",
    "easy_install",
    "",
    ""
  ),
  @(
    "PyQuery 1.2.1",
    "https://pypi.python.org/packages/62/71/8ac1f5c0251e51714d20e4b102710d5eee1683c916616129552b0a025ba5/pyquery-1.2.17-py2.py3-none-any.whl",
    "easy_install",
    "",
    ""
  ),
  @(
    "PIL 1.1.7",
    "http://effbot.org/downloads/PIL-1.1.7.win32-py2.7.exe",
    "easy_install",
    "",
    ""
  )
)

# prepare registry lookup
$regPath = "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
if(!(Test-Path $regPath)) {
    $regPath = "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall"
}

#-- ask before running
Write-Host ""
Write-Host "Do you want to install Python 2.7 and Gtk dependencies now?"
Write-Host "–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––"
Write-Host " → This will install 32-bit versions of Python and Gtk."
Write-Host " → Downloads will remain in $TEMP"
if(!(Test-IsElevated)) {
    Write-Host -foregroundcolor red "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
    Write-Host -foregroundcolor red "┃ ⚠ ⛔  If you run this script in non-elevated mode you will not be able to  ┃"
    Write-Host -foregroundcolor red "┃      uninstall Python and Gtk using the control panels´ software list.    ┃"
    Write-Host -foregroundcolor red "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
}
Write-Host ""
$y = Read-Host "y/n"
if ($y -notmatch "y|Y|1") {
    exit;
}
Write-Host ""

#-- process
ForEach ($task in $tasks) {
    $title, $url, $cmd, $args, $regkey = $task;

    echo ""
    echo "Installing $title"
    echo "------------------------"
    echo ""
    chdir($TEMP);


    # get "filename" part from url
    $file = [regex]::match($url, "/([^/]+?)([\?\#]|$)").Groups[1].Value;

    # download
    if ($url -match "https?://.+") {
        echo " → download( $url )"
        $wget = New-Object System.Net.WebClient
        $wget.DownloadFile($url, "$TEMP\$file");
    }

    # run shorthand or custom command
    if ($cmd) {
        chdir($PYTHON)
        if ($cmd -eq "pip") {
            $cmd = "$PYTHON\Scripts\pip.exe install $url"
        }
        elseif ($cmd -match "^(easy|easy_install|silent)$") {
            $cmd = "$PYTHON\Scripts\easy_install.exe $TEMP\$file"
        }
        echo " → exec( $cmd )"
        Invoke-Expression "& $cmd"
    }
    # msi
    elseif ($file -match ".+.msi$") {
        echo " → exec( msiexec /i $file $args )"
        Start-Process -Wait msiexec -ArgumentList /i,"$TEMP\$file",$args
        if ($regkey) { Try {
           Set-ItemProperty -Path "$regPath\$regkey" -Name "WindowsInstaller"  -Value "0"
        } Catch {} }
    }
    # exe
    elseif ($file -match ".+.exe$") {
        echo " → exec( $file $args )"
        if ($args) {
            Start-Process -Wait "$TEMP\$file" -ArgumentList $args
        }
        else {
            Start-Process -Wait "$TEMP\$file"
        }
    }
    # other files
    else {
        echo " → exec( $file )"
        & "$TEMP\$file"
    }
}

#-- make ST2 .lnk
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$Home\Desktop\Streamtuner2.lnk")
$Shortcut.TargetPath = "$PYTHON\pythonw.exe"
$Shortcut.Arguments = "c:\usr\bin\streamtuner2"
$Shortcut.Save()

