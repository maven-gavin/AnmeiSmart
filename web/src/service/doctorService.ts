import { Patient, TreatmentPlan, DoctorAppointment, DrugConflict, RiskFactor, Treatment } from '@/types/doctor';
import { mockPatients, mockTreatmentPlans, mockDoctorAppointments } from './mockData';

// 模拟治疗记录数据
const mockTreatments: Treatment[] = [
  {
    id: 'treatment-001',
    patientId: '101',
    patientName: '李小姐',
    doctorId: '1',
    doctorName: '张医生',
    planId: 'plan-001',
    treatmentType: '双眼皮手术',
    date: '2024-04-15',
    duration: 120,
    details: '上睑下垂矫正手术，切开法双眼皮成形术',
    procedures: [
      {
        id: 'proc-001',
        name: '双眼皮切开法',
        description: '通过切开上眼睑皮肤，去除多余脂肪和部分眼轮匝肌，形成双眼皮褶皱',
        duration: '2小时',
        notes: '手术顺利'
      }
    ],
    medications: [
      {
        id: 'med-001',
        name: '利多卡因',
        dosage: '2%',
        frequency: '术中局部注射',
        duration: '单次',
        notes: '局部麻醉剂'
      },
      {
        id: 'med-002',
        name: '头孢类抗生素',
        dosage: '0.5g',
        frequency: '每日2次',
        duration: '3天',
        notes: '预防感染'
      }
    ],
    outcome: '手术顺利完成，双眼皮形态自然',
    followUpRequired: true,
    followUpDate: '2024-04-22',
    notes: '患者手术后恢复良好，术后第二天有轻微水肿，疼痛感可接受',
    status: 'completed',
    createdAt: '2024-04-15T14:30:00Z'
  },
  {
    id: 'treatment-002',
    patientId: '102',
    patientName: '王先生',
    doctorId: '1',
    doctorName: '张医生',
    planId: 'plan-002',
    treatmentType: '玻尿酸填充',
    date: '2024-05-10',
    duration: 45,
    details: '面部额头凹陷区域注射玻尿酸进行填充',
    procedures: [
      {
        id: 'proc-002',
        name: '玻尿酸注射填充',
        description: '使用玻尿酸填充额头凹陷区域',
        duration: '45分钟',
        notes: '共注射2ml'
      }
    ],
    medications: [
      {
        id: 'med-003',
        name: '利多卡因乳膏',
        dosage: '适量',
        frequency: '术前局部涂抹',
        duration: '单次',
        notes: '表面麻醉'
      }
    ],
    outcome: '填充效果自然，客户满意',
    complications: '局部轻微红肿，预计3天内消退',
    followUpRequired: true,
    followUpDate: '2024-05-24',
    notes: '告知患者术后24小时内避免按摩填充部位，避免剧烈运动',
    status: 'completed',
    createdAt: '2024-05-10T10:15:00Z'
  },
  {
    id: 'treatment-003',
    patientId: '103',
    patientName: '赵女士',
    doctorId: '1',
    doctorName: '张医生',
    planId: 'plan-003',
    treatmentType: '肉毒素注射',
    date: '2024-05-20',
    duration: 30,
    details: '额头和眉间纹肉毒素注射',
    procedures: [
      {
        id: 'proc-003',
        name: '肉毒素注射',
        description: '通过肉毒素麻痹面部肌肉，减少动态皱纹',
        duration: '30分钟',
        notes: '共注射50单位'
      }
    ],
    medications: [],
    outcome: '注射成功，效果将在3-7天内逐渐显现',
    followUpRequired: false,
    notes: '告知患者4小时内不要按摩注射部位，24小时内不要做面部激烈运动',
    status: 'completed',
    createdAt: '2024-05-20T15:45:00Z'
  }
];

