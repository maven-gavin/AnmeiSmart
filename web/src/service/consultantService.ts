import { SimulationImage, ProjectType, PersonalizedPlan } from '@/types/consultant';
import { CustomerProfile } from '@/types/chat';

// 模拟项目类型数据
const mockProjectTypes: ProjectType[] = [
  {
    id: 'pt-001',
    name: 'double-eyelid',
    label: '双眼皮',
    description: '通过手术方式改变上眼睑形态，形成美观的双眼皮褶皱',
    parameters: [
      {
        id: 'param-001',
        name: 'foldWidth',
        label: '褶皱宽度',
        type: 'slider',
        min: 4,
        max: 10,
        step: 0.5,
        defaultValue: 6
      },
      {
        id: 'param-002',
        name: 'foldShape',
        label: '褶皱形状',
        type: 'select',
        options: [
          { value: 'parallel', label: '平行型' },
          { value: 'crescent', label: '新月型' },
          { value: 'natural', label: '自然型' }
        ],
        defaultValue: 'natural'
      }
    ]
  },
  {
    id: 'pt-002',
    name: 'nose-augmentation',
    label: '鼻部整形',
    description: '通过填充或手术方式改善鼻子形态，提升面部立体感',
    parameters: [
      {
        id: 'param-003',
        name: 'heightIncrease',
        label: '鼻梁高度',
        type: 'slider',
        min: 1,
        max: 5,
        step: 0.5,
        defaultValue: 2.5
      },
      {
        id: 'param-004',
        name: 'tipRefinement',
        label: '鼻尖精细度',
        type: 'slider',
        min: 1,
        max: 5,
        step: 0.5,
        defaultValue: 3
      },
      {
        id: 'param-005',
        name: 'nostrilWidth',
        label: '鼻孔宽度',
        type: 'slider',
        min: -3,
        max: 0,
        step: 0.5,
        defaultValue: -1.5
      }
    ]
  },
  {
    id: 'pt-003',
    name: 'face-slimming',
    label: '瘦脸',
    description: '通过注射或手术方式减少面部脂肪，塑造精致小脸',
    parameters: [
      {
        id: 'param-006',
        name: 'jawlineReduction',
        label: '下颌角缩小',
        type: 'slider',
        min: 0,
        max: 10,
        step: 1,
        defaultValue: 5
      },
      {
        id: 'param-007',
        name: 'cheekReduction',
        label: '颊部缩小',
        type: 'slider',
        min: 0,
        max: 10,
        step: 1,
        defaultValue: 5
      }
    ]
  },
  {
    id: 'pt-004',
    name: 'lip-augmentation',
    label: '唇部丰盈',
    description: '通过注射填充物质增加唇部饱满度和形态',
    parameters: [
      {
        id: 'param-008',
        name: 'volumeIncrease',
        label: '丰盈度',
        type: 'slider',
        min: 1,
        max: 5,
        step: 0.5,
        defaultValue: 2
      },
      {
        id: 'param-009',
        name: 'shapeStyle',
        label: '唇形风格',
        type: 'select',
        options: [
          { value: 'natural', label: '自然饱满' },
          { value: 'curvy', label: '性感曲线' },
          { value: 'defined', label: '轮廓分明' }
        ],
        defaultValue: 'natural'
      }
    ]
  }
];

// 模拟术前模拟图像数据
const mockSimulationImages: SimulationImage[] = [
  {
    id: 'sim-001',
    originalImage: '/images/simulation/original-1.jpg',
    simulatedImages: [
      {
        id: 'sim-001-1',
        image: '/images/simulation/sim-1-1.jpg',
        projectType: 'double-eyelid',
        parameters: {
          foldWidth: 6,
          foldShape: 'natural'
        }
      },
      {
        id: 'sim-001-2',
        image: '/images/simulation/sim-1-2.jpg',
        projectType: 'nose-augmentation',
        parameters: {
          heightIncrease: 2.5,
          tipRefinement: 3,
          nostrilWidth: -1.5
        }
      }
    ],
    customerId: '101',
    customerName: '李小姐',
    createdAt: '2024-05-01T14:30:00Z',
    notes: '客户对双眼皮效果满意，考虑进一步调整鼻部'
  },
  {
    id: 'sim-002',
    originalImage: '/images/simulation/original-2.jpg',
    simulatedImages: [
      {
        id: 'sim-002-1',
        image: '/images/simulation/sim-2-1.jpg',
        projectType: 'face-slimming',
        parameters: {
          jawlineReduction: 7,
          cheekReduction: 5
        }
      }
    ],
    customerId: '102',
    customerName: '王先生',
    createdAt: '2024-05-02T16:45:00Z'
  }
];

