# 个人中心模块产品设计文档

## 概述

个人中心作为安美智享系统的核心用户管理模块，为所有角色的用户提供统一的个人信息管理、偏好设置、安全配置等功能。该模块基于"关注点分离"和"角色适配"的设计原则，既保证了功能的一致性，又满足了不同角色的个性化需求。

## 业务价值

- **用户体验统一**: 为所有角色提供一致的个人中心体验
- **安全性提升**: 集中管理用户安全设置和隐私配置
- **个性化服务**: 支持用户偏好设置，提升系统使用体验
- **管理效率**: 简化用户信息维护，减少管理成本

## 功能架构

### 1. 核心功能模块

#### 1.1 个人信息管理

**基础信息**

- 姓名、头像、联系方式
- 邮箱、手机号码验证状态
- 账户创建时间、最后登录时间

**角色特定信息**

- 客户：年龄、性别、医疗偏好、过敏史
- 医生：执业资质、专业认证、科室信息
- 顾问：专业领域、服务评级、认证状态
- 运营：部门信息、职责范围
- 管理员：管理级别、权限范围

#### 1.2 角色与权限管理

**默认角色设置** ⭐核心功能

- 设置登录后的默认角色（用户有多角色时，仅首次登录时应用）
- 角色权限查看（只读）

#### 1.3 安全设置

**密码管理**

- 修改登录密码
- 密码强度要求提示
- 登录设备管理

**安全验证**

- 手机号码验证
- 邮箱验证
- 登录日志查看

#### 1.4 偏好设置

**通知偏好**

- 消息通知开关
- 邮件通知设置
- 推送时间段设置

#### 1.5 隐私设置

**信息可见性**

- 个人信息对其他角色的可见程度
- 在线状态显示设置

**数据管理**

- 个人数据导出
- 账户注销申请

### 2. 行业特色功能

#### 2.1 客户专属

**美容档案管理**

- 个人美容目标设置
- 过往治疗记录查看
- 过敏反应记录
- 美容偏好标签

**隐私保护**

- 敏感信息访问控制
- 照片隐私设置

#### 2.2 专业人员

**资质信息**

- 执业证书上传和管理
- 专业认证状态
- 继续教育记录

**服务统计**

- 个人服务数据统计
- 客户满意度反馈
- 专业发展轨迹

## 技术架构设计

### 3.1 前端设计

**页面结构**

```
/profile
  ├── /basic          # 基本信息
  ├── /security       # 安全设置  
  ├── /preferences    # 偏好设置
  ├── /privacy        # 隐私设置
  └── /role-settings  # 角色设置
```

**组件架构**

- `PersonalCenter` - 主容器组件
- `ProfileTabs` - 标签页导航
- `BasicInfoPanel` - 基本信息面板
- `SecurityPanel` - 安全设置面板
- `PreferencesPanel` - 偏好设置面板
- `RoleSettingsPanel` - 角色设置面板

### 3.2 后端设计

**API端点**

```
GET /api/v1/profile/me                    # 获取个人信息
PUT /api/v1/profile/me                    # 更新个人信息
GET /api/v1/profile/preferences           # 获取偏好设置
PUT /api/v1/profile/preferences           # 更新偏好设置
GET /api/v1/profile/security             # 获取安全设置
PUT /api/v1/profile/security             # 更新安全设置
POST /api/v1/profile/change-password     # 修改密码
GET /api/v1/profile/login-history        # 获取登录历史
PUT /api/v1/profile/default-role         # 设置默认角色
```

**数据模型扩展**

