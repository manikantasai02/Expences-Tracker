Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "py backend\server.py 5000", 0, False
WshShell.Run "http://localhost:5000", 1, False
Set WshShell = Nothing
