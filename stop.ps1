# KrushiSetu Platform - PowerShell Server Stop Script
Write-Host "================================================================" -ForegroundColor Yellow
Write-Host "           KRUSHISETU PLATFORM - STOPPING SERVER                " -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Yellow
$env:PYTHONPATH = "."
python run.py stop $args

