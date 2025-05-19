# 安美智享智能医美服务系统 - 数据库迁移工作流示例脚本
# 本脚本演示如何在修改模型后应用数据库迁移

# 步骤1: 检测模型变更
Write-Host "步骤1: 检测模型变更..." -ForegroundColor Green
python migration.py detect

# 步骤2: 创建迁移文件
Write-Host "`n步骤2: 创建迁移文件..." -ForegroundColor Green
$migrationMessage = Read-Host -Prompt "请输入迁移说明 (例如: '添加新字段')"
if (-not $migrationMessage) {
    $migrationMessage = "模型更新"
}
python migration.py create --message $migrationMessage

# 步骤3: 应用迁移
Write-Host "`n步骤3: 应用迁移..." -ForegroundColor Green
python migration.py upgrade

# 步骤4: 填充测试数据
Write-Host "`n步骤4: 是否需要更新测试数据?" -ForegroundColor Green
$updateTestData = Read-Host -Prompt "是否更新测试数据? (y/n)"
if ($updateTestData -eq "y" -or $updateTestData -eq "Y") {
    python seed_db.py
    Write-Host "测试数据已更新" -ForegroundColor Green
}

Write-Host "`n数据库迁移流程完成!" -ForegroundColor Green 