import { useState, useRef, useCallback } from 'react'

export function useMediaUpload() {
  // 图片上传状态
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [uploadingImage, setUploadingImage] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 语音相关状态
  const [audioPreview, setAudioPreview] = useState<string | null>(null)

  // 处理图片上传
  const handleImageUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    
    reader.onloadstart = () => {
      setUploadingImage(true)
    }
    
    reader.onload = (event) => {
      setImagePreview(event.target?.result as string)
      setUploadingImage(false)
    }
    
    reader.onerror = () => {
      setUploadingImage(false)
      alert('图片上传失败，请重试')
    }
    
    reader.readAsDataURL(file)
  }, [])

  // 取消图片预览
  const cancelImagePreview = useCallback(() => {
    setImagePreview(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }, [])

  // 取消音频预览
  const cancelAudioPreview = useCallback(() => {
    setAudioPreview(null)
  }, [])

  // 触发文件选择
  const triggerFileSelect = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  return {
    // 图片相关
    imagePreview,
    uploadingImage,
    fileInputRef,
    handleImageUpload,
    cancelImagePreview,
    triggerFileSelect,
    
    // 音频相关
    audioPreview,
    setAudioPreview,
    cancelAudioPreview
  }
} 