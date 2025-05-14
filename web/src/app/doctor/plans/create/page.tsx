'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { doctorService } from '@/service/doctorService';
import { Patient, Medication, TreatmentProcedure } from '@/types/doctor';

// 药物输入行组件
function MedicationRow({
  medication,
  index,
  onChange,
  onRemove,
  onCheckConflicts
}: {
  medication: Medication;
  index: number;
  onChange: (index: number, field: keyof Medication, value: string) => void;
  onRemove: (index: number) => void;
  onCheckConflicts: () => void;
}) {
  return (
    <div className="mb-2 grid grid-cols-12 gap-2">
      <div className="col-span-3">
        <input
          type="text"
          value={medication.name}
          onChange={(e) => onChange(index, 'name', e.target.value)}
          onBlur={onCheckConflicts}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none"
          placeholder="药物名称"
        />
      </div>
      <div className="col-span-2">
        <input
          type="text"
          value={medication.dosage}
          onChange={(e) => onChange(index, 'dosage', e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none"
          placeholder="剂量"
        />
      </div>
      <div className="col-span-2">
        <input
          type="text"
          value={medication.frequency}
          onChange={(e) => onChange(index, 'frequency', e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none"
          placeholder="频率"
        />
      </div>
      <div className="col-span-2">
        <input
          type="text"
          value={medication.duration}
          onChange={(e) => onChange(index, 'duration', e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none"
          placeholder="持续时间"
        />
      </div>
      <div className="col-span-2">
        <input
          type="text"
          value={medication.notes || ''}
          onChange={(e) => onChange(index, 'notes', e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none"
          placeholder="备注"
        />
      </div>
      <div className="col-span-1 flex items-center justify-center">
        <button
          type="button"
          onClick={() => onRemove(index)}
          className="rounded-full p-1 text-red-500 hover:bg-red-50"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}

// 治疗项目输入行组件
function ProcedureRow({
  procedure,
  index,
  onChange,
  onRemove
}: {
  procedure: TreatmentProcedure;
  index: number;
  onChange: (index: number, field: keyof TreatmentProcedure, value: string) => void;
  onRemove: (index: number) => void;
}) {
  return (
    <div className="mb-2 grid grid-cols-12 gap-2">
      <div className="col-span-3">
        <input
          type="text"
          value={procedure.name}
          onChange={(e) => onChange(index, 'name', e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none"
          placeholder="项目名称"
        />
      </div>
      <div className="col-span-4">
        <input
          type="text"
          value={procedure.description}
          onChange={(e) => onChange(index, 'description', e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none"
          placeholder="描述"
        />
      </div>
      <div className="col-span-2">
        <input
          type="text"
          value={procedure.duration}
          onChange={(e) => onChange(index, 'duration', e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none"
          placeholder="持续时间"
        />
      </div>
      <div className="col-span-2">
        <input
          type="text"
          value={procedure.notes || ''}
          onChange={(e) => onChange(index, 'notes', e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none"
          placeholder="备注"
        />
      </div>
      <div className="col-span-1 flex items-center justify-center">
        <button
          type="button"
          onClick={() => onRemove(index)}
          className="rounded-full p-1 text-red-500 hover:bg-red-50"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}

// 冲突警告组件
function ConflictWarning({
  conflicts
}: {
  conflicts: Array<{
    drug1: string;
    drug2: string;
    severity: 'high' | 'medium' | 'low';
    description: string;
  }>;
}) {
  if (conflicts.length === 0) return null;
  
  return (
    <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
      <div className="flex items-center">
        <svg className="mr-2 h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <h3 className="text-lg font-medium text-red-800">检测到用药冲突</h3>
      </div>
      
      <div className="mt-3 space-y-2">
        {conflicts.map((conflict, index) => (
          <div key={index} className="rounded-md border border-red-200 bg-white p-3">
            <div className="flex items-center justify-between">
              <div className="font-medium">
                <span className="text-red-800">{conflict.drug1}</span>
                <span className="mx-2 text-gray-500">与</span>
                <span className="text-red-800">{conflict.drug2}</span>
              </div>
              <span className={`rounded-full px-2 py-1 text-xs ${
                conflict.severity === 'high' 
                  ? 'bg-red-100 text-red-800' 
                  : conflict.severity === 'medium'
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-blue-100 text-blue-800'
              }`}>
                {conflict.severity === 'high' ? '高风险' : conflict.severity === 'medium' ? '中风险' : '低风险'}
              </span>
            </div>
            <p className="mt-1 text-sm text-gray-600">{conflict.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// 风险评估组件
function RiskAssessment({
  overallRisk,
  factors
}: {
  overallRisk: 'high' | 'medium' | 'low';
  factors: Array<{
    factor: string;
    severity: 'high' | 'medium' | 'low';
    description: string;
  }>;
}) {
  if (factors.length === 0) return null;
  
  const riskColorClass = 
    overallRisk === 'high' 
      ? 'bg-red-50 border-red-200' 
      : overallRisk === 'medium'
      ? 'bg-yellow-50 border-yellow-200'
      : 'bg-blue-50 border-blue-200';
      
  const riskTextClass = 
    overallRisk === 'high' 
      ? 'text-red-800' 
      : overallRisk === 'medium'
      ? 'text-yellow-800'
      : 'text-blue-800';
  
  return (
    <div className={`mb-6 rounded-lg border p-4 ${riskColorClass}`}>
      <div className="flex items-center">
        <svg className={`mr-2 h-5 w-5 ${riskTextClass}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 className={`text-lg font-medium ${riskTextClass}`}>
          风险评估: {overallRisk === 'high' ? '高风险' : overallRisk === 'medium' ? '中等风险' : '低风险'}
        </h3>
      </div>
      
      <div className="mt-3 space-y-2">
        {factors.map((factor, index) => (
          <div key={index} className="rounded-md border border-gray-200 bg-white p-3">
            <div className="flex items-center justify-between">
              <div className="font-medium text-gray-800">{factor.factor}</div>
              <span className={`rounded-full px-2 py-1 text-xs ${
                factor.severity === 'high' 
                  ? 'bg-red-100 text-red-800' 
                  : factor.severity === 'medium'
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-blue-100 text-blue-800'
              }`}>
                {factor.severity === 'high' ? '高风险' : factor.severity === 'medium' ? '中风险' : '低风险'}
              </span>
            </div>
            <p className="mt-1 text-sm text-gray-600">{factor.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function CreateTreatmentPlanPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<string>('');
  const [diagnosis, setDiagnosis] = useState('');
  const [medications, setMedications] = useState<Medication[]>([]);
  const [procedures, setProcedures] = useState<TreatmentProcedure[]>([]);
  const [notes, setNotes] = useState('');
  const [followUpDate, setFollowUpDate] = useState('');
  
  // 冲突和风险状态
  const [conflicts, setConflicts] = useState<Array<{
    drug1: string;
    drug2: string;
    severity: 'high' | 'medium' | 'low';
    description: string;
  }>>([]);
  const [riskAssessment, setRiskAssessment] = useState<{
    overallRisk: 'high' | 'medium' | 'low';
    factors: Array<{
      factor: string;
      severity: 'high' | 'medium' | 'low';
      description: string;
    }>;
  } | null>(null);
  
  // 加载患者数据
  useEffect(() => {
    const loadPatients = async () => {
      try {
        const data = await doctorService.getPatients();
        setPatients(data);
        
        // 默认选中第一个患者
        if (data.length > 0) {
          setSelectedPatient(data[0].id);
        }
      } catch (error) {
        console.error('加载患者数据失败', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadPatients();
  }, []);
  
  // 添加新药物
  const addMedication = () => {
    const newMed: Medication = {
      id: `temp-med-${Date.now()}`,
      name: '',
      dosage: '',
      frequency: '',
      duration: '',
      notes: ''
    };
    
    setMedications([...medications, newMed]);
  };
  
  // 更新药物信息
  const updateMedication = (index: number, field: keyof Medication, value: string) => {
    const updatedMeds = [...medications];
    updatedMeds[index] = { ...updatedMeds[index], [field]: value };
    setMedications(updatedMeds);
  };
  
  // 删除药物
  const removeMedication = (index: number) => {
    const updatedMeds = [...medications];
    updatedMeds.splice(index, 1);
    setMedications(updatedMeds);
    
    // 重新检查冲突
    checkDrugConflicts();
  };
  
  // 添加新治疗项目
  const addProcedure = () => {
    const newProc: TreatmentProcedure = {
      id: `temp-proc-${Date.now()}`,
      name: '',
      description: '',
      duration: '',
      notes: ''
    };
    
    setProcedures([...procedures, newProc]);
  };
  
  // 更新治疗项目信息
  const updateProcedure = (index: number, field: keyof TreatmentProcedure, value: string) => {
    const updatedProcs = [...procedures];
    updatedProcs[index] = { ...updatedProcs[index], [field]: value };
    setProcedures(updatedProcs);
  };
  
  // 删除治疗项目
  const removeProcedure = (index: number) => {
    const updatedProcs = [...procedures];
    updatedProcs.splice(index, 1);
    setProcedures(updatedProcs);
  };
  
  // 检查药物冲突
  const checkDrugConflicts = async () => {
    if (medications.length < 2) {
      setConflicts([]);
      return;
    }
    
    try {
      const medicationNames = medications
        .filter(med => med.name.trim() !== '')
        .map(med => med.name);
      
      if (medicationNames.length < 2) {
        setConflicts([]);
        return;
      }
      
      const result = await doctorService.checkDrugConflicts(medicationNames);
      setConflicts(result.conflicts);
    } catch (error) {
      console.error('检查药物冲突失败', error);
    }
  };
  
  // 评估风险
  const assessRisk = async () => {
    if (!selectedPatient) return;
    
    try {
      const medicationNames = medications
        .filter(med => med.name.trim() !== '')
        .map(med => med.name);
      
      const result = await doctorService.getRiskAssessment(selectedPatient, medicationNames);
      setRiskAssessment(result);
    } catch (error) {
      console.error('评估风险失败', error);
    }
  };
  
  // 患者选择变更时重新评估风险
  useEffect(() => {
    if (selectedPatient) {
      assessRisk();
    }
  }, [selectedPatient]);
  
  // 药物变更时重新检查冲突和评估风险
  useEffect(() => {
    checkDrugConflicts();
    assessRisk();
  }, [medications]);
  
  // 保存方案
  const savePlan = async () => {
    if (!selectedPatient || !diagnosis || medications.length === 0 || procedures.length === 0) {
      alert('请填写完整的方案信息');
      return;
    }
    
    try {
      setSaving(true);
      
      // 查找患者信息
      const patient = patients.find(p => p.id === selectedPatient);
      
      // 创建新方案
      const newPlan = await doctorService.createTreatmentPlan({
        patientId: selectedPatient,
        patientName: patient?.name || '',
        doctorId: '1', // 假设当前医生ID为1
        doctorName: '张医生', // 假设当前医生为张医生
        diagnosis,
        medications,
        procedures,
        createdAt: new Date().toISOString(),
        status: 'draft',
        notes: notes || undefined,
        followUpDate: followUpDate || undefined
      });
      
      // 跳转到方案列表页
      router.push('/doctor/plans');
    } catch (error) {
      console.error('保存方案失败', error);
      alert('保存方案失败，请重试');
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
        <h1 className="text-2xl font-bold text-gray-800">创建治疗方案</h1>
        <p className="text-gray-600">录入患者的治疗方案信息</p>
      </div>
      
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <div className="mb-6 grid grid-cols-1 gap-6 md:grid-cols-2">
          {/* 患者选择 */}
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              选择患者
            </label>
            <select
              value={selectedPatient}
              onChange={(e) => setSelectedPatient(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
            >
              <option value="">-- 选择患者 --</option>
              {patients.map((patient) => (
                <option key={patient.id} value={patient.id}>
                  {patient.name} ({patient.gender === 'male' ? '男' : '女'}, {patient.age}岁)
                </option>
              ))}
            </select>
          </div>
          
          {/* 随访日期 */}
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              随访日期（可选）
            </label>
            <input
              type="date"
              value={followUpDate}
              onChange={(e) => setFollowUpDate(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
            />
          </div>
        </div>
        
        {/* 诊断 */}
        <div className="mb-6">
          <label className="mb-2 block text-sm font-medium text-gray-700">
            诊断
          </label>
          <textarea
            value={diagnosis}
            onChange={(e) => setDiagnosis(e.target.value)}
            rows={3}
            className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
            placeholder="请输入诊断信息"
          />
        </div>
        
        {/* 药物列表 */}
        <div className="mb-6">
          <div className="mb-2 flex items-center justify-between">
            <label className="block text-sm font-medium text-gray-700">
              药物
            </label>
            <button
              type="button"
              onClick={addMedication}
              className="flex items-center rounded-md bg-white px-3 py-1 text-sm font-medium text-orange-600 hover:bg-orange-50"
            >
              <svg className="mr-1 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              添加药物
            </button>
          </div>
          
          {medications.length > 0 ? (
            <div>
              <div className="mb-1 grid grid-cols-12 gap-2 text-xs font-medium text-gray-500">
                <div className="col-span-3">药物名称</div>
                <div className="col-span-2">剂量</div>
                <div className="col-span-2">频率</div>
                <div className="col-span-2">持续时间</div>
                <div className="col-span-2">备注</div>
                <div className="col-span-1"></div>
              </div>
              
              {medications.map((medication, index) => (
                <MedicationRow
                  key={medication.id}
                  medication={medication}
                  index={index}
                  onChange={updateMedication}
                  onRemove={removeMedication}
                  onCheckConflicts={checkDrugConflicts}
                />
              ))}
            </div>
          ) : (
            <div className="rounded-md border border-gray-200 bg-gray-50 p-4 text-center text-sm text-gray-500">
              尚未添加药物
            </div>
          )}
        </div>
        
        {/* 冲突检测结果 */}
        <ConflictWarning conflicts={conflicts} />
        
        {/* 风险评估结果 */}
        {riskAssessment && (
          <RiskAssessment
            overallRisk={riskAssessment.overallRisk}
            factors={riskAssessment.factors}
          />
        )}
        
        {/* 治疗项目列表 */}
        <div className="mb-6">
          <div className="mb-2 flex items-center justify-between">
            <label className="block text-sm font-medium text-gray-700">
              治疗项目
            </label>
            <button
              type="button"
              onClick={addProcedure}
              className="flex items-center rounded-md bg-white px-3 py-1 text-sm font-medium text-orange-600 hover:bg-orange-50"
            >
              <svg className="mr-1 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              添加项目
            </button>
          </div>
          
          {procedures.length > 0 ? (
            <div>
              <div className="mb-1 grid grid-cols-12 gap-2 text-xs font-medium text-gray-500">
                <div className="col-span-3">项目名称</div>
                <div className="col-span-4">描述</div>
                <div className="col-span-2">持续时间</div>
                <div className="col-span-2">备注</div>
                <div className="col-span-1"></div>
              </div>
              
              {procedures.map((procedure, index) => (
                <ProcedureRow
                  key={procedure.id}
                  procedure={procedure}
                  index={index}
                  onChange={updateProcedure}
                  onRemove={removeProcedure}
                />
              ))}
            </div>
          ) : (
            <div className="rounded-md border border-gray-200 bg-gray-50 p-4 text-center text-sm text-gray-500">
              尚未添加治疗项目
            </div>
          )}
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
            onClick={() => router.push('/doctor/plans')}
            className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
            disabled={saving}
          >
            取消
          </button>
          <button
            type="button"
            onClick={savePlan}
            className="rounded-md bg-orange-500 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-orange-600"
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
            ) : '保存方案'}
          </button>
        </div>
      </div>
    </div>
  );
} 