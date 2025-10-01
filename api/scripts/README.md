# 安美智享智能医美服务系统 - 数据库管理脚本

本目录包含用于管理数据库的各种脚本，包括初始化、迁移、测试数据填充等功能。

## 脚本概览

| 脚本名称         | 描述                                               |
| ---------------- | -------------------------------------------------- |
| `init_db.py`   | 初始化数据库表结构和基本系统数据（不包含测试数据） |
| `migration.py` | 数据库迁移管理工具，用于创建和应用数据库结构变更   |
| `seed_db.py`   | 填充测试数据，用于开发和测试环境                   |
| `setup_db.py`  | 数据库连接和配置设置                               |
| `setup_all.py` | 一键配置整个系统环境                               |

## 数据库迁移流程

1. 当你修改 `app/db/models/` 目录下的模型文件时，需要创建数据库迁移
2. 使用 `migration.py` 脚本检测变更并创建迁移文件
3. 应用迁移更新数据库结构
4. 如果需要测试数据，使用 `seed_db.py` 填充

## 详细使用指南

### 初始化数据库 (init_db.py)

此脚本用于首次创建数据库表和初始化系统所需的基本数据。

```bash
# 基本用法
python .\scripts\init_db.py

# 强制重新创建所有表（慎用，会删除现有数据）
python .\scripts\init_db.py --drop-all

# 仅应用迁移，不初始化数据
python .\scripts\init_db.py --migrate-only

# 不使用迁移系统，直接创建表
python .\scripts\init_db.py --no-migrations
```

### 数据库迁移管理 (migration.py)

此脚本用于管理数据库结构变更。当您修改模型文件后，应该使用此脚本创建和应用迁移。

```bash
# 检测数据库模型变更
python .\scripts\migration.py detect

# 创建新的迁移（自动检测变更）
python .\scripts\migration.py create --message "添加新字段"

# 手动创建迁移（不自动检测）
python .\scripts\migration.py create --message "自定义迁移" --manual

# 应用迁移到最新版本
python .\scripts\migration.py upgrade

# 回滚到指定版本
python .\scripts\migration.py downgrade --revision 1a2b3c4d

# 显示迁移历史
python .\scripts\migration.py history
```

### 填充测试数据 (seed_db.py)

此脚本用于填充测试数据，适用于开发和测试环境。

```bash
# 基本用法
python .\scripts\seed_db.py

# 强制更新现有测试数据
python .\scripts\seed_db.py --force

# 清除现有测试数据后重新创建
python .\scripts\seed_db.py --clean
```

## 工作流程指南

### 1. 首次初始化数据库

```bash
# 创建表结构和基本数据
python .\scripts\init_db.py
```

### 2. 修改数据库模型后的流程

```bash
# 1. 检测模型变更
python .\scripts\migration.py detect

# 2. 创建迁移
python .\scripts\migration.py create --message "变更描述"

# 3. 应用迁移
python .\scripts\migration.py upgrade

# 4. (可选) 更新测试数据
python .\scripts\seed_db.py
```

### 3. 重置测试环境

```bash
# 1. 重新创建表结构
python .\scripts\init_db.py --drop-all

# 2. 添加测试数据
python .\scripts\seed_db.py
```

## 数据库设计原则

- `app/db/models/` 目录下的模型文件是数据库结构的唯一真实来源
- 所有数据库结构变更都应通过模型文件修改和迁移脚本来实现
- 系统基础数据通过 `init_db.py` 初始化
- 测试和示例数据通过 `seed_db.py` 填充
- 在开发和生产环境中，始终优先使用迁移系统而非直接创建表

## 注意事项

1. 在生产环境中，使用 `--force` 参数前请务必备份数据
2. 迁移文件一经提交到版本控制系统，不应再修改其内容
3. 如果迁移过程中出现错误，请先回滚到稳定版本再尝试修复
4. 测试数据脚本不应在生产环境中使用

## 最佳实践

