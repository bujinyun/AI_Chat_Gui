@echo off
REM 使用 pyinstaller 打包 gpt4.py 为单个可执行文件
pyinstaller --onefile --noconsole gpt4.py

REM 将生成的 exe 文件移动到当前目录
move dist\gpt4.exe .

REM 删除 build 文件夹
rmdir /s /q build

REM 删除 dist 文件夹
rmdir /s /q dist

REM 删除 .spec 文件
del gpt4.spec

echo 打包完成，清理完毕！
pause