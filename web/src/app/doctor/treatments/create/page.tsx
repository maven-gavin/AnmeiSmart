'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { doctorService } from '@/lib/doctorService';
import { Patient, Treatment, TreatmentProcedure, Medication } from '@/types/doctor';

export default function CreateTreatmentPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [patients, setPatients] = useState<Patient[]>([]);
  
  // 表单状态
  const [patientId, setPatientId] = useState('');
  const [treatmentType, setTreatmentType] = useState('');
  const [date, setDate] = useState('');
  const [duration, setDuration] = useState('60');
  const [details, setDetails] = useState('');
  const [outcome, setOutcome] = useState('');
  const [complications, setComplications] = useState('');
  const [followUpRequired, setFollowUpRequired] = useState(false);
  const [followUpDate, setFollowUpDate] = useState('');
  const [notes, setNotes] = useState('');
  const [status, setStatus] = useState<Treatment['status']>('in-progress');
  
  // 治疗项目和药物
  const [procedures, setProcedures] = useState<Omit<TreatmentProcedure, 'id'>[]>([
    { name: '', description: '', duration: '', notes: '' }
  ]);
  const [medications, setMedications] = useState<Omit<Medication, 'id'>[]>([
    { name: '', dosage: '', frequency: '', duration: '', notes: '' }
  ]);
  
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
  
  // 设置默认日期为今天
  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    setDate(today);
  }, []);
  
  // 添加治疗项目
  const addProcedure = () => {
    setProcedures([...procedures, { name: '', description: '', duration: '', notes: '' }]);
  };
  
  // 删除治疗项目
  const removeProcedure = (index: number) => {
    if (procedures.length > 1) {
      setProcedures(procedures.filter((_, i) => i !== index));
    }
  };
  
  // 更新治疗项目
  const updateProcedure = (index: number, field: keyof TreatmentProcedure, value: string) => {
    const updatedProcedures = [...procedures];
    updatedProcedures[index] = { ...updatedProcedures[index], [field]: value };
    setProcedures(updatedProcedures);
  };
  
  // 添加药物
  const addMedication = () => {
    setMedications([...medications, { name: '', dosage: '', frequency: '', duration: '', notes: '' }]);
  };
  
  // 删除药物
  const removeMedication = (index: number) => {
    if (medications.length > 1) {
      setMedications(medications.filter((_, i) => i !== index));
    }
  };
  
  // 更新药物
  const updateMedication = (index: number, field: keyof Medication, value: string) => {
    const updatedMedications = [...medications];
    updatedMedications[index] = { ...updatedMedications[index], [field]: value };
    setMedications(updatedMedications);
  };
  
  // 验证表单
  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!patientId) {
      newErrors.patientId = '请选择患者';
    }
    
    if (!treatmentType) {
      newErrors.treatmentType = '请输入治疗类型';
    }
    
    if (!date) {
      newErrors.date = '请选择日期';
    }
    
    if (!duration || isNaN(Number(duration)) || Number(duration) <= 0) {
      newErrors.duration = '请输入有效的持续时间';
    }
    
    if (!details) {
      newErrors.details = '请输入治疗详情';
    }
    
    if (!outcome) {
      newErrors.outcome = '请输入治疗效果';
    }
    
    if (followUpRequired && !followUpDate) {
      newErrors.followUpDate = '请选择随访日期';
    }
    
    // 验证治疗项目
    const validProcedures = procedures.filter(p => p.name.trim() !== '');
    if (validProcedures.length === 0) {
      newErrors.procedures = '请至少添加一个治疗项目';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  // 创建治疗记录
  const createTreatment = async () => {
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
      
      // 处理治疗项目和药物，过滤掉空项目
      const validProcedures = procedures
        .filter(p => p.name.trim() !== '')
        .map(p => ({ ...p }));
        
      const validMedications = medications
        .filter(m => m.name.trim() !== '')
        .map(m => ({ ...m }));
      
      // 创建新治疗记录
      const newTreatment: Omit<Treatment, 'id' | 'createdAt'> = {
        patientId,
        patientName: patient.name,
        doctorId: '1', // 假设当前登录的医生ID为1
        doctorName: '张医生', // 假设当前登录的医生姓名
        planId: undefined, // 暂不关联治疗方案
        treatmentType,
        date,
        duration: Number(duration),
        details,
        procedures: validProcedures as TreatmentProcedure[],
        medications: validMedications as Medication[],
        outcome,
        complications: complications || undefined,
        followUpRequired,
        followUpDate: followUpRequired ? followUpDate : undefined,
        notes: notes || undefined,
        attachments: undefined, // 暂不支持附件上传
        status,
        updatedAt: undefined
      };
      
      // 保存新治疗记录
      await doctorService.createTreatment(newTreatment);
      
      // 跳转到治疗记录列表页
      router.push('/doctor/treatments');
    } catch (error) {
      console.error('创建治疗记录失败', error);
      alert('创建治疗记录失败，请重试');
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
        <h1 className="text-2xl font-bold text-gray-800">创建治疗记录</h1>
        <p className="text-gray-600">记录患者的治疗信息</p>
      </div>
      
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <div className="space-y-6">
          {/* 基本信息部分 */}
          <div>
            <h2 className="mb-4 text-lg font-medium text-gray-800">基本信息</h2>
            
            {/* 患者选择 */}
            <div className="mb-4">
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
            
            {/* 治疗类型 */}
            <div className="mb-4">
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
            
            {/* 日期和时间 */}
            <div className="mb-4 grid grid-cols-1 gap-6 md:grid-cols-2">
              <div>
                <label className="mb-2 block text-sm font-medium text-gray-700">
                  治疗日期 <span className="text-red-500">*</span>
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
            
            {/* 治疗详情 */}
            <div className="mb-4">
              <label className="mb-2 block text-sm font-medium text-gray-700">
                治疗详情 <span className="text-red-500">*</span>
              </label>
              <textarea
                value={details}
                onChange={(e) => setDetails(e.target.value)}
                rows={3}
                className={`w-full rounded-md border ${
                  errors.details ? 'border-red-500' : 'border-gray-300'
                } px-3 py-2 focus:border-orange-500 focus:outline-none`}
                placeholder="请详细描述治疗过程和内容"
              />
              {errors.details && (
                <p className="mt-1 text-sm text-red-500">{errors.details}</p>
              )}
            </div>
            
            {/* 治疗状态 */}
            <div className="mb-4">
              <label className="mb-2 block text-sm font-medium text-gray-700">
                治疗状态
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as Treatment['status'])}
                className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
              >
                <option value="in-progress">进行中</option>
                <option value="completed">已完成</option>
                <option value="cancelled">已取消</option>
              </select>
            </div>
          </div>
          
          {/* 治疗项目部分 */}
          <div>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-medium text-gray-800">治疗项目</h2>
              <button
                type="button"
                onClick={addProcedure}
                className="text-sm text-orange-600 hover:text-orange-800"
              >
                + 添加治疗项目
              </button>
            </div>
            
            {errors.procedures && (
              <p className="mb-4 text-sm text-red-500">{errors.procedures}</p>
            )}
            
            {procedures.map((procedure, index) => (
              <div key={index} className="mb-6 rounded-md border border-gray-200 p-4">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-md font-medium text-gray-700">项目 #{index + 1}</h3>
                  {procedures.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeProcedure(index)}
                      className="text-sm text-red-600 hover:text-red-800"
                    >
                      删除
                    </button>
                  )}
                </div>
                
                <div className="mb-3">
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    项目名称 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={procedure.name}
                    onChange={(e) => updateProcedure(index, 'name', e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                    placeholder="如: 双眼皮切开法"
                  />
                </div>
                
                <div className="mb-3">
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    描述
                  </label>
                  <textarea
                    value={procedure.description}
                    onChange={(e) => updateProcedure(index, 'description', e.target.value)}
                    rows={2}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                    placeholder="请描述治疗项目的具体内容"
                  />
                </div>
                
                <div className="mb-3 grid grid-cols-1 gap-3 md:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">
                      持续时间
                    </label>
                    <input
                      type="text"
                      value={procedure.duration}
                      onChange={(e) => updateProcedure(index, 'duration', e.target.value)}
                      className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                      placeholder="如: 2小时"
                    />
                  </div>
                  
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">
                      备注
                    </label>
                    <input
                      type="text"
                      value={procedure.notes || ''}
                      onChange={(e) => updateProcedure(index, 'notes', e.target.value)}
                      className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                      placeholder="可选备注信息"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {/* 药物部分 */}
          <div>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-medium text-gray-800">用药情况</h2>
              <button
                type="button"
                onClick={addMedication}
                className="text-sm text-orange-600 hover:text-orange-800"
              >
                + 添加药物
              </button>
            </div>
            
            {medications.map((medication, index) => (
              <div key={index} className="mb-6 rounded-md border border-gray-200 p-4">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-md font-medium text-gray-700">药物 #{index + 1}</h3>
                  {medications.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeMedication(index)}
                      className="text-sm text-red-600 hover:text-red-800"
                    >
                      删除
                    </button>
                  )}
                </div>
                
                <div className="mb-3 grid grid-cols-1 gap-3 md:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">
                      药物名称
                    </label>
                    <input
                      type="text"
                      value={medication.name}
                      onChange={(e) => updateMedication(index, 'name', e.target.value)}
                      className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                      placeholder="如: 利多卡因"
                    />
                  </div>
                  
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">
                      剂量
                    </label>
                    <input
                      type="text"
                      value={medication.dosage}
                      onChange={(e) => updateMedication(index, 'dosage', e.target.value)}
                      className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                      placeholder="如: 2%"
                    />
                  </div>
                </div>
                
                <div className="mb-3 grid grid-cols-1 gap-3 md:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">
                      频率
                    </label>
                    <input
                      type="text"
                      value={medication.frequency}
                      onChange={(e) => updateMedication(index, 'frequency', e.target.value)}
                      className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                      placeholder="如: 每日2次"
                    />
                  </div>
                  
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">
                      持续时间
                    </label>
                    <input
                      type="text"
                      value={medication.duration}
                      onChange={(e) => updateMedication(index, 'duration', e.target.value)}
                      className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                      placeholder="如: 3天"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    备注
                  </label>
                  <input
                    type="text"
                    value={medication.notes || ''}
                    onChange={(e) => updateMedication(index, 'notes', e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                    placeholder="可选备注信息"
                  />
                </div>
              </div>
            ))}
          </div>
          
          {/* 结果评估部分 */}
          <div>
            <h2 className="mb-4 text-lg font-medium text-gray-800">结果评估</h2>
            
            {/* 治疗效果 */}
            <div className="mb-4">
              <label className="mb-2 block text-sm font-medium text-gray-700">
                治疗效果 <span className="text-red-500">*</span>
              </label>
              <textarea
                value={outcome}
                onChange={(e) => setOutcome(e.target.value)}
                rows={3}
                className={`w-full rounded-md border ${
                  errors.outcome ? 'border-red-500' : 'border-gray-300'
                } px-3 py-2 focus:border-orange-500 focus:outline-none`}
                placeholder="请描述治疗结果和效果"
              />
              {errors.outcome && (
                <p className="mt-1 text-sm text-red-500">{errors.outcome}</p>
              )}
            </div>
            
            {/* 并发症/副作用 */}
            <div className="mb-4">
              <label className="mb-2 block text-sm font-medium text-gray-700">
                并发症/副作用（如有）
              </label>
              <textarea
                value={complications}
                onChange={(e) => setComplications(e.target.value)}
                rows={2}
                className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                placeholder="如有并发症或副作用，请在此描述"
              />
            </div>
            
            {/* 随访需求 */}
            <div className="mb-4">
              <div className="mb-2 flex items-center">
                <input
                  type="checkbox"
                  id="followUpRequired"
                  checked={followUpRequired}
                  onChange={(e) => setFollowUpRequired(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-orange-600 focus:ring-orange-500"
                />
                <label htmlFor="followUpRequired" className="ml-2 block text-sm font-medium text-gray-700">
                  需要随访
                </label>
              </div>
              
              {followUpRequired && (
                <div className="mt-3">
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    随访日期 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    value={followUpDate}
                    onChange={(e) => setFollowUpDate(e.target.value)}
                    className={`w-full rounded-md border ${
                      errors.followUpDate ? 'border-red-500' : 'border-gray-300'
                    } px-3 py-2 focus:border-orange-500 focus:outline-none`}
                  />
                  {errors.followUpDate && (
                    <p className="mt-1 text-sm text-red-500">{errors.followUpDate}</p>
                  )}
                </div>
              )}
            </div>
            
            {/* 备注 */}
            <div className="mb-4">
              <label className="mb-2 block text-sm font-medium text-gray-700">
                其他备注
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                placeholder="请输入其他需要记录的信息"
              />
            </div>
          </div>
        </div>
        
        {/* 按钮区域 */}
        <div className="mt-8 flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => router.push('/doctor/treatments')}
            className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
            disabled={saving}
          >
            取消
          </button>
          <button
            type="button"
            onClick={createTreatment}
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
            ) : '创建治疗记录'}
          </button>
        </div>
      </div>
    </div>
  );
} 