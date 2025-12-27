@echo off
REM SPDX-License-Identifier: MIT
REM Copyright (c) 2025 Maxim Strekolovskiy
call csv_bot_env\Scripts\activate.bat
pyinstaller --onefile --name JivoAnalyticsBot ^
--hidden-import=anyio._core._eventloop ^
--hidden-import=anyio.streams ^
json_to_csv_json.py
pause