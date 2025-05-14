import { UserRole } from '@/types/auth';
import { Conversation, CustomerProfile, Message, User } from '@/types/chat';
import { Patient, TreatmentPlan, DoctorAppointment } from '@/types/doctor';

// 模拟用户数据
export const mockUsers = [
  {
    id: '1',
    name: '张医生',
    email: 'zhang@example.com',
    phone: '13800138001',
    avatar: '/avatars/doctor1.png',
    roles: ['doctor', 'consultant'] as UserRole[],
  },
  {
    id: '2',
    name: '李顾问',
    email: 'li@example.com',
    phone: '13900139001',
    avatar: '/avatars/consultant1.png',
    roles: ['consultant'] as UserRole[],
  },
  {
    id: '3',
    name: '王运营',
    email: 'wang@example.com',
    phone: '13700137001',
    avatar: '/avatars/operator1.png',
    roles: ['operator'] as UserRole[],
  },
  {
    id: '101',
    name: '李小姐',
    email: 'customer1@example.com',
    phone: '13812345678',
    avatar: '/avatars/user1.png',
    roles: ['customer'] as UserRole[],
  },
  {
    id: '102',
    name: '王先生',
    email: 'customer2@example.com',
    phone: '13987654321',
    avatar: '/avatars/user2.png',
    roles: ['customer'] as UserRole[],
  },
];


// 模拟会话数据
export const mockConversations: Conversation[] = [
  {
    id: '1',
    user: {
      id: '101',
      name: '李小姐',
      avatar: '/avatars/user1.png',
      tags: ['首次咨询', 'VIP客户'],
    },
    lastMessage: {
      id: 'm1',
      content: '请问双眼皮手术大概需要多久恢复？',
      type: 'text',
      sender: {
        id: '101',
        type: 'user',
        name: '李小姐',
        avatar: '/avatars/user1.png',
      },
      timestamp: '2024-04-28T10:30:00Z',
    },
    unreadCount: 2,
    updatedAt: '2024-04-28T10:30:00Z',
  },
  {
    id: '2',
    user: {
      id: '102',
      name: '王先生',
      avatar: '/avatars/user2.png',
      tags: ['回头客'],
    },
    lastMessage: {
      id: 'm2',
      content: '我想了解一下玻尿酸的效果',
      type: 'text',
      sender: {
        id: '102',
        type: 'user',
        name: '王先生',
        avatar: '/avatars/user2.png',
      },
      timestamp: '2024-04-28T09:15:00Z',
    },
    unreadCount: 0,
    updatedAt: '2024-04-28T09:15:00Z',
  },
];

// 模拟聊天消息数据
export const mockMessages: Record<string, Message[]> = {
  '1': [
    {
      id: 'm1',
      content: '您好，请问有什么可以帮您？',
      type: 'text',
      sender: {
        id: 'ai1',
        type: 'ai',
        name: 'AI助手',
        avatar: '/avatars/ai.png',
      },
      timestamp: '2024-04-28T10:29:00Z',
    },
    {
      id: 'm2',
      content: '请问双眼皮手术大概需要多久恢复？',
      type: 'text',
      sender: {
        id: '101',
        type: 'user',
        name: '李小姐',
        avatar: '/avatars/user1.png',
      },
      timestamp: '2024-04-28T10:30:00Z',
    },
    {
      id: 'm3',
      content: '双眼皮手术一般术后1-2周即可基本恢复，但完全恢复需要1-3个月。拆线通常在术后5-7天进行，之后可以化淡妆。建议术后1个月内避免剧烈运动，3个月内防晒。每个人的恢复情况会有差异，具体还需根据医生的建议进行。',
      type: 'text',
      sender: {
        id: 'ai1',
        type: 'ai',
        name: 'AI助手',
        avatar: '/avatars/ai.png',
      },
      timestamp: '2024-04-28T10:31:00Z',
    },
  ],
  '2': [
    {
      id: 'm1',
      content: '您好，有什么可以帮到您？',
      type: 'text',
      sender: {
        id: 'ai1',
        type: 'ai',
        name: 'AI助手',
        avatar: '/avatars/ai.png',
      },
      timestamp: '2024-04-28T09:10:00Z',
    },
    {
      id: 'm2',
      content: '我想了解一下玻尿酸的效果',
      type: 'text',
      sender: {
        id: '102',
        type: 'user',
        name: '王先生',
        avatar: '/avatars/user2.png',
      },
      timestamp: '2024-04-28T09:15:00Z',
    },
  ],
};

