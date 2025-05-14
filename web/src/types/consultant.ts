export interface SimulationImage {
  id: string;
  originalImage: string;
  simulatedImages: {
    id: string;
    image: string;
    projectType: string;
    parameters?: {
      [key: string]: string | number;
    };
  }[];
  customerId: string;
  customerName: string;
  createdAt: string;
  notes?: string;
}

export interface SimulationParameter {
  id: string;
  name: string;
  label: string;
  type: 'slider' | 'select' | 'radio';
  min?: number;
  max?: number;
  step?: number;
  options?: {
    value: string;
    label: string;
  }[];
  defaultValue: string | number;
}

export interface ProjectType {
  id: string;
  name: string;
  label: string;
  description: string;
  parameters: SimulationParameter[];
}

export interface PersonalizedPlan {
  id: string;
  customerId: string;
  customerName: string;
  customerProfile?: {
    age: number;
    gender: 'male' | 'female';
    concerns: string[];
    budget?: number;
    expectedResults?: string;
  };
  projects: {
    id: string;
    name: string;
    description: string;
    cost: number;
    duration: string;
    recoveryTime: string;
    expectedResults: string;
    risks: string[];
  }[];
  totalCost: number;
  estimatedTimeframe: string;
  createdAt: string;
  updatedAt?: string;
  consultantId: string;
  consultantName: string;
  status: 'draft' | 'shared' | 'accepted' | 'rejected';
  notes?: string;
} 