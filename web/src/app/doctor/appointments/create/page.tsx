'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { doctorService } from '@/lib/doctorService';
import { Patient, DoctorAppointment } from '@/types/doctor';

export default function CreateAppointmentPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [patients, setPatients] = useState<Patient[]>([]);
  
  // 表单状态
  const [patientId, setPatientId] = useState('');
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [duration, setDuration] = useState('30');
  const [treatmentType, setTreatmentType] = useState('');
  const [description, setDescription] = useState('');
  const [notes, setNotes] = useState('');
  
  // 字段验证状态
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  // 加载患者数据
  useEffect(() => {
    const loadPatients = async () => {
      try {
        setLoading(true);
        const data = await doctorService.getPatients();
        setPatients(data);
      } catch (error) {
        console.error('加载患者数据失败', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadPatients();
  }, []);
  
  // 设置默认日期为明天
  useEffect(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowStr = tomorrow.toISOString().split('T')[0];
    setDate(tomorrowStr);
  }, []);
  
  // 验证表单
  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!patientId) {
      newErrors.patientId = '请选择患者';
    }
    
    if (!date) {
      newErrors.date = '请选择日期';
    }
    
    if (!time) {
      newErrors.time = '请选择时间';
    }
    
    if (!treatmentType) {
      newErrors.treatmentType = '请输入治疗类型';
    }
    
    if (!duration || isNaN(Number(duration)) || Number(duration) <= 0) {
      newErrors.duration = '请输入有效的持续时间';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  // 创建预约
  const createAppointment = async () => {
    if (!validateForm()) {
      return;
    }
    
    try {
      setSaving(true);
      
      // 查找患者信息
      const patient = patients.find(p => p.id === patientId);
      if (!patient) {
        setErrors({ patientId: '患者不存在' });
        return;
      }
      
      // 创建新预约
      const newAppointment: Omit<DoctorAppointment, 'id'> = {
        patientId,
        patientName: patient.name,
        date,
        time,
        duration: Number(duration),
        treatmentType,
        description: description || undefined,
        notes: notes || undefined,
        status: 'pending'
      };
      
      // 保存新预约
      await doctorService.createAppointment(newAppointment);
      
      // 跳转到预约列表页
      router.push('/doctor/appointments');
    } catch (error) {
      console.error('创建预约失败', error);
      alert('创建预约失败，请重试');
    } finally {
      setSaving(false);
    }
  };
  
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-orange-500 border-t-transparent"></div>
      </div>
    );
  }
  
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">创建新预约</h1>
        <p className="text-gray-600">为患者安排新的预约时间</p>
      </div>
      
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        {/* 患者选择 */}
        <div className="mb-6">
          <label className="mb-2 block text-sm font-medium text-gray-700">
            选择患者 <span className="text-red-500">*</span>
          </label>
          <select
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            className={`w-full rounded-md border ${
              errors.patientId ? 'border-red-500' : 'border-gray-300'
            } px-3 py-2 focus:border-orange-500 focus:outline-none`}
          >
            <option value="">-- 选择患者 --</option>
            {patients.map((patient) => (
              <option key={patient.id} value={patient.id}>
                {patient.name} ({patient.gender === 'male' ? '男' : '女'}, {patient.age}岁)
              </option>
            ))}
          </select>
          {errors.patientId && (
            <p className="mt-1 text-sm text-red-500">{errors.patientId}</p>
          )}
        </div>
        
        {/* 日期和时间 */}
        <div className="mb-6 grid grid-cols-1 gap-6 md:grid-cols-2">
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              预约日期 <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className={`w-full rounded-md border ${
                errors.date ? 'border-red-500' : 'border-gray-300'
              } px-3 py-2 focus:border-orange-500 focus:outline-none`}
            />
            {errors.date && (
              <p className="mt-1 text-sm text-red-500">{errors.date}</p>
            )}
          </div>
          
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              预约时间 <span className="text-red-500">*</span>
            </label>
            <input
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              className={`w-full rounded-md border ${
                errors.time ? 'border-red-500' : 'border-gray-300'
              } px-3 py-2 focus:border-orange-500 focus:outline-none`}
            />
            {errors.time && (
              <p className="mt-1 text-sm text-red-500">{errors.time}</p>
            )}
          </div>
        </div>
        
        {/* 治疗类型和持续时间 */}
        <div className="mb-6 grid grid-cols-1 gap-6 md:grid-cols-2">
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              治疗类型 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={treatmentType}
              onChange={(e) => setTreatmentType(e.target.value)}
              placeholder="如: 双眼皮手术、玻尿酸填充等"
              className={`w-full rounded-md border ${
                errors.treatmentType ? 'border-red-500' : 'border-gray-300'
              } px-3 py-2 focus:border-orange-500 focus:outline-none`}
            />
            {errors.treatmentType && (
              <p className="mt-1 text-sm text-red-500">{errors.treatmentType}</p>
            )}
          </div>
          
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              持续时间(分钟) <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              min="1"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              className={`w-full rounded-md border ${
                errors.duration ? 'border-red-500' : 'border-gray-300'
              } px-3 py-2 focus:border-orange-500 focus:outline-none`}
            />
            {errors.duration && (
              <p className="mt-1 text-sm text-red-500">{errors.duration}</p>
            )}
          </div>
        </div>
        
        {/* 描述 */}
        <div className="mb-6">
          <label className="mb-2 block text-sm font-medium text-gray-700">
            预约描述（可选）
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
            placeholder="请输入预约描述，如患者主诉、特殊需求等"
          />
        </div>
        
        {/* 备注 */}
        <div className="mb-6">
          <label className="mb-2 block text-sm font-medium text-gray-700">
            备注（可选）
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
            placeholder="请输入备注信息"
          />
        </div>
        
        {/* 按钮区域 */}
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => router.push('/doctor/appointments')}
            className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
            disabled={saving}
          >
            取消
          </button>
          <button
            type="button"
            onClick={createAppointment}
            className="rounded-md bg-orange-500 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-orange-600 disabled:opacity-70"
            disabled={saving}
          >
            {saving ? (
              <span className="flex items-center">
                <svg className="mr-2 h-4 w-4 animate-spin" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                保存中...
              </span>
            ) : '创建预约'}
          </button>
        </div>
      </div>
    </div>
  );
} 