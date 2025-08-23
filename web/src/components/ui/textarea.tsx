import * as React from "react"
import { cn } from "@/service/utils"

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  autoResize?: boolean
  maxRows?: number
  minRows?: number
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, autoResize = false, maxRows = 6, minRows = 1, ...props }, ref) => {
    const textareaRef = React.useRef<HTMLTextAreaElement>(null)
    
    // 合并refs
    React.useImperativeHandle(ref, () => textareaRef.current!)

    const adjustHeight = React.useCallback(() => {
      const textarea = textareaRef.current
      if (!textarea || !autoResize) return

      // 重置高度以获取正确的scrollHeight
      textarea.style.height = 'auto'
      
      // 计算行高
      const computedStyle = window.getComputedStyle(textarea)
      const lineHeight = parseInt(computedStyle.lineHeight) || 20
      
      // 计算最小和最大高度
      const minHeight = lineHeight * minRows
      const maxHeight = lineHeight * maxRows
      
      // 设置新高度
      const newHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight)
      textarea.style.height = `${newHeight}px`
    }, [autoResize, maxRows, minRows])

    React.useEffect(() => {
      adjustHeight()
    }, [props.value, adjustHeight])

    const handleInput = (e: React.FormEvent<HTMLTextAreaElement>) => {
      adjustHeight()
      props.onInput?.(e)
    }

    return (
      <textarea
        className={cn(
          "flex min-h-[40px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 resize-none",
          className
        )}
        ref={textareaRef}
        onInput={handleInput}
        {...props}
      />
    )
  }
)
Textarea.displayName = "Textarea"

export { Textarea }