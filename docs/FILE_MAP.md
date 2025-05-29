# 项目文件结构映射

## 文档作用与约束

* 该文件索引了..\api, ..\web, ..\scripts, ..\docs 目录下的所有文件
* 每完成一些任务，就请更新该文档，保证该文档与项目文件同步
* 每次更新该文件内容时，不要修改此文档作用与约束

## API接口

- `..\api\app\api\v1\api.py`

  - 用途：API路由注册与配置
- `..\api\app\api\v1\endpoints\auth.py`

  - 用途：用户认证与登录接口
- `..\api\app\api\v1\endpoints\users.py`

  - 用途：用户管理接口（创建、查询、更新）
- `..\api\app\core\config.py`

  - 用途：应用配置管理
- `..\api\app\core\security.py`

  - 用途：安全相关功能（JWT、密码加密）
- `..\api\app\db\base.py`

  - 用途：数据库连接与会话管理
- `..\api\app\db\init_db.py`

  - 用途：数据库初始化脚本
- `..\api\app\db\models\user.py`

  - 用途：用户数据库模型定义
- `..\api\app\schemas\token.py`

  - 用途：Token数据模型
- `..\api\app\schemas\user.py`

  - 用途：用户数据模型（Pydantic模型）
- `..\api\main.py`

  - 用途：FastAPI应用入口

## 前端组件

- `..\web\src\app\consultant\chat\page.tsx`
  - 用途：顾问聊天页面
- `..\web\src\app\components\Todo.tsx`
  - 用途：待办事项组件
- `..\web\src\app\layout.tsx`
  - 用途：应用布局定义
- `..\web\src\app\page.tsx`
  - 用途：首页组件
- `..\web\src\app\access-denied\page.tsx`
  - 用途：访问拒绝页面
- `..\web\src\app\customer\page.tsx`
  - 用途：顾客端首页
- `..\web\src\app\customer\layout.tsx`
  - 用途：顾客端布局
- `..\web\src\app\customer\profile\page.tsx`
  - 用途：顾客端个人中心页面
- `..\web\src\app\customer\chat\page.tsx`
  - 用途：顾客端在线咨询页面
- `..\web\src\app\customer\appointments\page.tsx`
  - 用途：顾客端预约管理页面
- `..\web\src\app\customer\treatments\page.tsx`
  - 用途：顾客端治疗记录页面
- `..\web\src\app\customer\plans\page.tsx`
  - 用途：顾客端治疗方案页面
- `..\web\src\app\doctor\page.tsx`
  - 用途：医生端首页
- `..\web\src\app\doctor\layout.tsx`
  - 用途：医生端布局
- `..\web\src\app\doctor\plans\page.tsx`
  - 用途：医生端治疗方案列表页面
- `..\web\src\app\doctor\plans\create\page.tsx`
  - 用途：医生端治疗方案录入页面
- `..\web\src\app\login\page.tsx`
  - 用途：登录页面
- `..\web\src\app\admin\page.tsx`
  - 用途：管理员端首页
- `..\web\src\app\admin\users\page.tsx`
  - 用途：用户管理页面
- `..\web\src\app\admin\roles\page.tsx`
  - 用途：角色管理页面
- `..\web\src\components\auth\LoginForm.tsx`
  - 用途：登录表单组件
- `..\web\src\components\auth\ProtectedRoute.tsx`
  - 用途：受保护路由组件
- `..\web\src\components\chat\ChatLayout.tsx`
  - 用途：聊天界面布局
- `..\web\src\components\chat\ChatWindow.tsx`
  - 用途：聊天窗口组件
- `..\web\src\components\chat\ConversationList.tsx`
  - 用途：会话列表组件
- `..\web\src\components\chat\CustomerProfile.tsx`
  - 用途：客户资料组件
- `..\web\src\components\chat\UserInfoBar.tsx`
  - 用途：用户信息栏组件
