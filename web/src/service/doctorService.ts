import { DrugConflict } from '@/types/doctor';

// 模拟医生服务数据接口
export const doctorService = {
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
  
  
}; 