Write-Host "Installing dependencies..." -ForegroundColor Green
python -m pip install -r requirements.txt
Write-Host "`nDone! You can now run: python test_api_only.py" -ForegroundColor Green
Read-Host "Press Enter to exit"
