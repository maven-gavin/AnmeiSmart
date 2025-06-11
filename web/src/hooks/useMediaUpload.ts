import { useState, useRef, useCallback } from 'react'
import { type FileInfo } from '@/types/chat'

export function useMediaUpload() {
  // 图片上传状态
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [uploadingImage, setUploadingImage] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 语音相关状态
  const [audioPreview, setAudioPreview] = useState<string | null>(null)

  // 文件预览状态
  const [filePreview, setFilePreview] = useState<FileInfo | null>(null)
  const fileInputForFileRef = useRef<HTMLInputElement>(null)
  // 存储原始文件对象的Map
  const [tempFileMap, setTempFileMap] = useState<Map<string, File>>(new Map())

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

  // 处理文件上传 - 只是选择和预览，不上传到服务器
  const handleFileUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // 生成临时ID
    const tempId = `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    // 创建文件预览信息
    const fileInfo: FileInfo = {
      file_url: tempId, // 使用临时ID作为标识
      file_name: file.name,
      file_size: file.size,
      file_type: getFileTypeFromFile(file),
      mime_type: file.type,
      object_name: undefined
    }

    // 存储原始文件对象
    setTempFileMap(prev => {
      const newMap = new Map(prev)
      newMap.set(tempId, file)
      return newMap
    })

    setFilePreview(fileInfo)
  }, [])

  // 获取临时文件对象
  const getTempFile = useCallback((tempId: string): File | undefined => {
    return tempFileMap.get(tempId)
  }, [tempFileMap])

  // 从文件推断文件类型
  const getFileTypeFromFile = useCallback((file: File): string => {
    const { type, name } = file
    
    if (type.startsWith('image/')) return 'image'
    if (type.startsWith('video/')) return 'video'
    if (type.startsWith('audio/')) return 'audio'
    if (type.includes('pdf') || type.includes('document') || type.includes('text')) return 'document'
    if (type.includes('zip') || type.includes('compressed')) return 'archive'
    
    // 根据文件扩展名进一步判断
    const extension = name.split('.').pop()?.toLowerCase()
    if (!extension) return 'document'
    
    const documentExts = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv']
    const archiveExts = ['zip', 'rar', '7z', 'tar', 'gz']
    
    if (documentExts.includes(extension)) return 'document'
    if (archiveExts.includes(extension)) return 'archive'
    
    return 'document' // 默认为文档类型
  }, [])

  // 取消图片预览
  const cancelImagePreview = useCallback(() => {
    setImagePreview(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }, [])

  // 取消文件预览
  const cancelFilePreview = useCallback(() => {
    if (filePreview) {
      // 清理临时文件存储
      setTempFileMap(prev => {
        const newMap = new Map(prev)
        newMap.delete(filePreview.file_url)
        return newMap
      })
    }
    setFilePreview(null)
    if (fileInputForFileRef.current) {
      fileInputForFileRef.current.value = ''
    }
  }, [filePreview])

  // 取消音频预览
  const cancelAudioPreview = useCallback(() => {
    setAudioPreview(null)
  }, [])

  // 触发图片文件选择
  const triggerFileSelect = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  // 触发普通文件选择
  const triggerFileUpload = useCallback(() => {
    fileInputForFileRef.current?.click()
  }, [])

  return {
    // 图片相关
    imagePreview,
    uploadingImage,
    fileInputRef,
    handleImageUpload,
    cancelImagePreview,
    triggerFileSelect,
    
    // 文件相关
    filePreview,
    fileInputForFileRef,
    handleFileUpload,
    cancelFilePreview,
    triggerFileUpload,
    getTempFile,
    
    // 音频相关
    audioPreview,
    setAudioPreview,
    cancelAudioPreview
  }
} 