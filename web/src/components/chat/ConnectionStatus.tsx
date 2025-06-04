import { ConnectionStatus } from '@/service/websocket'

interface ConnectionStatusProps {
  wsStatus: ConnectionStatus
  onReconnect: () => void
}

export function ConnectionStatusIndicator({ wsStatus, onReconnect }: ConnectionStatusProps) {
  if (wsStatus === ConnectionStatus.CONNECTED) {
    return null
  }

  const statusConfig = {
    [ConnectionStatus.CONNECTING]: {
      bgColor: 'bg-yellow-50',
      textColor: 'text-yellow-700',
      message: '正在连接服务器...',
      showSpinner: true,
      showReconnect: false
    },
    [ConnectionStatus.ERROR]: {
      bgColor: 'bg-red-50',
      textColor: 'text-red-700',
      message: '连接服务器失败',
      showSpinner: false,
      showReconnect: true
    },
    [ConnectionStatus.DISCONNECTED]: {
      bgColor: 'bg-gray-50',
      textColor: 'text-gray-700',
      message: '未连接到服务器',
      showSpinner: false,
      showReconnect: true
    }
  }

  const config = statusConfig[wsStatus] || statusConfig[ConnectionStatus.DISCONNECTED]

  return (
    <div className={`px-4 py-2 text-sm text-center ${config.bgColor} ${config.textColor}`}>
      {config.showSpinner ? (
        <span className="flex items-center justify-center">
          <svg 
            className="animate-spin -ml-1 mr-2 h-4 w-4" 
            xmlns="http://www.w3.org/2000/svg" 
            fill="none" 
            viewBox="0 0 24 24"
          >
            <circle 
              className="opacity-25" 
              cx="12" 
              cy="12" 
              r="10" 
              stroke="currentColor" 
              strokeWidth="4"
            />
            <path 
              className="opacity-75" 
              fill="currentColor" 
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          {config.message}
        </span>
      ) : (
        <div className="flex items-center justify-center">
          <span>{config.message}</span>
          {config.showReconnect && (
            <button 
              onClick={onReconnect}
              className={`ml-2 text-sm hover:underline ${
                wsStatus === ConnectionStatus.ERROR ? 'text-red-600 hover:text-red-800' : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              重新连接
            </button>
          )}
        </div>
      )}
    </div>
  )
} 