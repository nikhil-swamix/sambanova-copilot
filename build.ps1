poetry shell
pyinstaller copilot.py --windowed --onefile --icon="./assets/favicon.ico" --add-data ".env:." --add-data "utils.py:." --add-data "assets:assets"   --noconfirm --exclude-module tkinter --exclude-module PIL --exclude-module _tkinter --upx-dir C:\Users\User\Downloads\upx-4.2.4-win64\upx-4.2.4-win64
# pyinstaller vdb.py  --onefile --icon="../assets/favicon.ico"    --noconfirm --exclude-module tkinter --exclude-module PIL --exclude-module _tkinter --upx-dir C:\Users\User\Downloads\upx-4.2.4-win64\upx-4.2.4-win64
