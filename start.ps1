# KrushiSetu Platform - PowerShell Server Start Script
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "           KRUSHISETU PLATFORM - STARTING SERVER                " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
$env:PYTHONPATH = "."
python run.py start $args

