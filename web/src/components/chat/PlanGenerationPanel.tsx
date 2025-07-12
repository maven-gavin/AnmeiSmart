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
  Lightbulb,
  User,
  Star,
  TrendingUp,
  Shield,
  Activity
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

// 格式化方案内容展示的组件
const PlanContentDisplay: React.FC<{ content: any }> = ({ content }) => {
  if (!content) {
    return <div className="text-gray-500 text-center py-8">暂无方案内容</div>;
  }

  // 尝试解析方案内容
  const parseContent = (data: any) => {
    if (typeof data === 'string') {
      try {
        return JSON.parse(data);
      } catch {
        return { summary: data };
      }
    }
    return data;
  };

  const planData = parseContent(content);

  return (
    <div className="space-y-6">
      {/* 方案概要 */}
      {planData.summary && (
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 border border-blue-100">
          <div className="flex items-center space-x-2 mb-3">
            <Star className="h-5 w-5 text-blue-600" />
            <h3 className="font-semibold text-gray-900">方案概要</h3>
          </div>
          <p className="text-gray-700 leading-relaxed">{planData.summary}</p>
        </div>
      )}

      {/* 客户信息 */}
      {planData.customer_info && (
        <div className="bg-green-50 rounded-xl p-6 border border-green-100">
          <div className="flex items-center space-x-2 mb-3">
            <User className="h-5 w-5 text-green-600" />
            <h3 className="font-semibold text-gray-900">客户信息</h3>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            {Object.entries(planData.customer_info).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="text-gray-600">{key}:</span>
                <span className="text-gray-900 font-medium">{String(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 推荐项目 */}
      {planData.treatments && (
        <div className="bg-orange-50 rounded-xl p-6 border border-orange-100">
          <div className="flex items-center space-x-2 mb-3">
            <TrendingUp className="h-5 w-5 text-orange-600" />
            <h3 className="font-semibold text-gray-900">推荐项目</h3>
          </div>
          <div className="space-y-3">
            {planData.treatments.map((treatment: any, index: number) => (
              <div key={index} className="bg-white rounded-lg p-4 border border-orange-200">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">{treatment.name || treatment.title}</h4>
                  {treatment.priority && (
                    <Badge variant="outline" className="text-orange-600 border-orange-200">
                      {treatment.priority}
                    </Badge>
                  )}
                </div>
                {treatment.description && (
                  <p className="text-gray-600 text-sm mb-2">{treatment.description}</p>
                )}
                {treatment.expected_result && (
                  <p className="text-green-600 text-sm">预期效果: {treatment.expected_result}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 时间安排 */}
      {planData.timeline && (
        <div className="bg-purple-50 rounded-xl p-6 border border-purple-100">
          <div className="flex items-center space-x-2 mb-3">
            <Calendar className="h-5 w-5 text-purple-600" />
            <h3 className="font-semibold text-gray-900">时间安排</h3>
          </div>
          <div className="space-y-2">
            {Array.isArray(planData.timeline) ? (
              planData.timeline.map((phase: any, index: number) => (
                <div key={index} className="bg-white rounded-lg p-3 border border-purple-200">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-900">{phase.phase || phase.name}</span>
                    <span className="text-purple-600 text-sm">{phase.duration || phase.time}</span>
                  </div>
                  {phase.description && (
                    <p className="text-gray-600 text-sm mt-1">{phase.description}</p>
                  )}
                </div>
              ))
            ) : (
              <div className="bg-white rounded-lg p-3 border border-purple-200">
                <p className="text-gray-700">{planData.timeline}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 费用预算 */}
      {planData.cost && (
        <div className="bg-yellow-50 rounded-xl p-6 border border-yellow-100">
          <div className="flex items-center space-x-2 mb-3">
            <DollarSign className="h-5 w-5 text-yellow-600" />
            <h3 className="font-semibold text-gray-900">费用预算</h3>
          </div>
          {typeof planData.cost === 'object' ? (
            <div className="space-y-2">
              {Object.entries(planData.cost).map(([key, value]) => (
                <div key={key} className="flex justify-between items-center bg-white rounded-lg p-3 border border-yellow-200">
                  <span className="text-gray-700">{key}</span>
                  <span className="font-semibold text-gray-900">¥{String(value)}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-white rounded-lg p-3 border border-yellow-200">
              <p className="font-semibold text-gray-900">¥{String(planData.cost)}</p>
            </div>
          )}
        </div>
      )}

      {/* 注意事项 */}
      {planData.precautions && (
        <div className="bg-red-50 rounded-xl p-6 border border-red-100">
          <div className="flex items-center space-x-2 mb-3">
            <Shield className="h-5 w-5 text-red-600" />
            <h3 className="font-semibold text-gray-900">注意事项</h3>
          </div>
          <div className="space-y-2">
            {Array.isArray(planData.precautions) ? (
              planData.precautions.map((precaution: string, index: number) => (
                <div key={index} className="flex items-start space-x-2 bg-white rounded-lg p-3 border border-red-200">
                  <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700 text-sm">{precaution}</span>
                </div>
              ))
            ) : (
              <div className="flex items-start space-x-2 bg-white rounded-lg p-3 border border-red-200">
                <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                <span className="text-gray-700">{planData.precautions}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 原始数据（开发调试用，可在生产环境中移除） */}
      <details className="mt-6">
        <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
          查看原始数据（调试用）
        </summary>
        <pre className="mt-2 text-xs bg-gray-100 rounded-lg p-3 overflow-auto">
          {JSON.stringify(planData, null, 2)}
        </pre>
      </details>
    </div>
  );
};

// 改进的进度指示器组件
const ProgressIndicator: React.FC<{ currentStep: number; steps: string[] }> = ({ currentStep, steps }) => {
  return (
    <div className="flex items-center justify-between mb-6">
      {steps.map((step, index) => (
        <div key={index} className="flex items-center">
          <div className={`
            flex items-center justify-center w-8 h-8 rounded-full border-2 
            ${index < currentStep 
              ? 'bg-green-500 border-green-500 text-white' 
              : index === currentStep 
                ? 'bg-blue-500 border-blue-500 text-white animate-pulse'
                : 'bg-gray-100 border-gray-300 text-gray-400'
            }
          `}>
            {index < currentStep ? (
              <CheckCircle className="h-4 w-4" />
            ) : (
              <span className="text-sm font-medium">{index + 1}</span>
            )}
          </div>
          <span className={`ml-2 text-sm font-medium ${
            index <= currentStep ? 'text-gray-900' : 'text-gray-400'
          }`}>
            {step}
          </span>
          {index < steps.length - 1 && (
            <div className={`w-8 h-0.5 mx-4 ${
              index < currentStep ? 'bg-green-500' : 'bg-gray-200'
            }`} />
          )}
        </div>
      ))}
    </div>
  );
};

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
  
  // 错误状态
  const [error, setError] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [generationError, setGenerationError] = useState<string | null>(null);
  
  // UI状态
  const [activeTab, setActiveTab] = useState('analysis');
  const [showOptimizeDialog, setShowOptimizeDialog] = useState(false);
  const [optimizationRequirements, setOptimizationRequirements] = useState('');
  const [optimizationType, setOptimizationType] = useState<'cost' | 'timeline' | 'content'>('content');

  // 进度步骤
  const progressSteps = ['信息分析', '方案生成', '内容预览', '优化调整'];

  // 获取当前步骤
  const getCurrentStep = () => {
    switch (activeTab) {
      case 'analysis': return 0;
      case 'generation': return 1;
      case 'preview': return 2;
      case 'optimization': return 3;
      default: return 0;
    }
  };

  // 初始化会话
  useEffect(() => {
    initializeSession();
  }, [conversationId]);

  const initializeSession = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
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
      setError('初始化AI方案生成失败，请检查网络连接后重试');
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
      setAnalysisError(null);
      
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
      setAnalysisError('信息分析失败，请稍后重试。可能是对话内容不足或AI服务暂时不可用');
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
      setGenerationError(null);
      
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
      setGenerationError('方案生成失败，请稍后重试。可能是AI服务负载过高或网络不稳定');
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
      case 'collecting': return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'generating': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'optimizing': return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'reviewing': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'completed': return 'bg-green-100 text-green-800 border-green-200';
      case 'failed': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
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
          <div className="relative">
            <RefreshCw className="h-12 w-12 animate-spin mx-auto mb-4 text-blue-500" />
            <div className="absolute inset-0 rounded-full bg-blue-100 animate-ping opacity-20"></div>
          </div>
          <p className="text-gray-600 font-medium">正在初始化方案生成会话...</p>
          <p className="text-gray-400 text-sm mt-1">请稍候，这可能需要几秒钟</p>
        </div>
      </div>
    );
  }

  // 如果初始化失败，显示错误和重试按钮
  if (error && !session) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="font-medium">{error}</AlertDescription>
        </Alert>
        <div className="flex space-x-3">
          <Button onClick={initializeSession} variant="outline" className="flex items-center space-x-2">
            <RefreshCw className="h-4 w-4" />
            <span>重新初始化</span>
          </Button>
          <Button onClick={onClose} variant="outline">
            关闭
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full p-6 space-y-6">
      {/* 优化的标题和状态 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">AI辅助方案生成</h2>
          <p className="text-gray-600">智能分析客户需求，生成个性化美肌方案</p>
        </div>
        <div className="flex items-center space-x-3">
          {session && (
            <Badge className={`${getStatusColor(session.status)} border font-medium px-3 py-1`}>
              <Activity className="h-3 w-3 mr-1" />
              {getStatusText(session.status)}
            </Badge>
          )}
          <Button variant="outline" onClick={onClose} className="hover:bg-gray-50">
            关闭
          </Button>
        </div>
      </div>

      {/* 进度指示器 */}
      <ProgressIndicator currentStep={getCurrentStep()} steps={progressSteps} />

      {/* 主要内容 */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 bg-gray-100 p-1 rounded-xl">
          <TabsTrigger value="analysis" className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm">
            信息分析
          </TabsTrigger>
          <TabsTrigger value="generation" className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm">
            方案生成
          </TabsTrigger>
          <TabsTrigger value="preview" className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm">
            方案预览
          </TabsTrigger>
          <TabsTrigger value="optimization" className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm">
            优化调整
          </TabsTrigger>
        </TabsList>

        {/* 信息分析标签 */}
        <TabsContent value="analysis" className="space-y-6">
          <Card className="border-0 shadow-lg">
            <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-t-xl">
              <CardTitle className="flex items-center space-x-2">
                <Sparkles className="h-5 w-5 text-blue-600" />
                <span>信息完整性分析</span>
              </CardTitle>
              <CardDescription>
                AI分析对话内容，评估生成方案所需信息的完整性
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6 p-6">
              {/* 显示分析错误 */}
              {analysisError && (
                <Alert variant="destructive" className="border-red-200">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription className="font-medium">{analysisError}</AlertDescription>
                </Alert>
              )}
              
              {analysis ? (
                <div className="space-y-6">
                  {/* 完整性得分 */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">信息完整性得分</span>
                      <span className="text-lg font-bold text-blue-600">
                        {Math.round(analysis.completeness_score * 100)}%
                      </span>
                    </div>
                    <Progress 
                      value={analysis.completeness_score * 100} 
                      className="h-3 bg-gray-100" 
                    />
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>需要改进</span>
                      <span>良好</span>
                      <span>优秀</span>
                    </div>
                  </div>

                  {/* 缺失信息类别 */}
                  {analysis.missing_categories.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-medium text-gray-700">缺失信息类别</h4>
                      <div className="flex flex-wrap gap-2">
                        {analysis.missing_categories.map((category, index) => (
                          <Badge key={index} variant="outline" className="flex items-center space-x-1 border-orange-200 text-orange-700 bg-orange-50">
                            {getCategoryIcon(category)}
                            <span>{getCategoryName(category)}</span>
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 建议 - 确保这部分可以完整显示 */}
                  {analysis.suggestions.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-medium text-gray-700">改进建议</h4>
                      <div className="space-y-2 max-h-none"> {/* 移除高度限制 */}
                        {analysis.suggestions.map((suggestion, index) => (
                          <div key={index} className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                            <Lightbulb className="h-4 w-4 mt-0.5 flex-shrink-0 text-yellow-600" />
                            <span className="text-sm text-gray-700 leading-relaxed">{suggestion}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 生成状态 */}
                  <Alert className={analysis.can_generate_plan ? 'border-green-200 bg-green-50' : 'border-amber-200 bg-amber-50'}>
                    <CheckCircle className={`h-4 w-4 ${analysis.can_generate_plan ? 'text-green-600' : 'text-amber-600'}`} />
                    <AlertDescription className="font-medium">
                      {analysis.can_generate_plan
                        ? "✅ 信息已足够，可以生成高质量方案"
                        : "⚠️ 需要补充更多信息才能生成高质量方案"}
                    </AlertDescription>
                  </Alert>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <Activity className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                  <p className="font-medium">尚未进行信息分析</p>
                  <p className="text-sm">点击下方按钮开始分析</p>
                </div>
              )}

              {/* 操作按钮 */}
              <div className="flex space-x-3 pt-4 border-t border-gray-100">
                <Button
                  onClick={() => {
                    setAnalysisError(null);
                    performAnalysis();
                  }}
                  disabled={isAnalyzing}
                  className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700"
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
                    className="border-green-200 text-green-700 hover:bg-green-50"
                  >
                    生成方案
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 方案生成标签 */}
        <TabsContent value="generation" className="space-y-6">
          <Card className="border-0 shadow-lg">
            <CardHeader className="bg-gradient-to-r from-green-50 to-blue-50 rounded-t-xl">
              <CardTitle className="flex items-center space-x-2">
                <FileText className="h-5 w-5 text-green-600" />
                <span>方案生成</span>
              </CardTitle>
              <CardDescription>
                基于分析结果生成个性化美肌方案
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6 p-6">
              {/* 显示生成错误 */}
              {generationError && (
                <Alert variant="destructive" className="border-red-200">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription className="font-medium">{generationError}</AlertDescription>
                </Alert>
              )}
              
              {analysis?.can_generate_plan ? (
                <div className="space-y-6">
                  <Alert className="border-green-200 bg-green-50">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <AlertDescription className="font-medium text-green-800">
                      ✅ 信息完整性良好（{Math.round(analysis.completeness_score * 100)}%），
                      可以生成高质量的个性化方案
                    </AlertDescription>
                  </Alert>

                  <div className="bg-gray-50 rounded-xl p-6 space-y-4">
                    <h4 className="font-medium text-gray-900 flex items-center space-x-2">
                      <Target className="h-4 w-4" />
                      <span>方案生成选项</span>
                    </h4>
                    <div className="grid grid-cols-2 gap-4">
                      <label className="flex items-center space-x-3 p-3 bg-white rounded-lg border border-gray-200 cursor-pointer hover:bg-blue-50 hover:border-blue-200">
                        <input type="checkbox" id="include_timeline" defaultChecked className="text-blue-600" />
                        <span className="text-sm font-medium">包含时间规划</span>
                      </label>
                      <label className="flex items-center space-x-3 p-3 bg-white rounded-lg border border-gray-200 cursor-pointer hover:bg-blue-50 hover:border-blue-200">
                        <input type="checkbox" id="include_cost" defaultChecked className="text-blue-600" />
                        <span className="text-sm font-medium">包含费用明细</span>
                      </label>
                    </div>
                  </div>

                  <Button
                    onClick={() => {
                      setGenerationError(null);
                      handleGeneratePlan();
                    }}
                    disabled={isGenerating}
                    className="w-full h-12 text-lg bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 shadow-lg"
                  >
                    {isGenerating ? (
                      <div className="flex items-center space-x-2">
                        <RefreshCw className="h-5 w-5 animate-spin" />
                        <span>AI正在生成方案...</span>
                      </div>
                    ) : (
                      <div className="flex items-center space-x-2">
                        <Sparkles className="h-5 w-5" />
                        <span>开始生成方案</span>
                      </div>
                    )}
                  </Button>
                </div>
              ) : (
                <div className="text-center py-12">
                  <AlertCircle className="h-16 w-16 text-amber-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">信息完整性不足</h3>
                  <p className="text-gray-600 mb-6">
                    建议先补充更多信息以确保方案质量
                  </p>
                  <Button
                    onClick={() => setActiveTab('analysis')}
                    variant="outline"
                    className="border-amber-200 text-amber-700 hover:bg-amber-50"
                  >
                    返回分析
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 方案预览标签 */}
        <TabsContent value="preview" className="space-y-6">
          <Card className="border-0 shadow-lg">
            <CardHeader className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-t-xl">
              <CardTitle className="flex items-center space-x-2">
                <Eye className="h-5 w-5 text-purple-600" />
                <span>方案预览</span>
              </CardTitle>
              <CardDescription>
                查看生成的方案内容
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              {currentDraft ? (
                <div className="space-y-6">
                  {/* 版本信息 */}
                  <div className="flex items-center justify-between p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl border border-purple-200">
                    <div className="flex items-center space-x-3">
                      <div className="bg-purple-100 p-2 rounded-lg">
                        <FileText className="h-5 w-5 text-purple-600" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900">版本 {currentDraft.version}</h4>
                        <p className="text-sm text-gray-600">
                          {new Date(currentDraft.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <Badge className={`${getStatusColor(currentDraft.status)} border font-medium`}>
                      {currentDraft.status}
                    </Badge>
                  </div>

                  {/* 优化的方案内容显示 */}
                  <div className="border border-gray-200 rounded-xl overflow-hidden">
                    <div className="bg-gray-50 px-6 py-3 border-b border-gray-200">
                      <h5 className="font-semibold text-gray-900 flex items-center space-x-2">
                        <Star className="h-4 w-4 text-yellow-500" />
                        <span>方案内容</span>
                      </h5>
                    </div>
                    <div className="p-6">
                      <PlanContentDisplay content={currentDraft.content} />
                    </div>
                  </div>

                  {/* 操作按钮 */}
                  <div className="flex space-x-3 pt-4 border-t border-gray-100">
                    <Button
                      onClick={() => setActiveTab('optimization')}
                      variant="outline"
                      className="flex items-center space-x-2 border-purple-200 text-purple-700 hover:bg-purple-50"
                    >
                      <RefreshCw className="h-4 w-4" />
                      <span>优化方案</span>
                    </Button>
                    <Button
                      onClick={() => {
                        if (onPlanGenerated) {
                          onPlanGenerated(currentDraft);
                        }
                      }}
                      className="flex items-center space-x-2 bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600"
                    >
                      <Send className="h-4 w-4" />
                      <span>发送给客户</span>
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <FileText className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">暂无方案草稿</h3>
                  <p className="text-gray-600 mb-6">请先生成方案</p>
                  <Button
                    onClick={() => setActiveTab('generation')}
                    variant="outline"
                    className="border-blue-200 text-blue-700 hover:bg-blue-50"
                  >
                    生成方案
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 优化调整标签 */}
        <TabsContent value="optimization" className="space-y-6">
          <Card className="border-0 shadow-lg">
            <CardHeader className="bg-gradient-to-r from-orange-50 to-red-50 rounded-t-xl">
              <CardTitle className="flex items-center space-x-2">
                <RefreshCw className="h-5 w-5 text-orange-600" />
                <span>优化调整</span>
              </CardTitle>
              <CardDescription>
                根据需求优化和调整方案
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6 p-6">
              {currentDraft ? (
                <div className="space-y-6">
                  <div className="bg-orange-50 rounded-xl p-6 border border-orange-200">
                    <h4 className="font-medium text-gray-900 mb-4 flex items-center space-x-2">
                      <Target className="h-4 w-4 text-orange-600" />
                      <span>优化配置</span>
                    </h4>
                    
                    <div className="space-y-4">
                      <div>
                        <Label className="text-sm font-medium text-gray-700">优化类型</Label>
                        <Select value={optimizationType} onValueChange={(value: any) => setOptimizationType(value)}>
                          <SelectTrigger className="mt-1 bg-white border-gray-200">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="content">内容优化</SelectItem>
                            <SelectItem value="cost">费用优化</SelectItem>
                            <SelectItem value="timeline">时间优化</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label className="text-sm font-medium text-gray-700">优化要求</Label>
                        <Textarea
                          value={optimizationRequirements}
                          onChange={(e) => setOptimizationRequirements(e.target.value)}
                          placeholder="请详细描述您的优化要求，例如：降低预算、缩短时间、调整项目等..."
                          rows={4}
                          className="mt-1 bg-white border-gray-200 resize-none"
                        />
                      </div>
                    </div>
                  </div>

                  <Button
                    onClick={handleOptimizePlan}
                    disabled={isOptimizing || !optimizationRequirements.trim()}
                    className="w-full h-12 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 disabled:opacity-50"
                  >
                    {isOptimizing ? (
                      <div className="flex items-center space-x-2">
                        <RefreshCw className="h-5 w-5 animate-spin" />
                        <span>AI正在优化方案...</span>
                      </div>
                    ) : (
                      <div className="flex items-center space-x-2">
                        <Sparkles className="h-5 w-5" />
                        <span>开始优化方案</span>
                      </div>
                    )}
                  </Button>
                </div>
              ) : (
                <div className="text-center py-12">
                  <RefreshCw className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">请先生成方案</h3>
                  <p className="text-gray-600 mb-6">优化功能需要基于已生成的方案</p>
                  <Button
                    onClick={() => setActiveTab('generation')}
                    variant="outline"
                    className="border-orange-200 text-orange-700 hover:bg-orange-50"
                  >
                    生成方案
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 底部额外间距，确保内容可以完全滚动到 */}
      <div className="h-6"></div>
    </div>
  );
} 