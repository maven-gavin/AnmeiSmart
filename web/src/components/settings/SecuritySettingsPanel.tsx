'use client';

import { useForm } from 'react-hook-form';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';

interface SecuritySettings {
  userRegistrationEnabled: boolean;
}

interface SecuritySettingsPanelProps {
  settings: SecuritySettings;
  onSubmit: (data: SecuritySettings) => Promise<void>;
  isSubmitting: boolean;
}

export default function SecuritySettingsPanel({ 
  settings, 
  onSubmit, 
  isSubmitting 
}: SecuritySettingsPanelProps) {
  const { register, handleSubmit, reset } = useForm<SecuritySettings>({
    defaultValues: settings
  });

  const handleFormSubmit = async (data: SecuritySettings) => {
    await onSubmit(data);
  };

  const handleReset = () => {
    reset(settings);
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow">
      <h2 className="mb-4 text-xl font-semibold text-gray-800">安全与访问控制设置</h2>
      
      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="userRegistrationEnabled"
            {...register('userRegistrationEnabled')}
            className="h-4 w-4 rounded border-gray-300 text-orange-600 focus:ring-orange-500"
          />
          <Label htmlFor="userRegistrationEnabled" className="text-sm text-gray-700">
            允许新用户注册
          </Label>
        </div>
        
        {/* 这里可以添加更多安全相关的设置 */}

        <div className="mt-6 flex justify-end space-x-4">
          <Button
            type="button"
            variant="outline"
            onClick={handleReset}
          >
            重置
          </Button>
          <Button
            type="submit"
            disabled={isSubmitting}
            className="bg-orange-500 hover:bg-orange-600"
          >
            {isSubmitting ? '保存中...' : '保存设置'}
          </Button>
        </div>
      </form>
    </div>
  );
} 