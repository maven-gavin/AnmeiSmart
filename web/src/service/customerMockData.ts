import { CustomerAppointment, Treatment, TreatmentPlan } from "@/types/customer";
import { Message } from "@/types/chat";

// 模拟客户治疗记录
export const mockTreatments: Record<string, Treatment[]> = {
  '101': [
    {
      id: 't1',
      name: '双眼皮手术',
      date: '2024-03-20',
      doctor: '张医生',
      status: 'completed',
      description: '韩式三点双眼皮，7mm宽度',
      beforeImages: ['/images/eye-before-1.jpg', '/images/eye-before-2.jpg'],
      afterImages: ['/images/eye-after-1.jpg', '/images/eye-after-2.jpg'],
    }
  ],
  '102': [
    {
      id: 't2',
      name: '玻尿酸填充额头',
      date: '2023-12-20',
      doctor: '张医生',
      status: 'completed',
      description: '使用瑞蓝2号玻尿酸1ml',
      beforeImages: ['/images/face-before-1.jpg'],
      afterImages: ['/images/face-after-1.jpg'],
    },
    {
      id: 't3',
      name: '水光针',
      date: '2024-04-15',
      doctor: '刘医生',
      status: 'completed',
      description: '面部水光针注射，改善肤质',
    }
  ]
};

// 模拟客户治疗方案
export const mockTreatmentPlans: Record<string, TreatmentPlan[]> = {
  '101': [
    {
      id: 'p1',
      title: '面部综合提升方案',
      createdAt: '2024-04-10',
      doctorName: '张医生',
      status: 'approved',
      items: [
        {
          name: '双眼皮手术',
          description: '韩式三点双眼皮，7mm宽度',
          price: 3800
        },
        {
          name: '鼻部整形',
          description: '鼻尖微调+鼻梁填充',
          price: 8500
        }
      ],
      totalPrice: 12300,
      notes: '分两次完成，先做双眼皮，恢复期后再做鼻部'
    }
  ],
  '102': [
    {
      id: 'p2',
      title: '面部轮廓优化方案',
      createdAt: '2024-02-15',
      doctorName: '张医生',
      status: 'approved',
      items: [
        {
          name: '玻尿酸填充额头',
          description: '使用瑞蓝2号玻尿酸1ml',
          price: 2800
        },
        {
          name: '下颌角肉毒素注射',
          description: '改善脸型，瘦脸效果',
          price: 3200
        }
      ],
      totalPrice: 6000
    },
    {
      id: 'p3',
      title: '肌肤年轻化方案',
      createdAt: '2024-04-05',
      doctorName: '刘医生',
      status: 'pending',
      items: [
        {
          name: '水光针疗程',
          description: '3次水光针注射，每月1次',
          price: 4500
        },
        {
          name: '光子嫩肤',
          description: '改善暗沉，提亮肤色',
          price: 2800
        }
      ],
      totalPrice: 7300
    }
  ]
};

// 模拟客户预约
export const mockAppointments: Record<string, CustomerAppointment[]> = {
  '101': [
    {
      id: 'a1',
      type: 'treatment',
      title: '鼻部整形手术',
      date: '2024-05-15',
      time: '10:00',
      doctor: '张医生',
      status: 'confirmed'
    }
  ],
  '102': [
    {
      id: 'a2',
      type: 'consultation',
      title: '皮肤护理咨询',
      date: '2024-05-10',
      time: '14:30',
      consultant: '李顾问',
      status: 'confirmed'
    },
    {
      id: 'a3',
      type: 'followup',
      title: '水光针术后复查',
      date: '2024-05-20',
      time: '15:00',
      doctor: '刘医生',
      status: 'pending'
    }
  ]
};

// 模拟客户消息通知
export const mockCustomerMessages: Record<string, Message[]> = {
  '101': [
    {
      id: 'cm1',
      type: 'text',
      content: '您的鼻部整形预约已确认，请于5月15日10:00准时到院。',
      sender: {
        id: 'system',
        type: 'system',
        name: '系统通知',
        avatar: '/avatars/system.png'
      },
      timestamp: '2024-04-25T10:00:00Z',
      isSystemMessage: true
    },
    {
      id: 'cm2',
      type: 'text',
      content: '您的方案"面部综合提升方案"已审核通过，可在方案详情中查看。',
      sender: {
        id: 'system',
        type: 'system',
        name: '系统通知',
        avatar: '/avatars/system.png'
      },
      timestamp: '2024-04-12T14:30:00Z',
      isSystemMessage: true
    }
  ],
  '102': [
    {
      id: 'cm3',
      type: 'text',
      content: '您的皮肤护理咨询预约已确认，请于5月10日14:30准时到院。',
      sender: {
        id: 'system',
        type: 'system',
        name: '系统通知',
        avatar: '/avatars/system.png'
      },
      timestamp: '2024-04-28T09:00:00Z',
      isSystemMessage: true
    }
  ]
}; 