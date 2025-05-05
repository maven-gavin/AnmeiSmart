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
- `..\api\app\crud\crud_user.py`
  - 用途：用户数据库操作
- `..\api\app\db\base.py`
  - 用途：数据库连接与会话管理
- `..\api\app\db\init_db.py`
  - 用途：数据库初始化脚本
- `..\api\app\db\models\user.py`
  - 用途：用户数据库模型定义
- `..\api\app\models\token.py`
  - 用途：Token数据模型
- `..\api\app\models\user.py`
  - 用途：用户数据模型（Pydantic模型）
- `..\api\main.py`
  - 用途：FastAPI应用入口

## 前端组件

- `..\web\src\app\advisor\chat\page.tsx`
  - 用途：顾问聊天页面
- `..\web\src\app\components\Todo.tsx`
  - 用途：待办事项组件
- `..\web\src\app\layout.tsx`
  - 用途：应用布局定义
- `..\web\src\app\page.tsx`
  - 用途：首页组件
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

## 工具和类型

- `..\web\src\lib\utils.ts`
  - 用途：通用工具函数
- `..\web\src\types\chat.ts`
  - 用途：聊天相关类型定义

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
