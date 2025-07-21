'use client';

import { useForm } from 'react-hook-form';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';


interface GeneralSettings {
  siteName: string;
  logoUrl: string;
  maintenanceMode: boolean;
}

interface GeneralSettingsPanelProps {
  settings: GeneralSettings;
  onSubmit: (data: GeneralSettings) => Promise<void>;
  isSubmitting: boolean;
}

export default function GeneralSettingsPanel({ 
  settings, 
  onSubmit, 
  isSubmitting 
}: GeneralSettingsPanelProps) {
  const { register, handleSubmit, formState: { errors }, reset } = useForm<GeneralSettings>({
    defaultValues: settings
  });

  const handleFormSubmit = async (data: GeneralSettings) => {
    await onSubmit(data);
  };

  const handleReset = () => {
    reset(settings);
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow">
      <h2 className="mb-4 text-xl font-semibold text-gray-800">基本系统设置</h2>
      
      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
        <div>
          <Label htmlFor="siteName" className="mb-2 block text-sm font-medium text-gray-700">
            系统名称
          </Label>
          <Input
            id="siteName"
            type="text"
            {...register('siteName', { required: '系统名称不能为空' })}
            className="w-full"
          />
          {errors.siteName && (
            <p className="mt-1 text-sm text-red-600">{errors.siteName.message}</p>
          )}
        </div>
        
        <div>
          <Label htmlFor="logoUrl" className="mb-2 block text-sm font-medium text-gray-700">
            Logo URL
          </Label>
          <Input
            id="logoUrl"
            type="text"
            {...register('logoUrl')}
            className="w-full"
          />
        </div>
        
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="maintenanceMode"
            {...register('maintenanceMode')}
            className="h-4 w-4 rounded border-gray-300 text-orange-600 focus:ring-orange-500"
          />
          <Label htmlFor="maintenanceMode" className="text-sm text-gray-700">
            启用维护模式
          </Label>
        </div>

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