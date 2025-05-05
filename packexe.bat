@echo off
nuitka ^
  --onefile ^
  --standalone ^
  --lto=yes ^
  --enable-plugin=tk-inter ^
  --windows-console-mode=disable ^
  --remove-output ^
  --windows-product-version=1.1.0 ^
  --windows-file-version=1.1.0 ^
  --windows-company-name="Zhiqian Yu" ^
  --windows-product-name="Multi Stage Timer" ^
  --windows-file-description="多阶段随机提醒计时器" ^
  --nofollow-import-to=tkinter.test,email,http ^
  "Multi Stage Random Notification Timer.py"
pause
