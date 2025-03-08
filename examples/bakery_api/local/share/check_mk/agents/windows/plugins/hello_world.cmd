@echo off
set /a rand=(%random%*100/32768)
echo ^<^<^<^hello_bakery^>^>^>
echo hello_bakery %rand%.5
