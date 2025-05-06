'use client';

import { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { 
  Card, CardContent, CardDescription, CardFooter, 
  CardHeader, CardTitle 
} from '@/components/ui/card';
import { 
  Dialog, DialogContent, DialogDescription, DialogFooter, 
  DialogHeader, DialogTitle, DialogTrigger 
} from '@/components/ui/dialog';
import { 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue 
} from '@/components/ui/select';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { 
  getAllPersonalizedPlans, getCustomerPlans, 
  createPersonalizedPlan, updatePersonalizedPlan 
} from '@/lib/advisorService';
import { PersonalizedPlan } from '@/types/advisor';

export default function PlanPageClient() {
  const [plans, setPlans] = useState<PersonalizedPlan[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<PersonalizedPlan | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const data = await getAllPersonalizedPlans();
        setPlans(data);
        setIsLoading(false);
      } catch (error) {
        console.error('获取方案失败', error);
        setIsLoading(false);
      }
    };

    fetchPlans();
  }, []);

  // 过滤方案
  const filteredPlans = plans.filter(plan => {
    const matchesSearch = 
      plan.customerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      plan.customerId.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (selectedTab === 'all') return matchesSearch;
    if (selectedTab === 'draft') return matchesSearch && plan.status === 'draft';
    if (selectedTab === 'shared') return matchesSearch && plan.status === 'shared';
    if (selectedTab === 'accepted') return matchesSearch && plan.status === 'accepted';
    return matchesSearch;
  });

  const handleSelectPlan = (plan: PersonalizedPlan) => {
    setSelectedPlan(plan);
  };

  const getPlanStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'bg-gray-200 text-gray-700';
      case 'shared': return 'bg-blue-100 text-blue-700';
      case 'accepted': return 'bg-green-100 text-green-700';
      case 'rejected': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getPlanStatusText = (status: string) => {
    switch (status) {
      case 'draft': return '草稿';
      case 'shared': return '已分享';
      case 'accepted': return '已接受';
      case 'rejected': return '已拒绝';
      default: return '未知状态';
    }
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">个性化方案推荐</h1>
        <Button 
          onClick={() => setShowCreateDialog(true)}
          className="bg-orange-500 hover:bg-orange-600"
        >
          创建新方案
        </Button>
      </div>

      <div className="mb-6 flex items-center space-x-4">
        <div className="relative flex-1">
          <Input
            type="text"
            placeholder="搜索客户姓名或ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
      </div>

      <div className="mb-6">
        <Tabs value={selectedTab} onValueChange={setSelectedTab}>
          <TabsList>
            <TabsTrigger value="all">全部</TabsTrigger>
            <TabsTrigger value="draft">草稿</TabsTrigger>
            <TabsTrigger value="shared">已分享</TabsTrigger>
            <TabsTrigger value="accepted">已接受</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>方案列表</CardTitle>
              <CardDescription>
                {filteredPlans.length} 个方案
              </CardDescription>
            </CardHeader>
            <CardContent className="max-h-[500px] overflow-y-auto">
              {filteredPlans.length === 0 ? (
                <div className="rounded-lg border border-dashed py-8 text-center">
                  <p className="text-gray-500">暂无符合条件的方案</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {filteredPlans.map(plan => (
                    <div 
                      key={plan.id}
                      className={`cursor-pointer rounded-lg border p-3 transition-all hover:shadow-md ${
                        selectedPlan?.id === plan.id ? 'border-orange-500 bg-orange-50' : ''
                      }`}
                      onClick={() => handleSelectPlan(plan)}
                    >
                      <div className="flex items-center justify-between">
                        <h3 className="font-medium">{plan.customerName}</h3>
                        <Badge className={getPlanStatusColor(plan.status)}>
                          {getPlanStatusText(plan.status)}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-500">
                        ID: {plan.customerId}
                      </p>
                      <p className="text-sm text-gray-500">
                        创建于: {new Date(plan.createdAt).toLocaleDateString('zh-CN')}
                      </p>
                      <p className="mt-1 text-sm">
                        总费用: ¥{plan.totalCost.toLocaleString()}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-2">
          {selectedPlan ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>{selectedPlan.customerName}的个性化方案</CardTitle>
                    <CardDescription>
                      创建于 {new Date(selectedPlan.createdAt).toLocaleDateString('zh-CN')}
                      {selectedPlan.updatedAt && 
                        ` · 更新于 ${new Date(selectedPlan.updatedAt).toLocaleDateString('zh-CN')}`}
                    </CardDescription>
                  </div>
                  <Badge className={getPlanStatusColor(selectedPlan.status)}>
                    {getPlanStatusText(selectedPlan.status)}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h3 className="mb-2 text-sm font-medium">客户需求</h3>
                  <Card>
                    <CardContent className="p-4">
                      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <div>
                          <p className="text-sm font-medium text-gray-500">年龄</p>
                          <p>{selectedPlan.customerProfile?.age || '未知'}</p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-500">性别</p>
                          <p>{selectedPlan.customerProfile?.gender === 'female' ? '女' : '男'}</p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-500">预算</p>
                          <p>¥{selectedPlan.customerProfile?.budget?.toLocaleString() || '未指定'}</p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-500">关注问题</p>
                          <div className="flex flex-wrap gap-1">
                            {selectedPlan.customerProfile?.concerns.map((concern, index) => (
                              <Badge key={index} variant="outline">
                                {concern}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        <div className="md:col-span-2">
                          <p className="text-sm font-medium text-gray-500">期望效果</p>
                          <p>{selectedPlan.customerProfile?.expectedResults || '未指定'}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                <div>
                  <h3 className="mb-2 text-sm font-medium">推荐项目</h3>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>项目名称</TableHead>
                        <TableHead>费用</TableHead>
                        <TableHead className="hidden md:table-cell">持续时间</TableHead>
                        <TableHead className="hidden md:table-cell">恢复期</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {selectedPlan.projects.map(project => (
                        <TableRow key={project.id}>
                          <TableCell className="font-medium">{project.name}</TableCell>
                          <TableCell>¥{project.cost.toLocaleString()}</TableCell>
                          <TableCell className="hidden md:table-cell">{project.duration}</TableCell>
                          <TableCell className="hidden md:table-cell">{project.recoveryTime}</TableCell>
                        </TableRow>
                      ))}
                      <TableRow>
                        <TableCell className="font-bold">总计</TableCell>
                        <TableCell className="font-bold">¥{selectedPlan.totalCost.toLocaleString()}</TableCell>
                        <TableCell className="hidden md:table-cell"></TableCell>
                        <TableCell className="hidden md:table-cell"></TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </div>

                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                  <div>
                    <h3 className="mb-2 text-sm font-medium">方案详情</h3>
                    <Card>
                      <CardContent className="p-4 space-y-4">
                        <div>
                          <p className="text-sm font-medium text-gray-500">总估计时间</p>
                          <p>{selectedPlan.estimatedTimeframe}</p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-500">顾问</p>
                          <p>{selectedPlan.advisorName}</p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-500">备注</p>
                          <p>{selectedPlan.notes || '无'}</p>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  <div>
                    <h3 className="mb-2 text-sm font-medium">项目风险提示</h3>
                    <Card>
                      <CardContent className="p-4">
                        <ul className="space-y-2">
                          {selectedPlan.projects.flatMap(project => 
                            project.risks.map((risk, index) => (
                              <li key={`${project.id}-risk-${index}`} className="flex items-start">
                                <span className="mr-2 mt-0.5 text-yellow-500">⚠️</span>
                                <span className="text-sm">{risk}</span>
                              </li>
                            ))
                          )}
                        </ul>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => {}}>
                  编辑方案
                </Button>
                <Button 
                  className="bg-orange-500 hover:bg-orange-600"
                  onClick={() => {}}
                >
                  分享给客户
                </Button>
              </CardFooter>
            </Card>
          ) : (
            <div className="flex h-full items-center justify-center rounded-lg border border-dashed p-12">
              <div className="text-center">
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
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">没有选择方案</h3>
                <p className="mt-1 text-sm text-gray-500">
                  从左侧列表中选择一个方案查看详情
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 创建新方案对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>创建新的个性化方案</DialogTitle>
            <DialogDescription>
              为客户创建一个新的个性化医美方案
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <label className="text-right text-sm font-medium">
                客户ID
              </label>
              <Input
                placeholder="输入客户ID"
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <label className="text-right text-sm font-medium">
                客户姓名
              </label>
              <Input
                placeholder="输入客户姓名"
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <label className="text-right text-sm font-medium">
                关注问题
              </label>
              <Input
                placeholder="例如：双眼皮、鼻部整形"
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <label className="text-right text-sm font-medium">
                预算
              </label>
              <Input
                type="number"
                placeholder="输入预算金额"
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <label className="text-right text-sm font-medium">
                期望效果
              </label>
              <Textarea
                placeholder="客户期望达到的效果..."
                className="col-span-3"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              取消
            </Button>
            <Button 
              className="bg-orange-500 hover:bg-orange-600"
              onClick={() => {
                // 处理创建方案逻辑
                setShowCreateDialog(false);
              }}
            >
              创建方案
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
} 