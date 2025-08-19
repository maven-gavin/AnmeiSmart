'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Upload, User, Building, Zap, Shield } from 'lucide-react';
import toast from 'react-hot-toast';

import type { DigitalHuman, CreateDigitalHumanRequest, UpdateDigitalHumanRequest } from '@/types/digital-human';

interface DigitalHumanFormProps {
  digitalHuman?: DigitalHuman;
  onSubmit: (data: CreateDigitalHumanRequest | UpdateDigitalHumanRequest) => Promise<void>;
  onCancel: () => void;
}

interface FormData {
  name: string;
  description: string;
  type: 'personal' | 'business' | 'specialized' | 'system';
  status: 'active' | 'inactive' | 'maintenance';
  greetingMessage: string;
  welcomeMessage: string;
  personalityTone: string;
  personalityStyle: string;
  personalitySpecialization: string;
}

export default function DigitalHumanForm({
  digitalHuman,
  onSubmit,
  onCancel
}: DigitalHumanFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors }
  } = useForm<FormData>({
    defaultValues: {
      name: digitalHuman?.name || '',
      description: digitalHuman?.description || '',
      type: digitalHuman?.type || 'personal',
      status: digitalHuman?.status || 'active',
      greetingMessage: digitalHuman?.greeting_message || '',
      welcomeMessage: digitalHuman?.welcome_message || '',
      personalityTone: digitalHuman?.personality?.tone || 'friendly',
      personalityStyle: digitalHuman?.personality?.style || 'professional',
      personalitySpecialization: digitalHuman?.personality?.specialization || 'general'
    }
  });

  const watchedType = watch('type');
  const isEditing = !!digitalHuman;
  const isSystemCreated = digitalHuman?.is_system_created;

  useEffect(() => {
    if (digitalHuman?.avatar) {
      setAvatarPreview(digitalHuman.avatar);
    }
  }, [digitalHuman]);

  const handleAvatarChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        toast.error('头像文件大小不能超过 5MB');
        return;
      }

      setAvatarFile(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setAvatarPreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const onFormSubmit = async (data: FormData) => {
    setIsSubmitting(true);
    
    try {
      const submitData: CreateDigitalHumanRequest | UpdateDigitalHumanRequest = {
        name: data.name,
        description: data.description,
        type: data.type,
        status: data.status,
        greeting_message: data.greetingMessage,
        welcome_message: data.welcomeMessage,
        personality: {
          tone: data.personalityTone,
          style: data.personalityStyle,
          specialization: data.personalitySpecialization
        }
      };

      // 如果有头像文件，需要先上传
      if (avatarFile) {
        // TODO: 实现头像上传逻辑
        // submitData.avatar = uploadedAvatarUrl;
      }

      await onSubmit(submitData);
      toast.success(isEditing ? '数字人更新成功' : '数字人创建成功');
    } catch (error) {
      console.error('提交失败:', error);
      toast.error(isEditing ? '数字人更新失败' : '数字人创建失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'personal':
        return <User className="h-4 w-4" />;
      case 'business':
        return <Building className="h-4 w-4" />;
      case 'specialized':
        return <Zap className="h-4 w-4" />;
      case 'system':
        return <Shield className="h-4 w-4" />;
      default:
        return <User className="h-4 w-4" />;
    }
  };

  return (
    <div className="p-6">
      <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
        {/* 头像上传 */}
        <div className="flex flex-col items-center space-y-4">
          <Avatar className="w-24 h-24">
            <AvatarImage src={avatarPreview || undefined} />
            <AvatarFallback className="text-2xl bg-gradient-to-br from-orange-400 to-orange-600 text-white">
              {watch('name')?.charAt(0)?.toUpperCase() || '?'}
            </AvatarFallback>
          </Avatar>
          
          <div className="flex items-center space-x-2">
            <Label htmlFor="avatar-upload" className="cursor-pointer">
              <div className="flex items-center space-x-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
                <Upload className="h-4 w-4" />
                <span className="text-sm">上传头像</span>
              </div>
            </Label>
            <Input
              id="avatar-upload"
              type="file"
              accept="image/*"
              onChange={handleAvatarChange}
              className="hidden"
            />
          </div>
          <p className="text-xs text-gray-500">支持 JPG、PNG 格式，文件大小不超过 5MB</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 基础信息 */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">基础信息</h3>
            
            <div>
              <Label htmlFor="name">数字人名称 *</Label>
              <Input
                id="name"
                {...register('name', { 
                  required: '请输入数字人名称',
                  minLength: { value: 2, message: '名称至少2个字符' },
                  maxLength: { value: 50, message: '名称不能超过50个字符' }
                })}
                placeholder="为您的数字人起一个名字"
                className={errors.name ? 'border-red-500' : ''}
                disabled={isSystemCreated} // 系统创建的数字人名称不可修改
              />
              {errors.name && (
                <p className="text-sm text-red-600 mt-1">{errors.name.message}</p>
              )}
            </div>

            <div>
              <Label htmlFor="description">描述</Label>
              <Textarea
                id="description"
                {...register('description', {
                  maxLength: { value: 200, message: '描述不能超过200个字符' }
                })}
                placeholder="描述这个数字人的功能和特点"
                rows={3}
                className={errors.description ? 'border-red-500' : ''}
              />
              {errors.description && (
                <p className="text-sm text-red-600 mt-1">{errors.description.message}</p>
              )}
            </div>

            <div>
              <Label htmlFor="type">数字人类型 *</Label>
              <Select 
                value={watchedType} 
                onValueChange={(value) => setValue('type', value as any)}
                disabled={isSystemCreated} // 系统创建的数字人类型不可修改
              >
                <SelectTrigger className={errors.type ? 'border-red-500' : ''}>
                  <SelectValue placeholder="选择数字人类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="personal">
                    <div className="flex items-center space-x-2">
                      <User className="h-4 w-4" />
                      <span>个人助手</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="business">
                    <div className="flex items-center space-x-2">
                      <Building className="h-4 w-4" />
                      <span>商务助手</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="specialized">
                    <div className="flex items-center space-x-2">
                      <Zap className="h-4 w-4" />
                      <span>专业助手</span>
                    </div>
                  </SelectItem>
                  {isEditing && isSystemCreated && (
                    <SelectItem value="system">
                      <div className="flex items-center space-x-2">
                        <Shield className="h-4 w-4" />
                        <span>系统助手</span>
                      </div>
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="status">状态</Label>
              <Select 
                value={watch('status')} 
                onValueChange={(value) => setValue('status', value as any)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择状态" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">活跃</SelectItem>
                  <SelectItem value="inactive">停用</SelectItem>
                  <SelectItem value="maintenance">维护中</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* 个性化配置 */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">个性化配置</h3>
            
            <div>
              <Label htmlFor="personalityTone">语调风格</Label>
              <Select 
                value={watch('personalityTone')} 
                onValueChange={(value) => setValue('personalityTone', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择语调风格" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="friendly">友好</SelectItem>
                  <SelectItem value="professional">专业</SelectItem>
                  <SelectItem value="casual">轻松</SelectItem>
                  <SelectItem value="formal">正式</SelectItem>
                  <SelectItem value="warm">温暖</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="personalityStyle">交流风格</Label>
              <Select 
                value={watch('personalityStyle')} 
                onValueChange={(value) => setValue('personalityStyle', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择交流风格" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="concise">简洁明了</SelectItem>
                  <SelectItem value="detailed">详细解释</SelectItem>
                  <SelectItem value="interactive">互动引导</SelectItem>
                  <SelectItem value="supportive">支持鼓励</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="personalitySpecialization">专业领域</Label>
              <Select 
                value={watch('personalitySpecialization')} 
                onValueChange={(value) => setValue('personalitySpecialization', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择专业领域" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="general">通用助手</SelectItem>
                  <SelectItem value="medical_beauty">医美咨询</SelectItem>
                  <SelectItem value="customer_service">客户服务</SelectItem>
                  <SelectItem value="sales">销售支持</SelectItem>
                  <SelectItem value="education">教育培训</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* 消息配置 */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">消息配置</h3>
          
          <div>
            <Label htmlFor="greetingMessage">打招呼消息</Label>
            <Textarea
              id="greetingMessage"
              {...register('greetingMessage', {
                maxLength: { value: 500, message: '打招呼消息不能超过500个字符' }
              })}
              placeholder="数字人第一次与用户对话时的打招呼消息"
              rows={2}
            />
            {errors.greetingMessage && (
              <p className="text-sm text-red-600 mt-1">{errors.greetingMessage.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="welcomeMessage">欢迎消息模板</Label>
            <Textarea
              id="welcomeMessage"
              {...register('welcomeMessage', {
                maxLength: { value: 500, message: '欢迎消息不能超过500个字符' }
              })}
              placeholder="用户进入会话时的欢迎消息模板"
              rows={2}
            />
            {errors.welcomeMessage && (
              <p className="text-sm text-red-600 mt-1">{errors.welcomeMessage.message}</p>
            )}
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="flex justify-end space-x-4 pt-6 border-t">
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={isSubmitting}
          >
            取消
          </Button>
          <Button
            type="submit"
            disabled={isSubmitting}
            className="min-w-[100px]"
          >
            {isSubmitting ? (
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>{isEditing ? '更新中...' : '创建中...'}</span>
              </div>
            ) : (
              isEditing ? '更新数字人' : '创建数字人'
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
