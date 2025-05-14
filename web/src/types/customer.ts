export interface Treatment {
  id: string;
  name: string;
  date: string;
  doctor: string;
  status: 'completed' | 'scheduled' | 'canceled';
  description: string;
  beforeImages?: string[];
  afterImages?: string[];
}

export interface TreatmentPlan {
  id: string;
  title: string;
  createdAt: string;
  doctorName: string;
  status: 'draft' | 'pending' | 'approved' | 'rejected';
  items: {
    name: string;
    description: string;
    price: number;
  }[];
  totalPrice: number;
  notes?: string;
}

export interface CustomerAppointment {
  id: string;
  type: 'consultation' | 'treatment' | 'followup';
  title: string;
  date: string;
  time: string;
  consultant?: string;
  doctor?: string;
  status: 'confirmed' | 'pending' | 'canceled' | 'completed';
  notes?: string;
} 