import { MenuConfig } from '@/types/menu';

export const menuConfig: MenuConfig = {
  items: [
    // 所有角色共享
    {
      id: 'home',
      label: '首页  ',
      path: '/home',
      icon: 'home-icon',
      roles: ['doctor','consultant', 'customer', 'admin', 'operator']
    },
    // 任务管理 - 不同角色看到不同任务
    {
      id: 'tasks-admin',
      label: '任务管理',
      path: '/tasks',
      icon: 'task-icon',
      roles: ['doctor','consultant', 'customer', 'admin', 'operator']
    },    
    {
      id: 'agents-explore',
      label: '智能体探索',
      path: '/agents/explore',
      icon: 'agent-icon',
      roles: ['doctor','consultant', 'customer', 'admin', 'operator']
    },       
    {
      id: 'chat-consultant',
      label: '智能沟通',
      path: '/chat',
      icon: 'chat-icon',
      roles: ['doctor','consultant', 'customer', 'admin', 'operator']
    }, 
    {
      id: 'contacts',
      label: '通讯录管理',
      path: '/contacts',
      icon: 'contacts-icon',
      roles: ['doctor', 'consultant', 'customer', 'admin', 'operator']
    },    
    // 医生端菜单
    // 患者管理模块已移除
    
    // 顾问端菜单
    // 术前模拟与方案推荐模块已移除
    
    // 客户端菜单
    
    // 管理端菜单
    {
      id: 'users',
      label: '用户管理',
      path: '/users',
      icon: 'users-icon',
      roles: ['admin']
    },
    {
      id: 'roles',
      label: '角色管理',
      path: '/admin/roles',
      icon: 'roles-icon',
      roles: ['admin']
    },
    {
      id: 'permissions-admin',
      label: '权限管理',
      path: '/admin/permissions',
      icon: 'permissions-icon',
      roles: ['admin']
    },
    {
      id: 'resources-admin',
      label: '资源管理',
      path: '/admin/resources',
      icon: 'resources-icon',
      roles: ['admin']
    },
    {
      id: 'tenants-admin',
      label: '租户管理',
      path: '/admin/tenants',
      icon: 'tenants-icon',
      roles: ['admin']
    },
    {
      id: 'digital-humans-admin',
      label: '数字人管理',
      path: '/admin/digital-humans',
      icon: 'digital-human-icon',
      roles: ['admin']
    },
    {
      id: 'agents-setup',
      label: '智能体配置',
      path: '/agents/setup',
      icon: 'agent-icon',
      roles: ['admin']
    },
    {
      id: 'mcp',
      label: 'MCP配置',
      path: '/mcp',
      icon: 'mcp-icon',
      roles: ['admin']
    },
    {
      id: 'settings',
      label: '系统设置',
      path: '/settings',
      icon: 'settings-icon',
      roles: ['admin']
    },
    {
      id: 'statistics',
      label: '数据统计',
      path: '/statistics',
      icon: 'stats-icon',
      roles: ['admin']
    },    

    {
      id: 'profile',
      label: '个人中心',
      path: '/profile',
      icon: 'profile-icon',
      roles: ['doctor', 'consultant', 'customer', 'admin', 'operator']
    }
  ]
}; 