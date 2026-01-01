'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
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

import { apiClient } from '@/service/apiClient';
import type { DigitalHuman, CreateDigitalHumanRequest, UpdateDigitalHumanRequest } from '@/types/digital-human';
import { useAuthedImageSrc } from '@/hooks/useAuthedImageSrc';

interface DigitalHumanFormProps {
  digitalHuman?: DigitalHuman;
  onSubmit: (data: CreateDigitalHumanRequest | UpdateDigitalHumanRequest) => Promise<void>;
  onCancel: () => void;
  allowSystemType?: boolean;
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

const TRIM = (v: unknown) => (typeof v === 'string' ? v.trim() : v);

const DigitalHumanFormSchema = z.object({
  name: z.preprocess(
    TRIM,
    z
      .string({ required_error: '请输入数字人名称' })
      .min(2, '数字人名称至少2个字符')
      .max(255, '数字人名称不能超过255个字符'),
  ),
  description: z.preprocess(
    (v: unknown) => {
      if (typeof v !== 'string') return v;
      const trimmed = v.trim();
      return trimmed === '' ? '' : trimmed;
    },
    z.string().max(500, '描述不能超过500个字符'),
  ),
  type: z.enum(['personal', 'business', 'specialized', 'system'], {
    required_error: '请选择数字人类型',
    invalid_type_error: '数字人类型无效',
  }),
  status: z.enum(['active', 'inactive', 'maintenance'], {
    required_error: '请选择状态',
    invalid_type_error: '状态无效',
  }),
  greetingMessage: z.string().max(500, '打招呼消息不能超过500个字符'),
  welcomeMessage: z.string().max(500, '欢迎消息模板不能超过500个字符'),
  personalityTone: z.string().min(1, '请选择语调风格'),
  personalityStyle: z.string().min(1, '请选择交流风格'),
  personalitySpecialization: z.string().min(1, '请选择专业领域'),
});

export default function DigitalHumanForm({
  digitalHuman,
  onSubmit,
  onCancel,
  allowSystemType = false,
}: DigitalHumanFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const authedAvatarSrc = useAuthedImageSrc(avatarPreview || digitalHuman?.avatar || null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors }
  } = useForm<FormData>({
    resolver: zodResolver(DigitalHumanFormSchema),
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
      setAvatarPreview(digitalHuman.avatar ?? null);
    }
  }, [digitalHuman]);

  const handleAvatarChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        toast.error('请选择图片文件');
        return;
      }
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
        description: data.description.trim() || undefined,
        ...((allowSystemType || data.type !== 'system') && { type: data.type }),
        status: data.status,
        greeting_message: data.greetingMessage.trim() || undefined,
        welcome_message: data.welcomeMessage.trim() || undefined,
        personality: {
          tone: data.personalityTone,
          style: data.personalityStyle,
          specialization: data.personalitySpecialization
        }
      };

      // 如果有头像文件，需要先上传
      if (avatarFile) {
        const formData = new FormData();
        formData.append('file', avatarFile);

        const { data: result } = await apiClient.upload<any>('/files/upload-avatar', formData);
        if (!result?.success) {
          throw new Error(result?.message || '头像上传失败');
        }

        const fileId = result?.file_info?.file_id as string | undefined;
        if (!fileId) {
          throw new Error('服务器返回的文件ID为空');
        }

        submitData.avatar = fileId;
      }

      await onSubmit(submitData);
      toast.success(isEditing ? '数字人更新成功' : '数字人创建成功');
    } catch (error) {
      console.error('提交失败:', error);
      const message = error instanceof Error ? error.message : (isEditing ? '数字人更新失败' : '数字人创建失败');
      toast.error(message);
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
    <div className="p-4 md:p-6 space-y-4 md:space-y-6">
      <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-4 md:space-y-6">
        {/* 基础信息卡片：头像 + 基本字段 */}
        <Card className="border-gray-200 shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-base md:text-lg">
              基础信息
            </CardTitle>
            <CardDescription>
              设置数字人的名称、类型和基础描述信息
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6 md:space-y-0 md:grid md:grid-cols-[auto,1fr] md:gap-8">
            {/* 头像区域 */}
            <div className="flex flex-col items-center space-y-3 md:items-start">
              <Avatar className="w-20 h-20 md:w-24 md:h-24 shadow-sm">
                <AvatarImage src={authedAvatarSrc} />
                <AvatarFallback className="text-xl md:text-2xl bg-gradient-to-br from-orange-400 to-orange-600 text-white">
                  {watch('name')?.charAt(0)?.toUpperCase() || '?'}
                </AvatarFallback>
              </Avatar>

              <div className="flex items-center space-x-2">
                <Label htmlFor="avatar-upload" className="cursor-pointer">
                  <div className="flex items-center space-x-2 px-3 py-1.5 bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 text-xs md:text-sm text-gray-700 transition-colors">
                    <Upload className="h-3.5 w-3.5 md:h-4 md:w-4" />
                    <span>上传头像</span>
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
              <p className="text-[11px] md:text-xs text-gray-500">
                支持 JPG、PNG 格式，文件大小不超过 5MB
              </p>
            </div>

            {/* 基础字段区域 */}
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="name">数字人名称 *</Label>
                  <Input
                    id="name"
                    {...register('name')}
                    placeholder="为你的数字人起一个名字"
                    className={errors.name ? 'border-red-500 focus-visible:ring-red-500' : ''}
                  />
                  {errors.name && (
                    <p className="text-xs text-red-600 mt-1">{errors.name.message}</p>
                  )}
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="type">数字人类型 *</Label>
                  <Select
                    value={watchedType}
                    onValueChange={(value) => setValue('type', value as any)}
                  >
                    <SelectTrigger className={errors.type ? 'border-red-500 focus-visible:ring-red-500' : ''}>
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
                      {(allowSystemType || (isEditing && isSystemCreated)) && (
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
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="description">描述</Label>
                <Textarea
                  id="description"
                  {...register('description')}
                  placeholder="简要描述这个数字人的功能和特点，方便后续管理和区分"
                  rows={3}
                  className={errors.description ? 'border-red-500 focus-visible:ring-red-500' : ''}
                />
                {errors.description && (
                  <p className="text-xs text-red-600 mt-1">{errors.description.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
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
          </CardContent>
        </Card>

        {/* 个性化配置卡片 */}
        <Card className="border-gray-200 shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-base md:text-lg">
              个性化配置
            </CardTitle>
            <CardDescription>
              配置对话语气、交流风格和专业领域，让数字人更符合使用场景
            </CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-1.5">
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

            <div className="space-y-1.5">
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

            <div className="space-y-1.5">
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
                  <SelectItem value="medical_beauty">咨询</SelectItem>
                  <SelectItem value="customer_service">客户服务</SelectItem>
                  <SelectItem value="sales">销售支持</SelectItem>
                  <SelectItem value="education">教育培训</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* 消息配置卡片 */}
        <Card className="border-gray-200 shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-base md:text-lg">
              消息配置
            </CardTitle>
            <CardDescription>
              配置数字人与用户首次接触时的打招呼和欢迎文案
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="greetingMessage">打招呼消息</Label>
              <Textarea
                id="greetingMessage"
                {...register('greetingMessage')}
                placeholder="例如：你好，我是你的专属数字助手，很高兴认识你～"
                rows={2}
              />
              {errors.greetingMessage && (
                <p className="text-xs text-red-600 mt-1">{errors.greetingMessage.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="welcomeMessage">欢迎消息模板</Label>
              <Textarea
                id="welcomeMessage"
                {...register('welcomeMessage')}
                placeholder="例如：欢迎来到我们的服务，我可以帮你解答产品、方案等相关问题。"
                rows={2}
              />
              {errors.welcomeMessage && (
                <p className="text-xs text-red-600 mt-1">{errors.welcomeMessage.message}</p>
              )}
            </div>

            {/* 操作按钮 */}
            <div className="flex flex-col-reverse gap-3 pt-2 border-t border-dashed border-gray-200 mt-4 md:flex-row md:justify-end md:space-x-4 md:gap-0 md:pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={onCancel}
                disabled={isSubmitting}
                className="w-full md:w-auto"
              >
                取消
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting}
                className="w-full md:w-auto min-w-[120px]"
              >
                {isSubmitting ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>{isEditing ? '更新中...' : '创建中...'}</span>
                  </div>
                ) : (
                  isEditing ? '更新数字人' : '创建数字人'
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  );
}
