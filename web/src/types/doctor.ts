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