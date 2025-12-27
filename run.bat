@echo off
REM SPDX-License-Identifier: MIT
REM Copyright (c) 2025 Maxim Strekolovskiy
call csv_bot_env\Scripts\activate.bat
python json_to_csv_json.py
pause