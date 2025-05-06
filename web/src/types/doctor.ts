export interface Patient {
  id: string;
  name: string;
  avatar: string;
  age: number;
  gender: 'male' | 'female' | 'other';
  phone: string;
  email?: string;
  treatment?: string;
  date?: string;
  urgency?: 'high' | 'medium' | 'low';
  medicalHistory: Array<{
    id: string;
    type: string;
    description: string;
    date: string;
  }>;
  allergies: string[];
  needsFollowUp?: boolean;
  lastVisit: string;
  treatments: string[];
}

export interface Medication {
  id: string;
  name: string;
  dosage: string;
  frequency: string;
  duration: string;
  notes?: string;
}

export interface TreatmentProcedure {
  id: string;
  name: string;
  description: string;
  duration: string;
  notes?: string;
}

export interface TreatmentPlan {
  id: string;
  patientId: string;
  patientName: string;
  doctorId: string;
  doctorName: string;
  diagnosis: string;
  medications: Medication[];
  procedures: TreatmentProcedure[];
  createdAt: string;
  updatedAt?: string;
  status: 'draft' | 'pending' | 'approved' | 'completed' | 'cancelled';
  notes?: string;
  followUpDate?: string;
}

// 治疗记录类型
export interface Treatment {
  id: string;
  patientId: string;
  patientName: string;
  doctorId: string;
  doctorName: string;
  planId?: string; // 关联的治疗方案ID
  treatmentType: string; // 治疗类型
  date: string; // 治疗日期
  duration: number; // 持续时间（分钟）
  details: string; // 治疗详情描述
  procedures: TreatmentProcedure[]; // 实际执行的治疗项目
  medications: Medication[]; // 使用的药物
  outcome: string; // 治疗结果/效果
  complications?: string; // 并发症/副作用（如有）
  followUpRequired: boolean; // 是否需要随访
  followUpDate?: string; // 下次随访日期
  notes?: string; // 其他备注
  attachments?: string[]; // 附件（如图片、文档链接等）
  status: 'completed' | 'cancelled' | 'in-progress'; // 状态
  createdAt: string; // 记录创建时间
  updatedAt?: string; // 记录更新时间
}

export interface DoctorAppointment {
  id: string;
  patientId: string;
  patientName: string;
  date: string;
  time: string;
  duration: number; // 分钟
  treatmentType: string;
  description?: string;
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed';
  notes?: string;
}

// 药物冲突类型
export interface DrugConflict {
  drug1: string;
  drug2: string;
  severity: 'high' | 'medium' | 'low';
  description: string;
}

// 风险因素类型
export interface RiskFactor {
  factor: string;
  severity: 'high' | 'medium' | 'low';
  description: string;
} 