@echo off
REM SPDX-License-Identifier: MIT
REM Copyright (c) 2025 Maxim Strekolovskiy
python -m venv csv_bot_env
call csv_bot_env\Scripts\activate.bat
pip install -r requirements.txt
echo Installation completed!
pause