```sql
-- 用户偏好设置表（简化版）
CREATE TABLE user_preferences (
    user_id VARCHAR(36) PRIMARY KEY,
    notification_enabled BOOLEAN DEFAULT true,
    email_notification BOOLEAN DEFAULT true,
    push_notification BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 用户默认角色设置表
CREATE TABLE user_default_roles (
    user_id VARCHAR(36) PRIMARY KEY,
    default_role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 登录历史表
CREATE TABLE login_history (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    login_role VARCHAR(50),
    location VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

**核心实现逻辑**

1. **默认角色应用逻辑**：

   - 用户首次登录时，检查是否设置了默认角色
   - 如果设置了且用户拥有该角色，自动切换到默认角色
   - 后续登录记住用户上次使用的角色（通过JWT token中的active_role）
2. **数据同步策略**：

   - 个人中心的信息修改直接操作现有的users表和相关扩展表
   - 与现有的customer/profile页面共享相同的数据源
   - 通过统一的用户服务接口(user_service.py)确保数据一致性
   - 使用相同的API接口（/api/v1/auth/me, /api/v1/users/me）

## 用户界面设计

### 4.1 导航设计

**入口位置**: RoleHeader组件的用户下拉菜单中

- 位置：在"切换角色"下方，"退出登录"上方
- 文本：个人中心
- 图标：用户设置图标

### 4.2 页面布局

**左侧导航栏**

- 基本信息
- 安全设置
- 偏好设置
- 隐私设置
- 角色管理（有多角色时显示）

**右侧内容区**

- 根据选中的导航项显示对应内容
- 支持实时保存和批量保存两种模式

### 4.3 关键页面设计

#### 基本信息页面

- 头像上传区域（支持裁剪）
- 基本信息表单（姓名、邮箱、手机号）
- 角色特定信息区域（动态显示）
- 账户状态信息（只读）

#### 角色管理页面

- 当前拥有的角色列表
- 默认角色设置（下拉选择）
- 各角色权限说明（只读）

## 权限控制

### 5.1 访问权限

**基本访问权限**

- 所有已认证用户可访问个人中心
- 用户只能查看和修改自己的信息

**功能模块权限**

- **基本信息**：所有用户可查看修改（姓名、邮箱、手机号、头像）
- **安全设置**：所有用户可访问（密码修改、登录历史查看）
- **偏好设置**：所有用户可访问（通知偏好设置）
- **隐私设置**：所有用户可访问（信息可见性控制）
- **角色管理**：只有多角色用户可见（默认角色设置、权限查看）

**敏感操作权限**

- 密码修改：需要验证当前密码
- 邮箱修改：需要新邮箱验证码确认
- 手机号修改：需要新手机号验证码确认
- 账户注销：需要管理员审核

**管理员特殊权限**

- 可查看（不可编辑）其他用户的基本信息
- 可查看用户的登录历史
- 可处理账户注销申请

### 5.2 数据权限

- 用户只能修改自己的信息
- 角色特定信息的修改权限由角色决定
- 某些字段（如用户名、角色分配）可能需要管理员权限

## 实施计划

### Phase 1: 基础功能

- [ ] 个人中心入口添加
- [ ] 基本信息管理
- [ ] 密码修改功能
- [ ] 默认角色设置

### Phase 2: 增强功能

- [ ] 偏好设置
- [ ] 登录历史
- [ ] 安全设置扩展
- [ ] 角色特定信息管理

### Phase 3: 高级功能

- [ ] 隐私控制
- [ ] 数据导出
- [ ] 设备管理

## 注意事项

1. **数据一致性**: 确保个人中心的信息与其他模块保持同步
2. **性能考虑**: 偏好设置的变更应该及时生效，避免需要重新登录
3. **安全性**: 敏感操作需要验证当前密码或短信验证
4. **用户体验**: 提供明确的保存状态反馈和错误提示
5. **移动端适配**: 确保在移动设备上的良好体验

## 验收标准

- [ ] 所有角色用户都能正常访问个人中心
- [ ] 默认角色设置功能正常工作
- [ ] 个人信息修改能正确保存和同步
- [ ] 密码修改功能安全可靠
- [ ] 界面响应式设计适配移动端
- [ ] 所有表单验证正确工作
- [ ] 权限控制符合安全要求

## 技术实现详细说明

### 默认角色实现逻辑

1. **数据存储**：在 `user_default_roles` 表中存储用户的默认角色设置
2. **首次登录检查**：
   ```javascript
   // 在authService.login中添加逻辑
   if (isFirstLogin && userHasDefaultRole && userHasThisRole) {
     await this.switchRole(defaultRole);
   }
   ```
3. **角色记忆**：后续登录使用JWT token中的active_role
4. **设置界面**：在个人中心提供下拉选择器设置默认角色

### 数据同步方案

1. **统一数据源**：

   - 个人中心与现有profile页面使用相同的API接口
   - 共享 `users` 表和各角色扩展表（`customers`, `doctors`, 等）
   - 通过 `user_service.py` 统一处理数据更新
2. **API复用**：

   - 复用现有的 `/api/v1/auth/me` 和 `/api/v1/users/me` 接口
   - 扩展现有的用户更新接口支持个人中心的新字段
3. **前端同步**：

   - 使用相同的 `authService` 和用户状态管理
   - 个人中心的修改会触发全局用户状态更新

### 集成现有系统

个人中心作为新增功能，将与现有系统无缝集成：

- 不破坏现有的用户管理功能
- 复用现有的权限控制体系
- 保持与现有API的兼容性
