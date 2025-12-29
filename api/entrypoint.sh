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
    # 使用 Python 直接测试数据库连接，而不是 alembic current（因为 alembic 会检查版本号）
    retry_count=0
    while [ $retry_count -lt $MAX_RETRIES ]; do
        # 使用 Python 测试数据库连接（不依赖 alembic 版本检查）
        if python -c "
import os
import sys
try:
    import psycopg2
    from urllib.parse import urlparse
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        sys.exit(1)
    parsed = urlparse(db_url)
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.strip('/'),
        connect_timeout=5
    )
    conn.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; then
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
    
    # 检查当前版本（如果可能）
    echo "🔍 检查数据库迁移版本..."
    current_output=$(alembic current 2>&1)
    version_mismatch=false
    
    if echo "$current_output" | grep -q "Can't locate revision"; then
        current_version=$(echo "$current_output" | grep -oP "identified by '\K[^']+")
        echo "⚠️  警告: 数据库版本 $current_version 不在当前迁移链中"
        echo "   这可能是由于迁移文件不同步导致的"
        version_mismatch=true
        
        # 获取迁移链的起始版本
        first_revision=$(alembic history | tail -1 | awk '{print $1}')
        echo "   当前迁移链起始版本: $first_revision"
        echo ""
        echo "   解决方案选项:"
        echo "   1. 如果数据库结构已经是最新的，可以 stamp 到 head:"
        echo "      alembic stamp head"
        echo "   2. 如果需要从迁移链起始版本开始，可以 stamp 到:"
        echo "      alembic stamp $first_revision"
        echo "   3. 或者联系开发团队获取帮助"
        echo ""
        echo "   将尝试直接升级（可能会失败）..."
    elif echo "$current_output" | grep -q "version_num"; then
        current_version=$(echo "$current_output" | grep "version_num" | awk '{print $NF}')
        echo "📌 当前数据库版本: $current_version"
    else
        echo "ℹ️  无法确定当前数据库版本，将尝试直接升级..."
    fi
    
    # 执行迁移
    echo "📦 执行数据库迁移..."
    migration_output=$(alembic upgrade head 2>&1)
    migration_exit_code=$?
    
    if [ $migration_exit_code -eq 0 ]; then
        echo "✅ 数据库迁移完成"
    else
        echo "❌ 数据库迁移失败"
        echo ""
        echo "错误详情:"
        echo "$migration_output" | tail -20
        echo ""
        
        if [ "$version_mismatch" = true ]; then
            echo "检测到版本不匹配问题。请按照上面的建议处理版本号后重试。"
        else
            echo "可能的原因:"
            echo "   1. 数据库版本与迁移文件不匹配"
            echo "   2. 迁移文件缺失或损坏"
            echo "   3. 数据库结构冲突"
            echo ""
            echo "建议解决方案:"
            echo "   1. 检查迁移文件是否完整"
            echo "   2. 如果数据库版本不在迁移链中，可能需要手动处理版本号"
            echo "   3. 联系开发团队获取帮助"
        fi
        exit 1
    fi
fi

echo "🚀 启动应用..."
exec "$@"