- `..\web\src\components\ui\button.tsx`
  - 用途：通用按钮组件
- `..\web\src\components\ui\LoadingSpinner.tsx`
  - 用途：加载动画组件
- `..\web\src\components\ui\RoleSelector.tsx`
  - 用途：角色选择器组件
- `..\web\src\components\ui\consultantNavigation.tsx`
  - 用途：顾问导航组件
- `..\web\src\components\layout\RoleHeader.tsx`
  - 用途：角色头部导航组件
- `..\web\src\app\consultant\page.tsx`
  - 用途：顾问端首页（聚合导航与入口）
- `..\web\src\app\consultant\consultantClientPage.tsx`
  - 用途：顾问端首页Client组件，展示主要功能入口卡片
- `..\web\src\app\consultant\plan\page.tsx`
  - 用途：顾问端-个性化方案推荐页面
- `..\web\src\app\consultant\plan\PlanPageClient.tsx`
  - 用途：顾问端-个性化方案推荐Client组件
- `..\web\src\app\consultant\simulation\page.tsx`
  - 用途：顾问端-术前模拟页面
- `..\web\src\app\consultant\simulation\SimulationPageClient.tsx`
  - 用途：顾问端-术前模拟Client组件
- `..\web\src\app\consultant\chat\page.tsx`
  - 用途：顾问端-智能客服页面
- `..\web\src\app\consultant\chat\ChatPageClient.tsx`
  - 用途：顾问端-智能客服Client组件

## 工具和类型

- `..\web\src\service\utils.ts`
  - 用途：通用工具函数
- `..\web\src\service\authService.ts`
  - 用途：认证服务
- `..\web\src\service\customerService.ts`
  - 用途：顾客服务接口
- `..\web\src\service\doctorService.ts`
  - 用途：医生服务接口
- `..\web\src\service\chatService.ts`
  - 用途：聊天服务接口
- `..\web\src\service\mockData.ts`
  - 用途：模拟数据
- `..\web\src\service\apiClient.ts`
  - 用途：API客户端，处理认证和请求拦截
- `..\web\src\service\consultantService.ts`
  - 用途：顾问服务接口
- `..\web\src\service\customerMockData.ts`
  - 用途：顾客端模拟数据
- `..\web\src\contexts\AuthContext.tsx`
  - 用途：全局认证状态管理
- `..\web\src\types\chat.ts`
  - 用途：聊天相关类型定义
- `..\web\src\types\auth.ts`
  - 用途：认证相关类型定义
- `..\web\src\types\customer.ts`
  - 用途：顾客相关类型定义
- `..\web\src\types\doctor.ts`
  - 用途：医生相关类型定义

## 样式文件

- `..\web\src\app\globals.css`
  - 用途：全局样式定义

## 配置文件

- `..\web\eslint.config.mjs`
  - 用途：ESLint配置
- `..\web\next.config.ts`
  - 用途：Next.js配置
- `..\web\postcss.config.mjs`
  - 用途：PostCSS配置
- `..\web\tsconfig.json`
  - 用途：TypeScript配置
- `..\web\next-env.d.ts`
  - 用途：Next.js类型声明

## 测试文件

- `..\api\scripts\test.ps1`
  - 用途：Windows测试脚本
- `..\api\scripts\test.sh`
  - 用途：Unix测试脚本
- `..\api\tests\conftest.py`
  - 用途：Pytest配置
- `..\api\tests\test_auth.py`
  - 用途：认证功能测试
- `..\api\tests\test_users.py`
  - 用途：用户功能测试

## 依赖管理

- `..\api\requirements.txt`
  - 用途：Python依赖清单
- `..\web\package.json`
  - 用途：Node.js依赖配置

## 文档文件

- `..\api\README.md`
  - 用途：API项目说明
- `..\web\README.md`
  - 用途：前端项目说明
- `..\README.md`
  - 用途：项目总体说明
- `..\docs\TODO.md`
  - 用途：项目待办任务清单