// 模拟客户档案数据
export const mockCustomerProfiles: Record<string, CustomerProfile> = {
  '101': {
    id: '101',
    basicInfo: {
      name: '李小姐',
      age: 28,
      gender: 'female',
      phone: '13812345678',
    },
    consultationHistory: [
      {
        date: '2024-03-15',
        type: '咨询',
        description: '咨询双眼皮和鼻部整形',
      },
    ],
    riskNotes: [],
  },
  '102': {
    id: '102',
    basicInfo: {
      name: '王先生',
      age: 35,
      gender: 'male',
      phone: '13987654321',
    },
    consultationHistory: [
      {
        date: '2023-12-20',
        type: '治疗',
        description: '玻尿酸填充额头',
      },
    ],
    riskNotes: [
      {
        type: '过敏史',
        description: '对青霉素过敏',
        level: 'medium',
      },
    ],
  },
};

// 模拟医生端患者数据
export const mockPatients: Patient[] = [
  {
    id: '101',
    name: '李小姐',
    avatar: '/avatars/user1.png',
    age: 28,
    gender: 'female',
    phone: '13812345678',
    email: 'customer1@example.com',
    treatment: '双眼皮手术',
    date: '2024-05-15',
    urgency: 'medium',
    medicalHistory: [
      {
        id: 'mh-101-1',
        type: 'surgery',
        description: '鼻部整形手术',
        date: '2023-10-15',
      }
    ],
    allergies: [],
    lastVisit: '2024-04-15',
    treatments: ['双眼皮', '鼻部整形'],
    needsFollowUp: true
  },
  {
    id: '102',
    name: '王先生',
    avatar: '/avatars/user2.png',
    age: 35,
    gender: 'male',
    phone: '13987654321',
    email: 'customer2@example.com',
    treatment: '玻尿酸填充',
    date: '2024-05-10',
    urgency: 'high',
    medicalHistory: [
      {
        id: 'mh-102-1',
        type: 'allergy',
        description: '对青霉素过敏',
        date: '2020-05-20',
      },
      {
        id: 'mh-102-2',
        type: 'treatment',
        description: '玻尿酸填充额头',
        date: '2023-12-20',
      }
    ],
    allergies: ['青霉素'],
    lastVisit: '2024-05-10',
    treatments: ['玻尿酸填充'],
    needsFollowUp: true
  },
  {
    id: '103',
    name: '赵女士',
    avatar: '/avatars/user3.png',
    age: 42,
    gender: 'female',
    phone: '13645678901',
    email: 'customer3@example.com',
    treatment: '肉毒素注射',
    date: '2024-05-20',
    urgency: 'low',
    medicalHistory: [
      {
        id: 'mh-103-1',
        type: 'treatment',
        description: '肉毒素注射额头纹',
        date: '2023-08-10',
      }
    ],
    allergies: [],
    lastVisit: '2024-05-20',
    treatments: ['肉毒素注射'],
    needsFollowUp: false
  },
  {
    id: '104',
    name: '钱先生',
    avatar: '/avatars/user4.png',
    age: 50,
    gender: 'male',
    phone: '13567890123',
    email: 'customer4@example.com',
    treatment: '脱发治疗',
    date: '2024-05-08',
    urgency: 'medium',
    medicalHistory: [
      {
        id: 'mh-104-1',
        type: 'heart',
        description: '高血压，长期服用降压药',
        date: '2015-01-05',
      }
    ],
    allergies: ['磺胺类药物'],
    lastVisit: '2024-05-08',
    treatments: ['脱发治疗', '面部护理'],
    needsFollowUp: false
  },
  {
    id: '105',
    name: '孙小姐',
    avatar: '/avatars/user5.png',
    age: 31,
    gender: 'female',
    phone: '13765432109',
    email: 'customer5@example.com',
    treatment: '激光祛斑',
    date: '2024-05-12',
    urgency: 'low',
    medicalHistory: [
      {
        id: 'mh-105-1',
        type: 'skin',
        description: '敏感性皮肤',
        date: '2022-03-15',
      }
    ],
    allergies: ['乳胶'],
    lastVisit: '2024-04-12',
    treatments: ['激光祛斑'],
    needsFollowUp: false
  }
];

