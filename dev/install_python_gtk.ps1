#

# Run as post-install script for .exe package

$TEMP = $env:TEMP
$PYTHON = "C:\Python27"

#-- what
$files = @(
  "https://www.python.org/ftp/python/2.7.12/python-2.7.12.msi",
  "http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/pygtk-all-in-one-2.24.2.win32-py2.7.msi",
  "$PYTHON\Scripts\easy_install.exe requests",
  "https://pypi.python.org/packages/3d/ee/affbc53073a951541b82a0ba2a70de266580c00f94dd768a60f125b04fca/lxml-2.3.win32-py2.7.exe",
  "https://pypi.python.org/packages/62/71/8ac1f5c0251e51714d20e4b102710d5eee1683c916616129552b0a025ba5/pyquery-1.2.17-py2.py3-none-any.whl#noexec",
  "$PYTHON\Scripts\pip.exe install $TEMP\pyquery-1.2.17-py2.py3-none-any.whl",
  "http://effbot.org/downloads/PIL-1.1.7.win32-py2.7.exe"
)

#-- ask before running
Write-Host ""
Write-Host "Do you want to install Python 2.7 and Gtk dependencies now?"
Write-Host ""
Write-Host " - This will install 32-bit versions of Python and Gtk."
Write-Host " - Leave the default install path of $PYTHON for this to work."
Write-Host " - Packages will go into $TEMP"
Write-Host ""
$y = Read-Host "y/n"
if ($y -notmatch "y|Y|1") {
    exit;
}
Write-Host ""
Write-Host "Downloading packages..."

#-- process
ForEach ($url in $files) {

    echo "`n[[[ $url ]]]" #`
    chdir($TEMP);

    if ($url -match "https?://.+") {
        $file = [regex]::match($url, "/([^/]+?)([\?\#]|$)").Groups[1].Value;

        # download
        $wget = New-Object System.Net.WebClient
        $wget.DownloadFile($url, "$TEMP\$file");

        # run
        if ($url -match ".+#noexec") {
            Write-Host "(skipping)"
        }
        elseif ($url -match ".+.msi$") {
            Start-Process -Wait msiexec -ArgumentList /i,"$TEMP\$file"
        }
        elseif ($url -match ".+.exe$") {
            Start-Process -Wait "$TEMP\$file"
        }
        else {
            & "$TEMP\$file"
        }
    }
    else {
        # only run command
        chdir($PYTHON)
        Invoke-Expression "& $url"
    }
}

#-- make ST2 .lnk
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$Home\Desktop\Streamtuner2.lnk")
$Shortcut.TargetPath = "C:\Python27\pythonw.exe"
$Shortcut.Arguments = "c:\usr\bin\streamtuner2"
$Shortcut.Save()
