@echo off
echo Installing dependencies...
python -m pip install -r requirements.txt
echo.
echo Done! You can now run: python test_api_only.py
pause
