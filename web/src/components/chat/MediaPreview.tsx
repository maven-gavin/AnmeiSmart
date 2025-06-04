interface MediaPreviewProps {
  imagePreview?: string | null
  audioPreview?: string | null
  onCancelImage?: () => void
  onCancelAudio?: () => void
}

export function MediaPreview({ 
  imagePreview, 
  audioPreview, 
  onCancelImage, 
  onCancelAudio 
}: MediaPreviewProps) {
  if (!imagePreview && !audioPreview) {
    return null
  }

  return (
    <>
      {/* 图片预览 */}
      {imagePreview && (
        <div className="border-t border-gray-200 bg-gray-50 p-3">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">图片预览</span>
            {onCancelImage && (
              <button 
                onClick={onCancelImage}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
          <div className="relative">
            <img 
              src={imagePreview} 
              alt="预览图片" 
              className="max-h-40 max-w-full rounded-lg object-contain"
            />
          </div>
        </div>
      )}

      {/* 音频预览 */}
      {audioPreview && (
        <div className="border-t border-gray-200 bg-gray-50 p-3">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">语音预览</span>
            {onCancelAudio && (
              <button 
                onClick={onCancelAudio}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
          <audio src={audioPreview} controls className="w-full" />
        </div>
      )}
    </>
  )
} 