1. **版本控制迁移文件**：所有迁移文件都应纳入版本控制系统
2. **单一职责原则**：每个迁移文件只处理一个逻辑变更
3. **向后兼容**：尽量设计向后兼容的迁移，避免破坏性变更
4. **测试迁移**：在应用到生产环境前，先在测试环境验证迁移
5. **记录文档**：对复杂迁移添加详细注释和文档说明
6. **检查自动生成的迁移**：始终检查自动生成的迁移文件，尤其是首次生成的迁移可能会错误地标记要删除现有表

## 常见问题及解决方案

### 常见错误

1. **"'Connection' object has no attribute 'as_sql'"**

   - 原因：Alembic 版本兼容性问题
   - 解决方案：已在新版本的 `migration.py` 中修复，使用 `MigrationContext` 直接配置连接
2. **"Found legacy 'flask' directory"**

   - 原因：之前使用 Flask 的 SQLAlchemy 扩展，现在使用原生 SQLAlchemy
   - 解决方案：检查是否仍有 Flask 相关的导入，确保使用原生 SQLAlchemy API
3. **"No such revision"**

   - 原因：迁移历史中不存在指定的版本号
   - 解决方案：使用 `python migration.py history` 查看正确的版本号
4. **"Table already exists"**

   - 原因：尝试创建已经存在的表
   - 解决方案：
     * 使用 `--force` 参数重新创建表
     * 或者编辑迁移文件，移除已存在表的创建语句
5. **"Target database is not up to date"**

   - 原因：尝试在未应用所有迁移的数据库上创建新迁移
   - 解决方案：先运行 `python migration.py upgrade` 更新数据库
6. **中文编码问题**

   - 原因：文件编码与系统默认编码不匹配
   - 解决方案：
     * 确保所有Python文件使用UTF-8编码
     * 使用 `with open(file_path, 'r', encoding='utf-8')` 方式打开文件

### 首次迁移问题

首次使用自动迁移时可能遇到以下问题：

1. **自动迁移检测不到表结构变更**

   - 原因：`env.py` 文件未正确配置
   - 解决方案：检查 `env.py` 中的 `target_metadata` 是否指向 `Base.metadata`
2. **迁移文件标记删除现有表**

   - 原因：首次迁移时，Alembic 不知道已有的表是期望的结构
   - 解决方案：编辑迁移文件，删除所有 `op.drop_table` 语句和相关的索引删除语句
3. **模型导入错误**

   - 原因：迁移过程中无法找到模型定义
   - 解决方案：确保 `__init__.py` 文件导入了所有模型，并且在 `env.py` 中正确导入了模型包

### 进阶问题解决

对于更复杂的迁移场景：

1. **需要添加数据迁移**

   - 使用 `op.bulk_insert` 和 `op.execute` 在迁移中添加数据转换逻辑
2. **需要更改表名或列名**

   - 检查生成的迁移是否正确捕获了修改意图
   - 可能需要手动编写迁移内容
3. **处理外键约束**

   - 迁移中可能需要暂时禁用外键约束: `op.execute("SET CONSTRAINTS ALL DEFERRED")`
   - 操作完成后重新启用: `op.execute("SET CONSTRAINTS ALL IMMEDIATE")`

## 其他脚本

此外，还有一些辅助脚本：

- **setup.py**: 安装指南脚本

## 注意事项

### Windows系统特殊考虑

在Windows系统上使用这些脚本时，需要特别注意：

1. 所有Python文件都应使用UTF-8编码保存
2. 在读写文件时，始终指定 `encoding="utf-8"`参数
3. 如果遇到编码相关错误，检查相关文件的编码是否正确
4. 使用命令行运行脚本时，建议使用PowerShell而非CMD

### 首次迁移时的特别注意事项

第一次创建迁移时，Alembic会比较数据库当前状态与模型定义，通常会导致以下情况：

1. 如果数据库为空：生成创建所有表的迁移
2. 如果数据库已有表但Alembic没有迁移历史：错误地将现有表标记为"需要删除"

在第二种情况下，应当：

1. 仔细检查生成的迁移文件
2. 删除或注释掉所有 `drop_table` 相关语句
3. 保留添加新表或字段的语句
4. 根据实际需求调整迁移文件内容
