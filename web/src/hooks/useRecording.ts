import { useState, useRef, useCallback, useEffect } from 'react'

interface RecordingState {
  isRecording: boolean
  isPaused: boolean
  recordingTime: number
  totalPausedTime: number
}

export function useRecording() {
  const [state, setState] = useState<RecordingState>({
    isRecording: false,
    isPaused: false,
    recordingTime: 0,
    totalPausedTime: 0
  })
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const startTimeRef = useRef<number>(0)
  const pauseStartTimeRef = useRef<number>(0)

  // 清理函数
  const cleanupRecording = useCallback(() => {
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current)
      recordingTimerRef.current = null
    }
    
    // 停止所有音轨
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    
    setState({
      isRecording: false,
      isPaused: false,
      recordingTime: 0,
      totalPausedTime: 0
    })
    
    audioChunksRef.current = []
    startTimeRef.current = 0
    pauseStartTimeRef.current = 0
  }, [])

  // 更新录音时间
  const updateRecordingTime = useCallback(() => {
    if (state.isRecording && !state.isPaused) {
      const currentTime = Date.now()
      const elapsedTime = Math.floor((currentTime - startTimeRef.current - state.totalPausedTime) / 1000)
      setState(prev => ({ ...prev, recordingTime: elapsedTime }))
    }
  }, [state.isRecording, state.isPaused, state.totalPausedTime])

  // 开始录音
  const startRecording = useCallback(async (): Promise<void> => {
    try {
      // 请求麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      })
      
      streamRef.current = stream
      
      // 检测支持的MIME类型，优先选择兼容性更好的格式
      // 避免使用opus编解码器，因为它在某些浏览器中可能无法正确读取时长元数据
      let mimeType = 'audio/webm'
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = 'audio/mp4'
        if (!MediaRecorder.isTypeSupported(mimeType)) {
          mimeType = 'audio/ogg'
          if (!MediaRecorder.isTypeSupported(mimeType)) {
            mimeType = 'audio/webm;codecs=opus' // 最后才尝试opus
            if (!MediaRecorder.isTypeSupported(mimeType)) {
              mimeType = '' // 使用默认格式
            }
          }
        }
      }
      
      const mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
      mediaRecorderRef.current = mediaRecorder

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onerror = (event) => {
        console.error('录音出错:', event)
        cleanupRecording()
      }

      // 开始录制
      mediaRecorder.start(100) // 每100ms收集一次数据
      
      // 设置初始状态
      startTimeRef.current = Date.now()
      setState({
        isRecording: true,
        isPaused: false,
        recordingTime: 0,
        totalPausedTime: 0
      })

      // 开始计时
      recordingTimerRef.current = setInterval(updateRecordingTime, 100)
      
    } catch (error) {
      console.error('录音失败:', error)
      alert('无法访问麦克风，请确保已授予麦克风权限')
      cleanupRecording()
      throw error
    }
  }, [cleanupRecording, updateRecordingTime])

  // 暂停录音
  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && state.isRecording && !state.isPaused) {
      mediaRecorderRef.current.pause()
      pauseStartTimeRef.current = Date.now()
      setState(prev => ({ ...prev, isPaused: true }))
    }
  }, [state.isRecording, state.isPaused])

  // 继续录音
  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current && state.isRecording && state.isPaused) {
      mediaRecorderRef.current.resume()
      const pauseDuration = Date.now() - pauseStartTimeRef.current
      setState(prev => ({ 
        ...prev, 
        isPaused: false,
        totalPausedTime: prev.totalPausedTime + pauseDuration
      }))
      pauseStartTimeRef.current = 0
    }
  }, [state.isRecording, state.isPaused])

  // 停止录音
  const stopRecording = useCallback((): Promise<string | null> => {
    return new Promise((resolve, reject) => {
      if (mediaRecorderRef.current && state.isRecording) {
        const recorder = mediaRecorderRef.current
        
        recorder.onstop = () => {
          try {
            // 使用录音时的MIME类型创建Blob
            const mimeType = recorder.mimeType || 'audio/webm'
            const audioBlob = new Blob(audioChunksRef.current, { type: mimeType })
            
            // 创建 Object URL 而不是 Data URL，性能更好且兼容性更强
            const audioUrl = URL.createObjectURL(audioBlob)
            
            console.log('录音完成:', {
              mimeType,
              size: audioBlob.size,
              chunks: audioChunksRef.current.length
            })
            
            cleanupRecording()
            resolve(audioUrl)
          } catch (error) {
            console.error('处理录音文件失败:', error)
            cleanupRecording()
            reject(error)
          }
        }
        
        recorder.stop()
      } else {
        cleanupRecording()
        resolve(null)
      }
    })
  }, [state.isRecording, cleanupRecording])

  // 取消录音
  const cancelRecording = useCallback(() => {
    if (mediaRecorderRef.current && state.isRecording) {
      mediaRecorderRef.current.stop()
    }
    cleanupRecording()
  }, [state.isRecording, cleanupRecording])

  // 格式化录音时间
  const formatRecordingTime = useCallback((seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
  }, [])

  // 清理效果
  useEffect(() => {
    return () => {
      cleanupRecording()
    }
  }, [cleanupRecording])

  // 更新录音时间的效果
  useEffect(() => {
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current)
    }
    
    if (state.isRecording) {
      recordingTimerRef.current = setInterval(updateRecordingTime, 100)
    }
    
    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current)
      }
    }
  }, [state.isRecording, state.isPaused, updateRecordingTime])

  return {
    isRecording: state.isRecording,
    isPaused: state.isPaused,
    recordingTime: state.recordingTime,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    cancelRecording,
    formatRecordingTime
  }
} 