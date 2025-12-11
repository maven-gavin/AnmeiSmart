#!/bin/bash
set -e

# 数据库迁移配置
MAX_RETRIES=${DB_MIGRATION_MAX_RETRIES:-30}
RETRY_INTERVAL=${DB_MIGRATION_RETRY_INTERVAL:-2}
SKIP_MIGRATION=${SKIP_DB_MIGRATION:-false}

if [ "$SKIP_MIGRATION" = "true" ]; then
    echo "⚠️  跳过数据库迁移 (SKIP_DB_MIGRATION=true)"
else
    echo "🔄 开始执行数据库迁移..."
    echo "📊 数据库连接: ${DATABASE_URL:-未设置}"
    
    # 重试机制：等待数据库可用
    retry_count=0
    while [ $retry_count -lt $MAX_RETRIES ]; do
        if alembic current >/dev/null 2>&1; then
            echo "✅ 数据库连接成功"
            break
        fi
        
        retry_count=$((retry_count + 1))
        if [ $retry_count -lt $MAX_RETRIES ]; then
            echo "⏳ 等待数据库连接... (${retry_count}/${MAX_RETRIES})"
            sleep $RETRY_INTERVAL
        fi
    done
    
    if [ $retry_count -eq $MAX_RETRIES ]; then
        echo "❌ 错误: 无法连接到数据库"
        echo "   请检查以下配置:"
        echo "   1. DATABASE_URL 是否正确设置"
        echo "   2. 数据库服务是否正在运行"
        echo "   3. 网络连接是否正常"
        echo "   4. 如果数据库在宿主机，请使用宿主机IP而不是 localhost"
        echo ""
        echo "   提示: 在 Docker 容器中，'localhost' 指向容器自身"
        echo "   如果数据库在宿主机，请使用: postgresql://user:pass@host.docker.internal:5432/db"
        echo "   或使用宿主机IP: postgresql://user:pass@<宿主机IP>:5432/db"
        exit 1
    fi
    
    # 执行迁移
    echo "📦 执行数据库迁移..."
    if alembic upgrade head; then
        echo "✅ 数据库迁移完成"
    else
        echo "❌ 数据库迁移失败"
        exit 1
    fi
fi

echo "🚀 启动应用..."
exec "$@"

