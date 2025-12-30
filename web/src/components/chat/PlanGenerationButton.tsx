'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Sparkles, RefreshCw, Zap, Brain } from 'lucide-react';
import PlanGenerationPanel from './PlanGenerationPanel';

interface PlanGenerationButtonProps {
  conversationId: string;
  customerId: string;
  consultantId: string;
  disabled?: boolean;
  onPlanGenerated?: (plan: any) => void;
}

export default function PlanGenerationButton({
  conversationId,
  customerId,
  consultantId,
  disabled = false,
  onPlanGenerated
}: PlanGenerationButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleOpenPanel = () => {
    setIsOpen(true);
  };

  const handleClosePanel = () => {
    setIsOpen(false);
  };

  const handlePlanGenerated = (plan: any) => {
    setIsGenerating(false);
    if (onPlanGenerated) {
      onPlanGenerated(plan);
    }
    // 可以选择是否自动关闭面板
    // setIsOpen(false);
  };

  return (
    <>
      <Button
        onClick={handleOpenPanel}
        disabled={disabled || isGenerating}
        className="group relative overflow-hidden bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 hover:from-blue-600 hover:via-purple-600 hover:to-pink-600 text-white border-0 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
        size="sm"
      >
        {/* 闪烁效果 */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-0 group-hover:opacity-20 transform -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 ease-out"></div>
        
        <div className="relative flex items-center space-x-2">
          {isGenerating ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <div className="relative">
              <Brain className="h-4 w-4" />
              <Sparkles className="h-2 w-2 absolute -top-1 -right-1 animate-pulse text-yellow-300" />
            </div>
          )}
          <span className="font-medium">AI方案生成</span>
          {!disabled && (
            <Badge variant="secondary" className="bg-yellow-400 text-yellow-900 text-xs px-1.5 py-0.5 font-bold">
              Beta
            </Badge>
          )}
        </div>
      </Button>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-7xl h-[95vh] w-[95vw] p-0 bg-gradient-to-br from-gray-50 to-white border-0 shadow-2xl flex flex-col">
          {/* 固定的对话框头部 */}
          <DialogHeader className="shrink-0 px-6 py-4 bg-gradient-to-r from-blue-50 via-purple-50 to-pink-50 border-b border-gray-200">
            <DialogTitle className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl flex items-center justify-center">
                    <Brain className="h-6 w-6 text-white" />
                  </div>
                  <div className="absolute -top-1 -right-1 w-4 h-4 bg-yellow-400 rounded-full flex items-center justify-center">
                    <Sparkles className="h-2 w-2 text-yellow-900" />
                  </div>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">AI辅助方案生成</h2>
                  <p className="text-sm text-gray-600 mt-0.5">智能分析对话内容，生成个性化美肌方案</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <Badge className="bg-gradient-to-r from-green-100 to-blue-100 text-green-800 border-green-200 px-3 py-1">
                  <Zap className="h-3 w-3 mr-1" />
                  AI驱动
                </Badge>
              </div>
            </DialogTitle>
            <DialogDescription className="sr-only">
              AI辅助方案生成工具，智能分析对话内容并生成个性化方案
            </DialogDescription>
          </DialogHeader>
          
          {/* 可滚动的面板内容区域 */}
          <div className="flex-1 overflow-y-auto overflow-x-hidden bg-white">
            <PlanGenerationPanel
              conversationId={conversationId}
              customerId={customerId}
              consultantId={consultantId}
              onClose={handleClosePanel}
              onPlanGenerated={handlePlanGenerated}
            />
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
} 