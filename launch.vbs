Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
WshShell.CurrentDirectory = FSO.GetParentFolderName(WScript.ScriptFullName)
WshShell.Run "pythonw.exe main.py", 0, False
WScript.Sleep 2000
Set proc = GetObject("winmgmts:\\.\root\cimv2").ExecQuery("SELECT * FROM Win32_Process WHERE Name='pythonw.exe'")
If proc.Count = 0 Then
    WshShell.Run "python main.py", 1, False
End If
