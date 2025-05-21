# 安美智享智能医美服务系统 - 数据库UUID迁移脚本

# 脚本所在目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

# 激活虚拟环境
if (Test-Path "$projectRoot\venv\Scripts\Activate.ps1") {
    Write-Host "激活虚拟环境..." -ForegroundColor Cyan
    & "$projectRoot\venv\Scripts\Activate.ps1"
} else {
    Write-Host "警告: 未找到虚拟环境, 尝试使用系统Python环境" -ForegroundColor Yellow
}

# 显示执行步骤
Write-Host "===== 安美智享数据库UUID迁移工具 =====" -ForegroundColor Green
Write-Host "此工具将数据库主键从整数类型迁移到UUID类型" -ForegroundColor Yellow

# 执行迁移脚本
Set-Location $projectRoot
python -m scripts.migrate_to_uuid $args

# 完成
Write-Host "操作完成!" -ForegroundColor Green 