// 模拟治疗方案数据
export const mockTreatmentPlans: TreatmentPlan[] = [
  {
    id: 'plan-001',
    patientId: '101',
    patientName: '李小姐',
    doctorId: '1',
    doctorName: '张医生',
    diagnosis: '上睑下垂，需要双眼皮手术矫正',
    medications: [
      {
        id: 'med-001-1',
        name: '利多卡因',
        dosage: '2%',
        frequency: '术中局部注射',
        duration: '单次',
        notes: '局部麻醉剂'
      },
      {
        id: 'med-001-2',
        name: '头孢类抗生素',
        dosage: '0.5g',
        frequency: '每日2次',
        duration: '3天',
        notes: '预防感染'
      }
    ],
    procedures: [
      {
        id: 'proc-001-1',
        name: '双眼皮切开法',
        description: '通过切开上眼睑皮肤，去除多余脂肪和部分眼轮匝肌，形成双眼皮褶皱',
        duration: '1-2小时',
        notes: '需要局部麻醉'
      }
    ],
    createdAt: '2024-05-01T09:30:00Z',
    status: 'approved',
    followUpDate: '2024-05-15'
  },
  {
    id: 'plan-002',
    patientId: '102',
    patientName: '王先生',
    doctorId: '1',
    doctorName: '张医生',
    diagnosis: '面部额头凹陷，需要填充改善',
    medications: [
      {
        id: 'med-002-1',
        name: '利多卡因',
        dosage: '2%',
        frequency: '术前局部涂抹',
        duration: '单次',
        notes: '表面麻醉'
      }
    ],
    procedures: [
      {
        id: 'proc-002-1',
        name: '玻尿酸注射填充',
        description: '使用玻尿酸填充额头凹陷区域',
        duration: '30分钟',
        notes: '玻尿酸品牌：XXX，用量：2ml'
      }
    ],
    createdAt: '2024-04-28T14:15:00Z',
    status: 'pending',
    notes: '患者有青霉素过敏史，需注意观察'
  },
  {
    id: 'plan-003',
    patientId: '103',
    patientName: '赵女士',
    doctorId: '1',
    doctorName: '张医生',
    diagnosis: '面部皱纹明显，额头和眉间纹需要改善',
    medications: [
      {
        id: 'med-003-1',
        name: '肉毒素',
        dosage: '50单位',
        frequency: '单次注射',
        duration: '一次性',
        notes: '分配：额头20单位，眉间20单位，眼尾10单位'
      }
    ],
    procedures: [
      {
        id: 'proc-003-1',
        name: '肉毒素注射',
        description: '通过肉毒素麻痹面部肌肉，减少动态皱纹',
        duration: '20分钟',
        notes: '预计维持时间4-6个月'
      }
    ],
    createdAt: '2024-05-03T10:45:00Z',
    status: 'approved',
    followUpDate: '2024-05-20'
  }
];

// 模拟医生预约数据
export const mockDoctorAppointments: DoctorAppointment[] = [
  {
    id: 'appt-001',
    patientId: '101',
    patientName: '李小姐',
    date: '2024-05-06', // 今天日期，需要动态调整
    time: '09:30',
    duration: 60,
    treatmentType: '术前评估 - 双眼皮手术',
    status: 'confirmed',
    notes: '首次手术，需详细评估'
  },
  {
    id: 'appt-002',
    patientId: '102',
    patientName: '王先生',
    date: '2024-05-06', // 今天日期，需要动态调整
    time: '11:00',
    duration: 30,
    treatmentType: '玻尿酸填充',
    status: 'confirmed',
    notes: '患者有青霉素过敏史'
  },
  {
    id: 'appt-003',
    patientId: '103',
    patientName: '赵女士',
    date: '2024-05-06', // 今天日期，需要动态调整
    time: '14:30',
    duration: 30,
    treatmentType: '肉毒素注射',
    status: 'pending',
    notes: '复诊患者'
  },
  {
    id: 'appt-004',
    patientId: '104',
    patientName: '钱先生',
    date: '2024-05-08',
    time: '10:00',
    duration: 45,
    treatmentType: '脱发治疗评估',
    status: 'confirmed',
    notes: '患有高血压，长期服用降压药'
  },
  {
    id: 'appt-005',
    patientId: '105',
    patientName: '孙小姐',
    date: '2024-05-12',
    time: '15:00',
    duration: 45,
    treatmentType: '激光祛斑',
    status: 'confirmed',
    notes: '敏感性皮肤，需谨慎操作'
  }
]; 