// 模拟个性化方案数据
const mockPersonalizedPlans: PersonalizedPlan[] = [
  {
    id: 'plan-a001',
    customerId: '101',
    customerName: '李小姐',
    customerProfile: {
      age: 28,
      gender: 'female',
      concerns: ['眼睛单眼皮', '鼻子不够挺'],
      budget: 20000,
      expectedResults: '希望变得更加精致自然'
    },
    projects: [
      {
        id: 'proj-001',
        name: '全切双眼皮',
        description: '通过手术方式创建持久自然的双眼皮褶皱',
        cost: 8000,
        duration: '1-2小时',
        recoveryTime: '7-10天',
        expectedResults: '更加明亮有神的眼睛',
        risks: ['术后肿胀', '疤痕', '感染风险']
      },
      {
        id: 'proj-002',
        name: '鼻部整形',
        description: '通过植入物提升鼻梁，refinement鼻尖',
        cost: 12000,
        duration: '2-3小时',
        recoveryTime: '10-14天',
        expectedResults: '鼻梁更高挺，鼻尖更加精致',
        risks: ['感染', '位移', '色素沉着']
      }
    ],
    totalCost: 20000,
    estimatedTimeframe: '2周',
    createdAt: '2024-05-03T11:30:00Z',
    consultantId: '2',
    consultantName: '李顾问',
    status: 'shared',
    notes: '客户对方案表示满意，计划下周确认'
  },
  {
    id: 'plan-a002',
    customerId: '102',
    customerName: '王先生',
    customerProfile: {
      age: 35,
      gender: 'male',
      concerns: ['面部显老', '下巴轮廓不明显'],
      budget: 15000,
      expectedResults: '希望看起来更年轻有精神'
    },
    projects: [
      {
        id: 'proj-003',
        name: '玻尿酸填充',
        description: '使用玻尿酸填充面部凹陷区域',
        cost: 6000,
        duration: '30分钟',
        recoveryTime: '1-2天',
        expectedResults: '面部更加饱满年轻',
        risks: ['淤青', '不对称', '过敏反应']
      },
      {
        id: 'proj-004',
        name: '下巴轮廓注射',
        description: '通过注射方式强化下巴轮廓',
        cost: 8000,
        duration: '45分钟',
        recoveryTime: '3-5天',
        expectedResults: '更加分明的下巴轮廓线',
        risks: ['淤青', '不对称', '感染']
      }
    ],
    totalCost: 14000,
    estimatedTimeframe: '1周',
    createdAt: '2024-05-04T14:20:00Z',
    consultantId: '2',
    consultantName: '李顾问',
    status: 'draft'
  }
];

// 获取所有项目类型
export const getProjectTypes = async (): Promise<ProjectType[]> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(mockProjectTypes);
    }, 500);
  });
};

// 获取特定客户的术前模拟图像
export const getCustomerSimulations = async (customerId: string): Promise<SimulationImage[]> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const results = mockSimulationImages.filter(sim => sim.customerId === customerId);
      resolve(results);
    }, 700);
  });
};

// 获取所有术前模拟图像
export const getAllSimulations = async (): Promise<SimulationImage[]> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(mockSimulationImages);
    }, 700);
  });
};

// 上传原始图像并生成模拟效果
export const uploadAndSimulate = async (
  file: File,
  customerId: string,
  customerName: string,
  projectType: string,
  parameters: Record<string, string | number>
): Promise<SimulationImage> => {
  // 在实际应用中，这里会上传图像到服务器并调用AI进行处理
  return new Promise((resolve) => {
    setTimeout(() => {
      const newSimulation: SimulationImage = {
        id: `sim-${Date.now()}`,
        originalImage: '/images/simulation/new-original.jpg', // 在实际应用中，这将是上传后的URL
        simulatedImages: [
          {
            id: `sim-${Date.now()}-1`,
            image: '/images/simulation/new-simulated.jpg', // 在实际应用中，这将是AI生成的URL
            projectType,
            parameters
          }
        ],
        customerId,
        customerName,
        createdAt: new Date().toISOString(),
      };
      mockSimulationImages.push(newSimulation);
      resolve(newSimulation);
    }, 1500); // 模拟上传和处理时间
  });
};

// 获取客户的个性化方案
export const getCustomerPlans = async (customerId: string): Promise<PersonalizedPlan[]> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const plans = mockPersonalizedPlans.filter(plan => plan.customerId === customerId);
      resolve(plans);
    }, 600);
  });
};

// 获取所有个性化方案
export const getAllPersonalizedPlans = async (): Promise<PersonalizedPlan[]> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(mockPersonalizedPlans);
    }, 600);
  });
};

// 创建个性化方案
export const createPersonalizedPlan = async (
  planData: Omit<PersonalizedPlan, 'id' | 'createdAt'>
): Promise<PersonalizedPlan> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const newPlan: PersonalizedPlan = {
        ...planData,
        id: `plan-a${Date.now()}`,
        createdAt: new Date().toISOString()
      };
      mockPersonalizedPlans.push(newPlan);
      resolve(newPlan);
    }, 800);
  });
};

// 更新个性化方案
export const updatePersonalizedPlan = async (
  planId: string,
  planData: Partial<PersonalizedPlan>
): Promise<PersonalizedPlan> => {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const planIndex = mockPersonalizedPlans.findIndex(p => p.id === planId);
      if (planIndex === -1) {
        reject(new Error('方案不存在'));
        return;
      }
      
      const updatedPlan = {
        ...mockPersonalizedPlans[planIndex],
        ...planData,
        updatedAt: new Date().toISOString()
      };
      
      mockPersonalizedPlans[planIndex] = updatedPlan;
      resolve(updatedPlan);
    }, 700);
  });
}; 