- `..\docs\FILE_MAP.md`
  - 用途：项目文件结构映射

## 资源文件

- `..\web\public\file.svg`
  - 用途：文件图标
- `..\web\public\globe.svg`
  - 用途：全球图标
- `..\web\public\next.svg`
  - 用途：Next.js图标
- `..\web\public\vercel.svg`
  - 用途：Vercel图标
- `..\web\public\window.svg`
  - 用途：窗口图标
- `..\web\public\logo.svg`
  - 用途：安美智享Logo
- `..\web\public\logo.png`
  - 用途：安美智享Logo备用图片
- `..\web\public\logo.ico`
  - 用途：安美智享网站图标
- `..\web\public\avatars\default.png`
  - 用途：默认头像
- `..\web\public\avatars\user1.png`
  - 用途：顾客李小姐头像
- `..\web\public\avatars\user2.png`
  - 用途：顾客王先生头像

## 用户系统重构设计

### 数据库模型

在重构后，我们将从单表用户设计迁移到多表继承模式，主要包括以下表结构：

**1. 基础用户表 (Users)**

- 存储所有用户共享的基本信息
- 字段：id, email, username, hashed_password, phone, avatar, is_active, created_at, updated_at

**2. 角色表 (Roles)**

- 存储系统中的角色定义
- 字段：id, name, description, created_at, updated_at

**3. 用户-角色关联表 (UserRoles)**

- 多对多关联用户和角色
- 字段：user_id, role_id, assigned_at, assigned_by

**4. 顾客表 (Customers)**

- 存储顾客特有信息
- 字段：id, user_id(外键), medical_history, allergies, preferences

**5. 医生表 (Doctors)**

- 存储医生特有信息
- 字段：id, user_id(外键), specialization, certification, license_number

**6. 顾问表 (Consultants)**

- 存储顾问特有信息
- 字段：id, user_id(外键), expertise, performance_metrics

**7. 运营人员表 (Operators)**

- 存储运营人员特有信息
- 字段：id, user_id(外键), department, responsibilities

**8. 管理员表 (Administrators)**

- 存储管理员特有信息
- 字段：id, user_id(外键), admin_level, access_permissions

### API设计

**1. 认证相关**

- POST /api/auth/register - 顾客自行注册
- POST /api/auth/login - 用户登录
- POST /api/auth/refresh-token - 刷新令牌
- GET /api/auth/me - 获取当前用户信息
- PUT /api/auth/me - 更新当前用户信息
- GET /api/auth/roles - 获取用户角色
- POST /api/auth/switch-role - 切换当前活跃角色

**2. 用户管理**

- GET /api/users - 获取用户列表(支持角色筛选)
- POST /api/users - 创建新用户(支持指定角色)
- GET /api/users/{id} - 获取特定用户信息
- PUT /api/users/{id} - 更新用户信息
- DELETE /api/users/{id} - 删除用户
- GET /api/users/{id}/roles - 获取用户的角色
- POST /api/users/{id}/roles - 为用户分配角色
- DELETE /api/users/{id}/roles/{role_id} - 移除用户角色

**3. 角色管理**

- GET /api/roles - 获取所有角色
- POST /api/roles - 创建新角色
- GET /api/roles/{id} - 获取特定角色
- PUT /api/roles/{id} - 更新角色
- DELETE /api/roles/{id} - 删除角色

### 重构路径

**1. 数据迁移**

- 创建新的数据库表结构
- 从现有用户表提取基本信息到新的Users表
- 根据现有用户角色创建相应的扩展表记录
- 建立用户-角色关联关系

**2. 认证流程**

- 更新JWT令牌生成和验证逻辑，包含活跃角色信息
- 实现基于角色的访问控制(RBAC)
- 支持用户角色切换功能

**3. 前端适配**

- 更新Auth状态管理
- 重构用户管理界面
- 实现角色切换UI
