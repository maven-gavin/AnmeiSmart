'use client';

import { useState, useRef, useEffect } from 'react';
import { Volume2, VolumeX, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'react-hot-toast';
import { apiClient } from '@/service/apiClient';

interface TextToSpeechButtonProps {
  text: string;
  agentConfigId: string;
  messageId: string;
}

export function TextToSpeechButton({
  text,
  agentConfigId,
  messageId
}: TextToSpeechButtonProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlRef = useRef<string | null>(null);

  // 清理音频资源
  useEffect(() => {
    return () => {
      if (audioUrlRef.current) {
        URL.revokeObjectURL(audioUrlRef.current);
      }
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  const handlePlay = async () => {
    try {
      setIsLoading(true);
      
      // 调用后端 TTS API
      const response = await apiClient.post(
        `/agent/${agentConfigId}/text-to-audio`,
        {
          body: {
            text: text.substring(0, 1000), // 限制文本长度
            streaming: false
          },
          responseType: 'blob' as any
        }
      );

      // 创建音频 URL
      const audioBlob = response.data as Blob;
      const audioUrl = URL.createObjectURL(audioBlob);
      
      // 释放旧的 URL
      if (audioUrlRef.current) {
        URL.revokeObjectURL(audioUrlRef.current);
      }
      audioUrlRef.current = audioUrl;

      // 创建或更新音频元素
      if (!audioRef.current) {
        audioRef.current = new Audio();
        audioRef.current.onended = () => setIsPlaying(false);
        audioRef.current.onerror = () => {
          setIsPlaying(false);
          toast.error('音频播放失败');
        };
      }

      audioRef.current.src = audioUrl;
      await audioRef.current.play();
      setIsPlaying(true);
    } catch (error) {
      console.error('TTS 失败:', error);
      toast.error('语音合成失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStop = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
    }
  };

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={isPlaying ? handleStop : handlePlay}
      disabled={isLoading || !text}
      title={isPlaying ? '停止播放' : '播放语音'}
      className="h-8 w-8 p-0"
    >
      {isLoading ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : isPlaying ? (
        <VolumeX className="h-4 w-4" />
      ) : (
        <Volume2 className="h-4 w-4" />
      )}
    </Button>
  );
}

