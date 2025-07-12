'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Sparkles, RefreshCw } from 'lucide-react';
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
        className="flex items-center space-x-2 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white"
        size="sm"
      >
        {isGenerating ? (
          <RefreshCw className="h-4 w-4 animate-spin" />
        ) : (
          <Sparkles className="h-4 w-4" />
        )}
        <span>AI方案生成</span>
      </Button>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <Sparkles className="h-5 w-5" />
              <span>AI辅助方案生成</span>
            </DialogTitle>
          </DialogHeader>
          
          <PlanGenerationPanel
            conversationId={conversationId}
            customerId={customerId}
            consultantId={consultantId}
            onClose={handleClosePanel}
            onPlanGenerated={handlePlanGenerated}
          />
        </DialogContent>
      </Dialog>
    </>
  );
} 