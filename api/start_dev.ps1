# 启动虚拟环境
# 请根据您的实际虚拟环境路径调整此部分
$VenvPath = "..\venv"
if (Test-Path $VenvPath) {
    # 激活虚拟环境
    & "$VenvPath\Scripts\Activate.ps1"
    
    Write-Host "虚拟环境已激活" -ForegroundColor Green
    
    # 运行开发服务器
    Write-Host "启动开发服务器..." -ForegroundColor Cyan
    python run_dev.py
} else {
    Write-Host "错误: 虚拟环境不存在于路径 $VenvPath" -ForegroundColor Red
    
    # 提示创建虚拟环境
    Write-Host "请先创建并激活虚拟环境，然后安装依赖:" -ForegroundColor Yellow
    Write-Host "python -m venv venv" -ForegroundColor Yellow
    Write-Host ".\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "pip install -r requirements.txt" -ForegroundColor Yellow
} 