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
    // 医生端菜单
    {
      id: 'plans-doctor',
      label: '治疗方案',
      path: '/plans/doctor',
      icon: 'treatment-icon',
      roles: ['doctor']
    },
    {
      id: 'patients-doctor',
      label: '患者管理',
      path: '/patients/doctor',
      icon: 'patients-icon',
      roles: ['doctor']
    },
    {
      id: 'treatments-doctor',
      label: '治疗记录',
      path: '/treatments/doctor',
      icon: 'records-icon',
      roles: ['doctor']
    },
    {
      id: 'appointments-doctor',
      label: '预约管理',
      path: '/appointments',
      icon: 'calendar-icon',
      roles: ['doctor']
    },
    
    // 顾问端菜单
    {
      id: 'chat-consultant',
      label: '智能客服',
      path: '/chat/consultant',
      icon: 'chat-icon',
      roles: ['consultant']
    },
    {
      id: 'simulation',
      label: '术前模拟',
      path: '/simulation',
      icon: 'simulation-icon',
      roles: ['consultant']
    },
    {
      id: 'consultant-plan',
      label: '方案推荐',
      path: '/plan',
      icon: 'plan-icon',
      roles: ['consultant']
    },
    
    // 客户端菜单
    {
      id: 'chat-customer',
      label: '在线咨询',
      path: '/chat/customer',
      icon: 'chat-icon',
      roles: ['customer']
    },
    {
      id: 'treatments-customer',
      label: '治疗记录',
      path: '/treatments/customer',
      icon: 'records-icon',
      roles: ['customer']
    },
    {
      id: 'plans-customer',
      label: '治疗方案',
      path: '/plans/customer',
      icon: 'treatment-icon',
      roles: ['customer']
    },
    {
      id: 'appointments-customer',
      label: '我的预约',
      path: '/appointments/customer',
      icon: 'calendar-icon',
      roles: ['customer']
    },
    
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
      path: '/roles',
      icon: 'roles-icon',
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
    
    // 所有角色共享
    {
      id: 'profile',
      label: '个人中心',
      path: '/profile',
      icon: 'profile-icon',
      roles: ['doctor', 'consultant', 'customer', 'admin']
    }
  ]
}; 