// 模拟医生服务数据接口
export const doctorService = {
  // 获取患者列表
  async getPatients(): Promise<Patient[]> {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 500));
    return mockPatients;
  },
  
  // 获取紧急/需要关注的患者
  async getUrgentPatients(): Promise<Patient[]> {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 300));
    return mockPatients.filter(patient => 
      patient.urgency === 'high' || patient.urgency === 'medium'
    );
  },
  
  // 根据ID获取患者详情
  async getPatientById(id: string): Promise<Patient | null> {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 300));
    return mockPatients.find(patient => patient.id === id) || null;
  },
  
  // 获取治疗方案列表
  async getTreatmentPlans(): Promise<TreatmentPlan[]> {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 600));
    return mockTreatmentPlans;
  },
  
  // 根据ID获取治疗方案详情
  async getTreatmentPlanById(id: string): Promise<TreatmentPlan | null> {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 400));
    return mockTreatmentPlans.find(plan => plan.id === id) || null;
  },
  
  // 创建新治疗方案
  async createTreatmentPlan(plan: Omit<TreatmentPlan, 'id'>): Promise<TreatmentPlan> {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // 模拟创建新方案（生成随机ID）
    const newPlan: TreatmentPlan = {
      id: `plan-${Date.now()}`,
      ...plan,
      createdAt: new Date().toISOString(),
    };
    
    // 实际应用中，这里会发送 POST 请求到后端
    return newPlan;
  },
  
  // 检查用药冲突
  async checkDrugConflicts(medications: string[]): Promise<{
    hasConflicts: boolean;
    conflicts: DrugConflict[];
  }> {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 700));
    
    // 模拟冲突检测逻辑
    const conflicts: DrugConflict[] = [];
    
    // 这里只是简单演示，实际应用中会有更复杂的冲突检测算法
    if (medications.includes('苯海拉明') && medications.includes('酮咯酸')) {
      conflicts.push({
        drug1: '苯海拉明',
        drug2: '酮咯酸',
        severity: 'medium',
        description: '联合用药可能增加中枢神经系统抑制风险',
      });
    }
    
    if (medications.includes('利多卡因') && medications.includes('普萘洛尔')) {
      conflicts.push({
        drug1: '利多卡因',
        drug2: '普萘洛尔',
        severity: 'high',
        description: '可能导致严重心脏不良反应',
      });
    }
    
    return {
      hasConflicts: conflicts.length > 0,
      conflicts
    };
  },
  
  // 获取风险评估
  async getRiskAssessment(patientId: string, medications: string[]): Promise<{
    overallRisk: 'high' | 'medium' | 'low';
    factors: RiskFactor[];
  }> {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 900));
    
    // 获取患者数据
    const patient = await this.getPatientById(patientId);
    
    if (!patient) {
      throw new Error('患者不存在');
    }
    
    // 模拟风险评估逻辑
    const factors: RiskFactor[] = [];
    
    // 根据患者年龄评估风险
    if (patient.age > 65) {
      factors.push({
        factor: '高龄',
        severity: 'medium',
        description: '患者年龄大于65岁，可能影响药物代谢',
      });
    }
    
    // 根据患者病史评估风险
    if (patient.medicalHistory.some(h => h.type === 'allergy')) {
      factors.push({
        factor: '过敏史',
        severity: 'high',
        description: '患者有过敏史，使用药物时需谨慎',
      });
    }
    
    if (patient.medicalHistory.some(h => h.type === 'heart')) {
      factors.push({
        factor: '心脏病史',
        severity: 'high',
        description: '患者有心脏病史，某些手术可能增加风险',
      });
    }
    
    // 确定总体风险等级
    let overallRisk: 'high' | 'medium' | 'low' = 'low';
    
    if (factors.some(f => f.severity === 'high')) {
      overallRisk = 'high';
    } else if (factors.some(f => f.severity === 'medium')) {
      overallRisk = 'medium';
    }
    
    return {
      overallRisk,
      factors
    };
  },
  
  // 获取全部预约
  async getAppointments(): Promise<DoctorAppointment[]> {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 500));
    return mockDoctorAppointments;
  },
  
  // 获取今日预约
  async getTodayAppointments(): Promise<DoctorAppointment[]> {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 300));
    
    // 获取今天的日期字符串（格式：YYYY-MM-DD）
    const today = new Date().toISOString().split('T')[0];
    
    // 过滤今日预约
    return mockDoctorAppointments.filter(appointment => 
      appointment.date === today
    );
  },
  
  // 更新治疗方案
  async updateTreatmentPlan(plan: TreatmentPlan): Promise<TreatmentPlan> {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // 模拟更新逻辑，实际应用中应发送PUT/PATCH请求到服务器
    // 在这个模拟环境中，我们假设更新成功并返回更新后的方案
    return {
      ...plan,
      updatedAt: new Date().toISOString()
    };
  },

  // 获取全部治疗记录
  async getTreatments(): Promise<Treatment[]> {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 600));
    return mockTreatments;
  },

  // 根据患者ID获取治疗记录
  async getTreatmentsByPatientId(patientId: string): Promise<Treatment[]> {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 400));
    return mockTreatments.filter(treatment => treatment.patientId === patientId);
  },

  // 根据ID获取治疗记录详情
  async getTreatmentById(id: string): Promise<Treatment | null> {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 300));
    return mockTreatments.find(treatment => treatment.id === id) || null;
  },

  // 创建新治疗记录
  async createTreatment(treatment: Omit<Treatment, 'id' | 'createdAt'>): Promise<Treatment> {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 700));
    
    // 模拟创建新记录（生成随机ID）
    const newTreatment: Treatment = {
      id: `treatment-${Date.now()}`,
      ...treatment,
      createdAt: new Date().toISOString(),
    };
    
    // 实际应用中，这里会发送 POST 请求到后端
    return newTreatment;
  },

  // 更新治疗记录
  async updateTreatment(treatment: Treatment): Promise<Treatment> {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 600));
    
    // 模拟更新逻辑，实际应用中应发送PUT/PATCH请求到服务器
    return {
      ...treatment,
      updatedAt: new Date().toISOString()
    };
  },

  // 创建新预约
  async createAppointment(appointment: Omit<DoctorAppointment, 'id'>): Promise<DoctorAppointment> {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 模拟创建新预约（生成随机ID）
    const newAppointment: DoctorAppointment = {
      id: `appt-${Date.now()}`,
      ...appointment,
    };
    
    // 实际应用中，这里会发送 POST 请求到后端
    return newAppointment;
  },

  // 更新预约状态
  async updateAppointmentStatus(
    id: string, 
    status: DoctorAppointment['status']
  ): Promise<DoctorAppointment> {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 400));
    
    // 查找预约
    const appointment = mockDoctorAppointments.find(a => a.id === id);
    
    if (!appointment) {
      throw new Error('预约不存在');
    }
    
    // 更新状态
    const updatedAppointment = {
      ...appointment,
      status,
    };
    
    // 实际应用中，这里会发送 PATCH 请求到后端
    return updatedAppointment;
  }
}; 