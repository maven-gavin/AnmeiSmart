# 安美智享自动化测试环境设置脚本 (Windows PowerShell 版本)

Write-Host "=== 安美智享自动化测试环境设置 ===" -ForegroundColor Blue
Write-Host "该脚本帮助你启动测试所需的服务" -ForegroundColor Yellow

# 验证后端API服务是否可用
function Check-ApiService {
    Write-Host "检查API服务 (端口 8000)..." -ForegroundColor Blue
    
    $apiUrl = "http://127.0.0.1:8000/api/v1/chat/health"
    
    try {
        $response = Invoke-WebRequest -Uri $apiUrl -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ API服务运行正常" -ForegroundColor Green
            return $true
        }
    }
    catch {
        Write-Host "✗ API服务不可用" -ForegroundColor Red
        return $false
    }
    
    return $false
}

# 验证前端服务是否可用
function Check-FrontendService {
    Write-Host "检查前端服务 (端口 3000)..." -ForegroundColor Blue
    
    $frontendUrl = "http://127.0.0.1:3000"
    
    try {
        $response = Invoke-WebRequest -Uri $frontendUrl -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ 前端服务运行正常" -ForegroundColor Green
            return $true
        }
    }
    catch {
        Write-Host "✗ 前端服务不可用" -ForegroundColor Red
        return $false
    }
    
    return $false
}

# 启动后端API服务
function Start-ApiService {
    Write-Host "启动API服务..." -ForegroundColor Blue
    
    # 获取当前路径
    $currentPath = Get-Location
    $apiPath = Join-Path -Path (Split-Path -Path (Split-Path -Path (Split-Path -Path $currentPath -Parent) -Parent) -Parent) -ChildPath "api"
    
    # 启动API服务
    try {
        Start-Process -FilePath "powershell" -ArgumentList "-Command `"cd '$apiPath'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`"" -WindowStyle Normal
        
        Write-Host "等待API服务启动..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        
        if (Check-ApiService) {
            Write-Host "API服务已成功启动" -ForegroundColor Green
        }
        else {
            Write-Host "API服务启动失败，请手动检查" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "启动API服务时出错: $_" -ForegroundColor Red
    }
}

# 启动前端服务
function Start-FrontendService {
    Write-Host "启动前端服务..." -ForegroundColor Blue
    
    # 获取当前路径
    $currentPath = Get-Location
    $webPath = Join-Path -Path (Split-Path -Path (Split-Path -Path (Split-Path -Path $currentPath -Parent) -Parent) -Parent) -ChildPath "web"
    
    # 启动前端服务
    try {
        Start-Process -FilePath "powershell" -ArgumentList "-Command `"cd '$webPath'; npm run dev`"" -WindowStyle Normal
        
        Write-Host "等待前端服务启动..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        
        if (Check-FrontendService) {
            Write-Host "前端服务已成功启动" -ForegroundColor Green
        }
        else {
            Write-Host "前端服务启动失败，请手动检查" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "启动前端服务时出错: $_" -ForegroundColor Red
    }
}

# 运行测试
function Run-Tests {
    Write-Host "运行端到端测试..." -ForegroundColor Blue
    
    # 获取当前路径
    $currentPath = Get-Location
    $webPath = Join-Path -Path (Split-Path -Path (Split-Path -Path (Split-Path -Path $currentPath -Parent) -Parent) -Parent) -ChildPath "web"
    
    # 运行测试
    try {
        Set-Location -Path $webPath
        npx playwright test
    }
    catch {
        Write-Host "运行测试时出错: $_" -ForegroundColor Red
    }
    finally {
        Set-Location -Path $currentPath
    }
}

# 检查服务状态
$apiRunning = Check-ApiService
$frontendRunning = Check-FrontendService

# 启动缺少的服务
if (-not $apiRunning) {
    Write-Host "API服务未运行，尝试启动..." -ForegroundColor Yellow
    Start-ApiService
}

if (-not $frontendRunning) {
    Write-Host "前端服务未运行，尝试启动..." -ForegroundColor Yellow
    Start-FrontendService
}

# 最终检查
Write-Host "最终检查服务状态..." -ForegroundColor Blue
$apiOk = Check-ApiService
$frontendOk = Check-FrontendService

# 如果服务都运行正常，运行测试
if ($apiOk -and $frontendOk) {
    Write-Host "所有服务运行正常，准备开始测试" -ForegroundColor Green
    
    # 询问用户是否运行测试
    $answer = Read-Host "是否运行测试? (Y/N)"
    if ($answer -eq "Y" -or $answer -eq "y") {
        Run-Tests
    }
    else {
        Write-Host "测试已取消" -ForegroundColor Yellow
    }
}
else {
    Write-Host "部分服务未能正常启动，无法执行测试" -ForegroundColor Red
    Write-Host "请尝试手动启动服务:" -ForegroundColor Yellow
    Write-Host "1. 启动API服务: cd api; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000" -ForegroundColor Yellow
    Write-Host "2. 启动前端服务: cd web; npm run dev" -ForegroundColor Yellow
    Write-Host "3. 运行测试: cd web; npx playwright test" -ForegroundColor Yellow
} 