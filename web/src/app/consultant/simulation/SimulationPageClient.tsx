'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import Image from 'next/image';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue 
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  Dialog, DialogContent, DialogDescription, DialogFooter, 
  DialogHeader, DialogTitle, DialogTrigger 
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { SimulationImage, ProjectType } from '@/types/consultant';
import { 
  getProjectTypes, uploadAndSimulate, 
  getAllSimulations 
} from '@/service/consultantService';
import { useAuthContext } from '@/contexts/AuthContext';
import { getConnectionStatus } from '@/service/chatService';
import { ConnectionStatus } from '@/service/websocket';

export default function SimulationPageClient() {
  const [selectedSimulation, setSelectedSimulation] = useState<SimulationImage | null>(null);
  const [projectTypes, setProjectTypes] = useState<ProjectType[]>([]);
  const [selectedProjectType, setSelectedProjectType] = useState<string>('');
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState('upload');
  const [simulations, setSimulations] = useState<SimulationImage[]>([]);
  const [notes, setNotes] = useState('');
  const [selectedSimulatedImage, setSelectedSimulatedImage] = useState<string | null>(null);
  const [customerName, setCustomerName] = useState('');
  const [customerId, setCustomerId] = useState('');

  // 获取项目类型和模拟图像
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [types, sims] = await Promise.all([
          getProjectTypes(),
          getAllSimulations()
        ]);
        setProjectTypes(types);
        setSimulations(sims);
        if (types.length > 0) {
          setSelectedProjectType(types[0].id);
          // 初始化默认参数
          const defaultParams: Record<string, any> = {};
          types[0].parameters.forEach(param => {
            defaultParams[param.name] = param.defaultValue;
          });
          setParameters(defaultParams);
        }
      } catch (error) {
        console.error('获取数据失败', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, []);

  // 切换项目类型时更新参数
  useEffect(() => {
    if (!selectedProjectType) return;
    
    const projectType = projectTypes.find(pt => pt.id === selectedProjectType);
    if (projectType) {
      const newParameters: Record<string, any> = {};
      projectType.parameters.forEach(param => {
        newParameters[param.name] = param.defaultValue;
      });
      setParameters(newParameters);
    }
  }, [selectedProjectType, projectTypes]);

  // 文件上传区域配置
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    
    const file = acceptedFiles[0];
    const objectUrl = URL.createObjectURL(file);
    setPreviewImage(objectUrl);
    
    // 清理函数
    return () => URL.revokeObjectURL(objectUrl);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png']
    },
    maxFiles: 1
  });

  // 更新参数值
  const handleParameterChange = (name: string, value: string | number) => {
    setParameters(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // 提交上传并模拟
  const handleSubmit = async () => {
    if (!previewImage || !customerId || !customerName || !selectedProjectType) return;
    
    try {
      setIsUploading(true);
      
      // 假设我们有一个File对象 - 在实际应用中，这将是从dropzone获取的
      const response = await fetch(previewImage);
      const blob = await response.blob();
      const file = new File([blob], 'upload.jpg', { type: 'image/jpeg' });
      
      const simulation = await uploadAndSimulate(
        file,
        customerId,
        customerName,
        selectedProjectType,
        parameters
      );
      
      setSimulations(prev => [simulation, ...prev]);
      setSelectedSimulation(simulation);
      setNotes('');
      setSelectedTab('history');
    } catch (error) {
      console.error('上传失败', error);
    } finally {
      setIsUploading(false);
    }
  };

  const handleSelectSimulation = (simulation: SimulationImage) => {
    setSelectedSimulation(simulation);
    if (simulation.simulatedImages.length > 0) {
      setSelectedSimulatedImage(simulation.simulatedImages[0].image);
    }
    setNotes(simulation.notes || '');
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  const currentProjectType = projectTypes.find(pt => pt.id === selectedProjectType);

  return (
    <div className="container mx-auto p-6">
      <h1 className="mb-6 text-2xl font-bold text-gray-800">术前模拟</h1>
      
      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="w-full">
        <TabsList className="mb-6">
          <TabsTrigger value="upload">上传照片</TabsTrigger>
          <TabsTrigger value="history">历史模拟</TabsTrigger>
        </TabsList>
        
        <TabsContent value="upload" className="space-y-6">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {/* 左侧 - 上传区和客户信息 */}
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>上传照片</CardTitle>
                  <CardDescription>
                    上传客户照片用于生成术前模拟效果
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div
                    {...getRootProps()}
                    className={`
                      border-2 border-dashed rounded-lg p-6 text-center cursor-pointer
                      transition-colors hover:border-orange-300
                      ${isDragActive ? 'border-orange-500 bg-orange-50' : 'border-gray-300'}
                    `}
                  >
                    <input {...getInputProps()} />
                    {previewImage ? (
                      <div className="relative h-48 w-full">
                        <Image
                          src={previewImage}
                          alt="预览图"
                          fill
                          style={{ objectFit: 'contain' }}
                        />
                      </div>
                    ) : (
                      <div className="py-8">
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className="mx-auto h-12 w-12 text-gray-400"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                          />
                        </svg>
                        <p className="mt-2 text-sm text-gray-500">
                          {isDragActive
                            ? '将图片放在这里...'
                            : '点击或拖拽图片到此处上传'}
                        </p>
                        <p className="mt-1 text-xs text-gray-400">
                          支持JPG, PNG格式，建议使用正面清晰照片
                        </p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>客户信息</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="mb-1 block text-sm font-medium">
                      客户ID
                    </label>
                    <Input
                      value={customerId}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCustomerId(e.target.value)}
                      placeholder="输入客户ID"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium">
                      客户姓名
                    </label>
                    <Input
                      value={customerName}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCustomerName(e.target.value)}
                      placeholder="输入客户姓名"
                    />
                  </div>
                </CardContent>
              </Card>
            </div>
            
            {/* 右侧 - 参数设置 */}
            <div>
              <Card>
                <CardHeader>
                  <CardTitle>模拟参数</CardTitle>
                  <CardDescription>
                    选择项目类型并调整参数
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <label className="mb-1 block text-sm font-medium">
                      项目类型
                    </label>
                    <Select
                      value={selectedProjectType}
                      onValueChange={setSelectedProjectType}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择项目类型" />
                      </SelectTrigger>
                      <SelectContent>
                        {projectTypes.map(type => (
                          <SelectItem key={type.id} value={type.id}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {currentProjectType && (
                    <div className="space-y-4">
                      <p className="text-sm text-gray-500">
                        {currentProjectType.description}
                      </p>
                      
                      {currentProjectType.parameters.map(param => (
                        <div key={param.id} className="space-y-2">
                          <div className="flex items-center justify-between">
                            <label className="text-sm font-medium">
                              {param.label}
                            </label>
                            {param.type === 'slider' && (
                              <span className="text-sm text-gray-500">
                                {parameters[param.name]}
                              </span>
                            )}
                          </div>
                          
                          {param.type === 'slider' && (
                            <Slider
                              value={[parameters[param.name]]}
                              min={param.min}
                              max={param.max}
                              step={param.step}
                              onValueChange={(value) => handleParameterChange(param.name, value[0])}
                            />
                          )}
                          
                          {param.type === 'select' && (
                            <Select
                              value={parameters[param.name]}
                              onValueChange={(value) => handleParameterChange(param.name, value)}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {param.options?.map(option => (
                                  <SelectItem key={option.value} value={option.value}>
                                    {option.label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          )}
                          
                          {param.type === 'radio' && param.options && (
                            <div className="flex space-x-4">
                              {param.options.map(option => (
                                <label key={option.value} className="flex items-center space-x-2">
                                  <input
                                    type="radio"
                                    value={option.value}
                                    checked={parameters[param.name] === option.value}
                                    onChange={() => handleParameterChange(param.name, option.value)}
                                    className="h-4 w-4 text-orange-500"
                                  />
                                  <span className="text-sm">{option.label}</span>
                                </label>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
                <CardFooter className="flex justify-end">
                  <Button
                    onClick={handleSubmit}
                    disabled={!previewImage || !customerId || !customerName || isUploading}
                    className="bg-orange-500 hover:bg-orange-600"
                  >
                    {isUploading ? (
                      <>
                        <LoadingSpinner className="mr-2 h-4 w-4" fullScreen={false} />
                        处理中...
                      </>
                    ) : '生成模拟效果'}
                  </Button>
                </CardFooter>
              </Card>
            </div>
          </div>
        </TabsContent>
        
        <TabsContent value="history" className="space-y-6">
          {simulations.length === 0 ? (
            <div className="rounded-lg border border-dashed p-8 text-center">
              <p className="text-gray-500">暂无模拟记录</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
              {simulations.map(simulation => (
                <Card 
                  key={simulation.id}
                  className={`cursor-pointer transition-all hover:shadow-md ${
                    selectedSimulation?.id === simulation.id ? 'ring-2 ring-orange-500' : ''
                  }`}
                  onClick={() => handleSelectSimulation(simulation)}
                >
                  <CardContent className="p-4">
                    <div className="relative h-48 w-full">
                      <Image
                        src={simulation.originalImage}
                        alt={`${simulation.customerName}的原始图片`}
                        fill
                        className="rounded-md"
                        style={{ objectFit: 'cover' }}
                      />
                    </div>
                    <div className="mt-3">
                      <h3 className="font-medium">{simulation.customerName}</h3>
                      <p className="text-sm text-gray-500">
                        {new Date(simulation.createdAt).toLocaleString('zh-CN', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })}
                      </p>
                      <p className="text-xs text-gray-400">
                        {simulation.simulatedImages.length} 个模拟效果
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
          
          {selectedSimulation && (
            <Card className="mt-6">
              <CardHeader>
                <CardTitle>{selectedSimulation.customerName}的模拟效果</CardTitle>
                <CardDescription>
                  创建于 {new Date(selectedSimulation.createdAt).toLocaleString('zh-CN')}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                  {/* 原始图像 */}
                  <div>
                    <h3 className="mb-2 text-sm font-medium">原始照片</h3>
                    <div className="relative h-80 w-full overflow-hidden rounded-lg border">
                      <Image
                        src={selectedSimulation.originalImage}
                        alt="原始照片"
                        fill
                        style={{ objectFit: 'contain' }}
                      />
                    </div>
                  </div>
                  
                  {/* 模拟效果 */}
                  <div>
                    <div className="mb-2 flex items-center justify-between">
                      <h3 className="text-sm font-medium">模拟效果</h3>
                      <div className="flex space-x-2">
                        {selectedSimulation.simulatedImages.map((sim, index) => (
                          <button
                            key={sim.id}
                            onClick={() => setSelectedSimulatedImage(sim.image)}
                            className={`h-6 w-6 rounded-full text-xs ${
                              selectedSimulatedImage === sim.image
                                ? 'bg-orange-500 text-white'
                                : 'bg-gray-200 text-gray-600'
                            }`}
                          >
                            {index + 1}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="relative h-80 w-full overflow-hidden rounded-lg border">
                      {selectedSimulatedImage && (
                        <Image
                          src={selectedSimulatedImage}
                          alt="模拟效果"
                          fill
                          style={{ objectFit: 'contain' }}
                        />
                      )}
                    </div>
                    
                    {/* 模拟参数信息 */}
                    <div className="mt-4 space-y-2">
                      {selectedSimulation.simulatedImages.find(
                        sim => sim.image === selectedSimulatedImage
                      )?.projectType && (
                        <p className="text-sm">
                          <span className="font-medium">项目类型：</span>
                          {projectTypes.find(
                            pt => pt.id === selectedSimulation.simulatedImages.find(
                              sim => sim.image === selectedSimulatedImage
                            )?.projectType
                          )?.label || '未知项目'}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
                
                {/* 备注 */}
                <div className="mt-6">
                  <label className="mb-1 block text-sm font-medium">
                    备注
                  </label>
                  <Textarea
                    value={notes}
                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNotes(e.target.value)}
                    placeholder="添加关于模拟效果的备注..."
                    className="h-24"
                  />
                </div>
              </CardContent>
              <CardFooter className="flex justify-between">
                <Dialog>
                  <DialogTrigger asChild>
                    <Button variant="outline">分享给客户</Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>分享模拟效果</DialogTitle>
                      <DialogDescription>
                        您可以通过以下方式将模拟效果分享给客户
                      </DialogDescription>
                    </DialogHeader>
                    <div className="flex flex-col gap-4 py-4">
                      <Button variant="outline" className="w-full justify-start">
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className="mr-2 h-4 w-4"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                          />
                        </svg>
                        复制分享链接
                      </Button>
                      <Button variant="outline" className="w-full justify-start">
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className="mr-2 h-4 w-4"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                          />
                        </svg>
                        通过邮件发送
                      </Button>
                      <Button variant="outline" className="w-full justify-start">
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className="mr-2 h-4 w-4"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
                          />
                        </svg>
                        发送到聊天窗口
                      </Button>
                    </div>
                    <DialogFooter>
                      <Button type="button" variant="secondary" onClick={() => {}}>
                        取消
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
                
                <Button
                  onClick={() => {
                    // 保存备注逻辑
                  }}
                  className="bg-orange-500 hover:bg-orange-600"
                >
                  保存备注
                </Button>
              </CardFooter>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
} 