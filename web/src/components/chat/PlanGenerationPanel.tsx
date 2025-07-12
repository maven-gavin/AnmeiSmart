'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  Sparkles, 
  RefreshCw, 
  Eye, 
  Send, 
  FileText,
  Info,
  Target,
  DollarSign,
  Calendar,
  Heart,
  MessageSquare,
  Lightbulb
} from 'lucide-react';
import { 
  getPlanGenerationSessionByConversation,
  createPlanGenerationSession,
  analyzeConversationInfo,
  generatePlan as generatePlanAPI,
  optimizePlan as optimizePlanAPI,
  getSessionDrafts,
  type PlanGenerationSession,
  type InfoAnalysis,
  type PlanDraft
} from '@/service/planGenerationService';

// 组件Props接口

interface PlanGenerationPanelProps {
  conversationId: string;
  customerId: string;
  consultantId: string;
  onClose: () => void;
  onPlanGenerated?: (plan: PlanDraft) => void;
}

export default function PlanGenerationPanel({
  conversationId,
  customerId,
  consultantId,
  onClose,
  onPlanGenerated
}: PlanGenerationPanelProps) {
  // 状态管理
  const [session, setSession] = useState<PlanGenerationSession | null>(null);
  const [analysis, setAnalysis] = useState<InfoAnalysis | null>(null);
  const [currentDraft, setCurrentDraft] = useState<PlanDraft | null>(null);
  const [drafts, setDrafts] = useState<PlanDraft[]>([]);
  
  // 加载状态
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isOptimizing, setIsOptimizing] = useState(false);
  
  // UI状态
  const [activeTab, setActiveTab] = useState('analysis');
  const [showOptimizeDialog, setShowOptimizeDialog] = useState(false);
  const [optimizationRequirements, setOptimizationRequirements] = useState('');
  const [optimizationType, setOptimizationType] = useState<'cost' | 'timeline' | 'content'>('content');
  
  // 初始化会话
  useEffect(() => {
    initializeSession();
  }, [conversationId]);

  const initializeSession = async () => {
    try {
      setIsLoading(true);
      
      // 检查是否已存在会话
      const existingSession = await checkExistingSession();
      if (existingSession) {
        setSession(existingSession);
        await loadAnalysis(existingSession.id);
        await loadDrafts(existingSession.id);
      } else {
        // 创建新会话
        const newSession = await createSession();
        setSession(newSession);
        // 自动进行信息分析
        await performAnalysis(newSession.id);
      }
    } catch (error) {
      console.error('初始化会话失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const checkExistingSession = async (): Promise<PlanGenerationSession | null> => {
    try {
      return await getPlanGenerationSessionByConversation(conversationId);
    } catch (error) {
      console.error('检查会话失败:', error);
      return null;
    }
  };

  const createSession = async (): Promise<PlanGenerationSession> => {
    return await createPlanGenerationSession({
      conversation_id: conversationId,
      customer_id: customerId,
      consultant_id: consultantId,
      session_metadata: {
        created_by: 'consultant',
        creation_context: 'chat_interface'
      }
    });
  };

  const performAnalysis = async (sessionId?: string) => {
    if (!session && !sessionId) return;
    
    try {
      setIsAnalyzing(true);
      
      const analysisResult = await analyzeConversationInfo({
        conversation_id: conversationId,
        force_analysis: true
      });
      
      setAnalysis(analysisResult);
      
      // 如果分析完成，自动切换到生成标签
      if (analysisResult.can_generate_plan) {
        setActiveTab('generation');
      }
    } catch (error) {
      console.error('分析失败:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const loadAnalysis = async (sessionId: string) => {
    try {
      const analysisResult = await analyzeConversationInfo({
        conversation_id: conversationId,
        force_analysis: false
      });
      setAnalysis(analysisResult);
    } catch (error) {
      console.error('加载分析失败:', error);
    }
  };

  const loadDrafts = async (sessionId: string) => {
    try {
      const draftsData = await getSessionDrafts(sessionId);
      setDrafts(draftsData);
      if (draftsData.length > 0) {
        setCurrentDraft(draftsData[0]); // 设置最新的草稿
        setActiveTab('preview');
      }
    } catch (error) {
      console.error('加载草稿失败:', error);
    }
  };

  const handleGeneratePlan = async () => {
    if (!session || !analysis?.can_generate_plan) return;
    
    try {
      setIsGenerating(true);
      
      const result = await generatePlanAPI({
        conversation_id: conversationId,
        force_generation: false,
        generation_options: {
          template_type: 'comprehensive',
          include_timeline: true,
          include_cost_breakdown: true
        }
      });
      
      // 重新加载草稿
      await loadDrafts(session.id);
      
      // 切换到预览标签
      setActiveTab('preview');
      
      if (onPlanGenerated && result.draft_id) {
        // 通知父组件方案已生成
        onPlanGenerated(currentDraft!);
      }
    } catch (error) {
      console.error('生成方案失败:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleOptimizePlan = async () => {
    if (!currentDraft || !optimizationRequirements.trim()) return;
    
    try {
      setIsOptimizing(true);
      
      const optimizedDraft = await optimizePlanAPI({
        draft_id: currentDraft.id,
        optimization_type: optimizationType,
        requirements: {
          description: optimizationRequirements,
          type: optimizationType
        }
      });
      
      // 重新加载草稿
      await loadDrafts(session!.id);
      
      setShowOptimizeDialog(false);
      setOptimizationRequirements('');
    } catch (error) {
      console.error('优化方案失败:', error);
    } finally {
      setIsOptimizing(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'collecting': return 'bg-yellow-100 text-yellow-800';
      case 'generating': return 'bg-blue-100 text-blue-800';
      case 'optimizing': return 'bg-purple-100 text-purple-800';
      case 'reviewing': return 'bg-orange-100 text-orange-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'collecting': return '收集信息中';
      case 'generating': return '生成中';
      case 'optimizing': return '优化中';
      case 'reviewing': return '审核中';
      case 'completed': return '已完成';
      case 'failed': return '失败';
      default: return '未知状态';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'basic_info': return <Info className="h-4 w-4" />;
      case 'concerns': return <Target className="h-4 w-4" />;
      case 'budget': return <DollarSign className="h-4 w-4" />;
      case 'timeline': return <Calendar className="h-4 w-4" />;
      case 'expectations': return <Heart className="h-4 w-4" />;
      default: return <MessageSquare className="h-4 w-4" />;
    }
  };

  const getCategoryName = (category: string) => {
    switch (category) {
      case 'basic_info': return '基本信息';
      case 'concerns': return '关注问题';
      case 'budget': return '预算范围';
      case 'timeline': return '时间计划';
      case 'expectations': return '期望效果';
      default: return category;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2" />
          <p className="text-sm text-gray-600">正在初始化方案生成会话...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* 标题和状态 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">AI辅助方案生成</h2>
          <p className="text-sm text-gray-600">智能分析客户需求，生成个性化美肌方案</p>
        </div>
        <div className="flex items-center space-x-2">
          {session && (
            <Badge className={getStatusColor(session.status)}>
              {getStatusText(session.status)}
            </Badge>
          )}
          <Button variant="outline" onClick={onClose}>
            关闭
          </Button>
        </div>
      </div>

      {/* 主要内容 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="analysis">信息分析</TabsTrigger>
          <TabsTrigger value="generation">方案生成</TabsTrigger>
          <TabsTrigger value="preview">方案预览</TabsTrigger>
          <TabsTrigger value="optimization">优化调整</TabsTrigger>
        </TabsList>

        {/* 信息分析标签 */}
        <TabsContent value="analysis" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Sparkles className="h-5 w-5" />
                <span>信息完整性分析</span>
              </CardTitle>
              <CardDescription>
                AI分析对话内容，评估生成方案所需信息的完整性
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {analysis ? (
                <>
                  {/* 完整性得分 */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">信息完整性得分</span>
                      <span className="text-sm font-bold">
                        {Math.round(analysis.completeness_score * 100)}%
                      </span>
                    </div>
                    <Progress value={analysis.completeness_score * 100} className="h-2" />
                  </div>

                  {/* 缺失信息类别 */}
                  {analysis.missing_categories.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium">缺失信息类别</h4>
                      <div className="flex flex-wrap gap-2">
                        {analysis.missing_categories.map((category, index) => (
                          <Badge key={index} variant="outline" className="flex items-center space-x-1">
                            {getCategoryIcon(category)}
                            <span>{getCategoryName(category)}</span>
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 建议 */}
                  {analysis.suggestions.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium">改进建议</h4>
                      <ul className="space-y-1">
                        {analysis.suggestions.map((suggestion, index) => (
                          <li key={index} className="text-sm text-gray-600 flex items-start space-x-2">
                            <Lightbulb className="h-4 w-4 mt-0.5 flex-shrink-0" />
                            <span>{suggestion}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* 生成状态 */}
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      {analysis.can_generate_plan
                        ? "信息已足够，可以生成方案"
                        : "需要补充更多信息才能生成高质量方案"}
                    </AlertDescription>
                  </Alert>
                </>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-600">尚未进行信息分析</p>
                </div>
              )}

              {/* 操作按钮 */}
              <div className="flex space-x-2">
                <Button
                  onClick={() => performAnalysis()}
                  disabled={isAnalyzing}
                  className="flex items-center space-x-2"
                >
                  {isAnalyzing ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <Sparkles className="h-4 w-4" />
                  )}
                  <span>{isAnalyzing ? '分析中...' : '重新分析'}</span>
                </Button>
                
                {analysis?.can_generate_plan && (
                  <Button
                    onClick={() => setActiveTab('generation')}
                    variant="outline"
                  >
                    生成方案
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 方案生成标签 */}
        <TabsContent value="generation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <FileText className="h-5 w-5" />
                <span>方案生成</span>
              </CardTitle>
              <CardDescription>
                基于分析结果生成个性化美肌方案
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {analysis?.can_generate_plan ? (
                <div className="space-y-4">
                  <Alert>
                    <CheckCircle className="h-4 w-4" />
                    <AlertDescription>
                      信息完整性良好（{Math.round(analysis.completeness_score * 100)}%），
                      可以生成高质量的个性化方案
                    </AlertDescription>
                  </Alert>

                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">方案生成选项</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="flex items-center space-x-2">
                        <input type="checkbox" id="include_timeline" defaultChecked />
                        <label htmlFor="include_timeline" className="text-sm">
                          包含时间规划
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input type="checkbox" id="include_cost" defaultChecked />
                        <label htmlFor="include_cost" className="text-sm">
                          包含费用明细
                        </label>
                      </div>
                    </div>
                  </div>

                  <Button
                    onClick={handleGeneratePlan}
                    disabled={isGenerating}
                    className="w-full flex items-center justify-center space-x-2"
                  >
                    {isGenerating ? (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    ) : (
                      <Sparkles className="h-4 w-4" />
                    )}
                    <span>{isGenerating ? '生成中...' : '生成方案'}</span>
                  </Button>
                </div>
              ) : (
                <div className="text-center py-8">
                  <AlertCircle className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
                  <p className="text-gray-600 mb-4">
                    信息完整性不足，建议先补充更多信息
                  </p>
                  <Button
                    onClick={() => setActiveTab('analysis')}
                    variant="outline"
                  >
                    返回分析
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 方案预览标签 */}
        <TabsContent value="preview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Eye className="h-5 w-5" />
                <span>方案预览</span>
              </CardTitle>
              <CardDescription>
                查看生成的方案内容
              </CardDescription>
            </CardHeader>
            <CardContent>
              {currentDraft ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">版本 {currentDraft.version}</h4>
                      <p className="text-sm text-gray-600">
                        {new Date(currentDraft.created_at).toLocaleString()}
                      </p>
                    </div>
                    <Badge className={getStatusColor(currentDraft.status)}>
                      {currentDraft.status}
                    </Badge>
                  </div>

                  {/* 方案内容预览 */}
                  <div className="border rounded-lg p-4 bg-gray-50">
                    <h5 className="font-medium mb-2">方案内容</h5>
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                      {JSON.stringify(currentDraft.content, null, 2)}
                    </pre>
                  </div>

                  {/* 操作按钮 */}
                  <div className="flex space-x-2">
                    <Button
                      onClick={() => setActiveTab('optimization')}
                      variant="outline"
                    >
                      优化方案
                    </Button>
                    <Button
                      onClick={() => {
                        if (onPlanGenerated) {
                          onPlanGenerated(currentDraft);
                        }
                      }}
                      className="flex items-center space-x-2"
                    >
                      <Send className="h-4 w-4" />
                      <span>发送给客户</span>
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-600">暂无方案草稿</p>
                  <Button
                    onClick={() => setActiveTab('generation')}
                    variant="outline"
                    className="mt-2"
                  >
                    生成方案
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 优化调整标签 */}
        <TabsContent value="optimization" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <RefreshCw className="h-5 w-5" />
                <span>优化调整</span>
              </CardTitle>
              <CardDescription>
                根据需求优化和调整方案
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {currentDraft ? (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>优化类型</Label>
                    <Select value={optimizationType} onValueChange={(value: any) => setOptimizationType(value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="content">内容优化</SelectItem>
                        <SelectItem value="cost">费用优化</SelectItem>
                        <SelectItem value="timeline">时间优化</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>优化要求</Label>
                    <Textarea
                      value={optimizationRequirements}
                      onChange={(e) => setOptimizationRequirements(e.target.value)}
                      placeholder="请描述您的优化要求..."
                      rows={4}
                    />
                  </div>

                  <Button
                                          onClick={handleOptimizePlan}
                    disabled={isOptimizing || !optimizationRequirements.trim()}
                    className="w-full flex items-center justify-center space-x-2"
                  >
                    {isOptimizing ? (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    ) : (
                      <Sparkles className="h-4 w-4" />
                    )}
                    <span>{isOptimizing ? '优化中...' : '优化方案'}</span>
                  </Button>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-600">请先生成方案后再进行优化</p>
                  <Button
                    onClick={() => setActiveTab('generation')}
                    variant="outline"
                    className="mt-2"
                  >
                    生成方案
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
} 