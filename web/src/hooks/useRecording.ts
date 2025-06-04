import { useState, useRef, useCallback, useEffect } from 'react'

export function useRecording() {
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null)

  // 清理函数
  const cleanupRecording = useCallback(() => {
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current)
      recordingTimerRef.current = null
    }
    setIsRecording(false)
    setRecordingTime(0)
    audioChunksRef.current = []
  }, [])

  // 开始录音
  const startRecording = useCallback(async (): Promise<string | null> => {
    try {
      // 请求麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder

      return new Promise((resolve, reject) => {
        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data)
          }
        }

        mediaRecorder.onstop = () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' })
          const audioUrl = URL.createObjectURL(audioBlob)
          cleanupRecording()
          
          // 停止所有音轨
          stream.getTracks().forEach(track => track.stop())
          
          resolve(audioUrl)
        }

        mediaRecorder.onerror = () => {
          cleanupRecording()
          stream.getTracks().forEach(track => track.stop())
          reject(new Error('录音失败'))
        }

        // 开始录制
        mediaRecorder.start()
        setIsRecording(true)

        // 开始计时
        recordingTimerRef.current = setInterval(() => {
          setRecordingTime(prev => prev + 1)
        }, 1000)
      })
    } catch (error) {
      console.error('录音失败:', error)
      alert('无法访问麦克风，请确保已授予麦克风权限')
      cleanupRecording()
      return null
    }
  }, [cleanupRecording])

  // 停止录音
  const stopRecording = useCallback((): Promise<string | null> => {
    return new Promise((resolve) => {
      if (mediaRecorderRef.current && isRecording) {
        const recorder = mediaRecorderRef.current
        const originalOnStop = recorder.onstop
        
        recorder.onstop = (event) => {
          if (originalOnStop) {
            originalOnStop.call(recorder, event)
          }
          // 这里resolve会在originalOnStop中被调用
        }
        
        recorder.stop()
      } else {
        resolve(null)
      }
    })
  }, [isRecording])

  // 取消录音
  const cancelRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      // 不保存录音结果
      cleanupRecording()
    }
  }, [isRecording, cleanupRecording])

  // 格式化录音时间
  const formatRecordingTime = useCallback((seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
  }, [])

  // 清理效果
  useEffect(() => {
    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current)
      }
      
      // 如果组件卸载时还在录音，则停止录音
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop()
      }
    }
  }, [isRecording])

  return {
    isRecording,
    recordingTime,
    startRecording,
    stopRecording,
    cancelRecording,
    formatRecordingTime
  }
} 