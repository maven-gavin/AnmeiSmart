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
  DialogTitle 
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, Sparkles, FileText, Users, Clock, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import { 
  PlanGenerationSession, 
  InfoAnalysis, 
  PlanDraft, 
  createPlanGenerationSession,
  analyzeConversationInfo,
  generatePlan,
  optimizePlan,
  getPlanGenerationSession,
  getPlanGenerationSessionByConversation,
  getSessionVersions,
  getDraft
} from '@/service/planGenerationService';

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
  // 主要状态
  const [session, setSession] = useState<PlanGenerationSession | null>(null);
  const [analysis, setAnalysis] = useState<InfoAnalysis | null>(null);
  const [currentDraft, setCurrentDraft] = useState<PlanDraft | null>(null);
  const [versions, setVersions] = useState<PlanDraft[]>([]);
  
  // UI状态
  const [activeTab, setActiveTab] = useState<'analysis' | 'generation' | 'optimization' | 'versions'>('analysis');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [step, setStep] = useState<'init' | 'analyzing' | 'generating' | 'optimizing' | 'completed'>('init');
  
  // 表单状态
  const [optimizationFeedback, setOptimizationFeedback] = useState('');
  const [optimizationType, setOptimizationType] = useState<'content' | 'cost' | 'timeline'>('content');

  // 初始化会话
  useEffect(() => {
    initializeSession();
  }, [conversationId]);

  const initializeSession = async () => {
    try {
      setLoading(true);
      setStep('init');
      
      // 尝试获取现有会话
      let existingSession = await getPlanGenerationSessionByConversation(conversationId);
      
      if (!existingSession) {
        // 创建新会话
        existingSession = await createPlanGenerationSession({
          conversation_id: conversationId,
          customer_id: customerId,
          consultant_id: consultantId,
          session_metadata: {
            created_from: 'chat_interface'
          }
        });
      }
      
      setSession(existingSession);
      
      // 如果会话已有分析结果，直接使用
      if (existingSession.status !== 'collecting') {
        await loadSessionData(existingSession.id);
      }
      
    } catch (error) {
      console.error('初始化会话失败:', error);
      setError('初始化失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const loadSessionData = async (sessionId: string) => {
    try {
      // 加载会话详情
      const sessionData = await getPlanGenerationSession(sessionId);
      setSession(sessionData);
      
      // 加载版本列表
      const versionList = await getSessionVersions(sessionId);
      setVersions(versionList);
      
      // 设置当前草稿为最新版本
      if (versionList.length > 0) {
        setCurrentDraft(versionList[0]);
      }
      
    } catch (error) {
      console.error('加载会话数据失败:', error);
      setError('加载数据失败');
    }
  };

  const handleStartAnalysis = async () => {
    if (!session) return;
    
    try {
      setLoading(true);
      setStep('analyzing');
      setProgress(25);
      
      const analysisResult = await analyzeConversationInfo({
        conversation_id: conversationId
      });
      
      setAnalysis(analysisResult);
      setProgress(50);
      
      // 如果信息充分，自动进入生成阶段
      if (analysisResult.can_generate_plan) {
        setActiveTab('generation');
        setStep('generating');
      } else {
        setStep('completed');
      }
      
    } catch (error) {
      console.error('分析失败:', error);
      setError('信息分析失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePlan = async () => {
    if (!session || !analysis) return;
    
    try {
      setLoading(true);
      setStep('generating');
      setProgress(75);
      
      const planResponse = await generatePlan({
        conversation_id: conversationId,
        generation_options: {
          include_timeline: true,
          include_cost_breakdown: true
        }
      });
      
      // 获取生成的草稿
      const draft = await getDraft(planResponse.draft_id);
      setCurrentDraft(draft);
      setProgress(100);
      setStep('completed');
      setActiveTab('generation');
      
      // 刷新版本列表
      await loadSessionData(session.id);
      
      // 通知外部组件
      if (onPlanGenerated) {
        onPlanGenerated(draft);
      }
      
    } catch (error) {
      console.error('方案生成失败:', error);
      setError('方案生成失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleOptimizePlan = async () => {
    if (!session || !currentDraft || !optimizationFeedback.trim()) return;
    
    try {
      setLoading(true);
      setStep('optimizing');
      
      const optimizedPlan = await optimizePlan({
        draft_id: currentDraft.id,
        optimization_type: optimizationType,
        feedback: optimizationFeedback,
        requirements: {
          maintain_budget: optimizationType !== 'cost',
          maintain_timeline: optimizationType !== 'timeline',
          maintain_treatments: optimizationType !== 'content'
        }
      });
      
      setCurrentDraft(optimizedPlan);
      setOptimizationFeedback('');
      setStep('completed');
      
      // 刷新版本列表
      await loadSessionData(session.id);
      
    } catch (error) {
      console.error('方案优化失败:', error);
      setError('方案优化失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const renderAnalysisTab = () => (
    <TabsContent value="analysis" className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            信息分析
          </CardTitle>
          <CardDescription>
            分析对话内容，提取客户需求和偏好
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!analysis ? (
            <div className="text-center py-8">
              <Button 
                onClick={handleStartAnalysis} 
                disabled={loading}
                className="flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    分析中...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    开始分析
                  </>
                )}
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">信息完整度</h3>
                <Badge variant={analysis.can_generate_plan ? "default" : "secondary"}>
                  {Math.round(analysis.completeness_score * 100)}%
                </Badge>
              </div>
              
              <Progress value={analysis.completeness_score * 100} className="h-2" />
              
              {analysis.missing_categories.length > 0 && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    缺失信息: {analysis.missing_categories.join(', ')}
                  </AlertDescription>
                </Alert>
              )}
              
              {analysis.suggestions.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium">建议补充:</h4>
                  <ul className="list-disc list-inside space-y-1 text-sm">
                    {analysis.suggestions.map((suggestion, index) => (
                      <li key={index}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {analysis.can_generate_plan && (
                <Alert>
                  <CheckCircle className="h-4 w-4" />
                  <AlertDescription>
                    信息已充分，可以生成方案
                  </AlertDescription>
                </Alert>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </TabsContent>
  );

  const renderGenerationTab = () => (
    <TabsContent value="generation" className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            方案生成
          </CardTitle>
          <CardDescription>
            基于分析结果生成个性化方案
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!currentDraft ? (
            <div className="text-center py-8">
              <Button 
                onClick={handleGeneratePlan} 
                disabled={loading || !analysis?.can_generate_plan}
                className="flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    生成中...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    生成方案
                  </>
                )}
              </Button>
              
              {!analysis?.can_generate_plan && (
                <p className="text-sm text-gray-500 mt-2">
                  请先完成信息分析
                </p>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">方案概览</h3>
                <Badge variant="outline">
                  版本 {currentDraft.version}
                </Badge>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="space-y-3">
                  <div>
                    <h4 className="font-medium">推荐项目</h4>
                    <p className="text-sm text-gray-600">
                      {currentDraft.content?.recommended_treatments?.join(', ') || '暂无数据'}
                    </p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium">预估费用</h4>
                    <p className="text-sm text-gray-600">
                      {currentDraft.content?.cost_estimate || '暂无数据'}
                    </p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium">预计时间</h4>
                    <p className="text-sm text-gray-600">
                      {currentDraft.content?.timeline || '暂无数据'}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  onClick={() => setActiveTab('optimization')}
                  className="flex items-center gap-2"
                >
                  <FileText className="h-4 w-4" />
                  优化方案
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => setActiveTab('versions')}
                  className="flex items-center gap-2"
                >
                  <Clock className="h-4 w-4" />
                  查看版本
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </TabsContent>
  );

  const renderOptimizationTab = () => (
    <TabsContent value="optimization" className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            方案优化
          </CardTitle>
          <CardDescription>
            根据反馈优化方案内容
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!currentDraft ? (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                请先生成方案
              </AlertDescription>
            </Alert>
          ) : (
            <div className="space-y-4">
              <div>
                <Label htmlFor="optimization-type">优化类型</Label>
                <Select 
                  value={optimizationType} 
                  onValueChange={(value: "content" | "cost" | "timeline") => setOptimizationType(value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择优化类型" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="content">内容优化</SelectItem>
                    <SelectItem value="cost">费用优化</SelectItem>
                    <SelectItem value="timeline">时间优化</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label htmlFor="optimization-feedback">优化要求</Label>
                <Textarea
                  id="optimization-feedback"
                  placeholder="请描述需要优化的具体内容..."
                  value={optimizationFeedback}
                  onChange={(e) => setOptimizationFeedback(e.target.value)}
                  rows={4}
                />
              </div>
              
              <Button 
                onClick={handleOptimizePlan}
                disabled={loading || !optimizationFeedback.trim()}
                className="w-full flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    优化中...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    开始优化
                  </>
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </TabsContent>
  );

  const renderVersionsTab = () => (
    <TabsContent value="versions" className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            版本历史
          </CardTitle>
          <CardDescription>
            查看方案的所有版本
          </CardDescription>
        </CardHeader>
        <CardContent>
          {versions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              暂无版本历史
            </div>
          ) : (
            <div className="space-y-3">
              {versions.map((version) => (
                <div 
                  key={version.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    currentDraft?.id === version.id 
                      ? 'bg-blue-50 border-blue-200' 
                      : 'hover:bg-gray-50'
                  }`}
                  onClick={() => setCurrentDraft(version)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">版本 {version.version}</span>
                        {currentDraft?.id === version.id && (
                          <Badge variant="default">当前</Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-600">
                        {new Date(version.created_at).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">
                        {version.status}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </TabsContent>
  );

  return (
    <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5" />
          AI辅助方案生成
        </DialogTitle>
        <DialogDescription>
          智能分析对话内容，生成个性化医美方案
        </DialogDescription>
      </DialogHeader>
      
      {error && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      
      {loading && step !== 'init' && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm">
              {step === 'analyzing' && '正在分析对话内容...'}
              {step === 'generating' && '正在生成方案...'}
              {step === 'optimizing' && '正在优化方案...'}
            </span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>
      )}
      
      <Tabs 
        defaultValue={activeTab} 
        onValueChange={(value: string) => setActiveTab(value as "analysis" | "generation" | "optimization" | "versions")} 
        className="w-full"
      >
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="analysis">信息分析</TabsTrigger>
          <TabsTrigger value="generation">方案生成</TabsTrigger>
          <TabsTrigger value="optimization">方案优化</TabsTrigger>
          <TabsTrigger value="versions">版本历史</TabsTrigger>
        </TabsList>
        
        {renderAnalysisTab()}
        {renderGenerationTab()}
        {renderOptimizationTab()}
        {renderVersionsTab()}
      </Tabs>
      
      <div className="flex justify-end gap-2 pt-4 border-t">
        <Button variant="outline" onClick={onClose}>
          关闭
        </Button>
        {currentDraft && (
          <Button 
            onClick={() => {
              if (onPlanGenerated) {
                onPlanGenerated(currentDraft);
              }
              onClose();
            }}
          >
            使用方案
          </Button>
        )}
      </div>
    </DialogContent>
  );
} 