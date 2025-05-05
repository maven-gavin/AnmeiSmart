import { type User } from '@/types/chat'

// 模拟数据，实际应从API获取
const currentUser: User = {
  id: '1',
  name: '张医生',
  avatar: '/avatars/default.png',
  tags: ['皮肤科', '整形外科']
}

export default function UserInfoBar() {
  return (
    <div className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-4">
      <div className="flex items-center space-x-3">
        <img
          src={currentUser.avatar}
          alt={currentUser.name}
          className="h-10 w-10 rounded-full"
        />
        <div>
          <h3 className="font-medium">{currentUser.name}</h3>
          <div className="flex space-x-2">
            {currentUser.tags.map(tag => (
              <span
                key={tag}
                className="rounded-full bg-orange-100 px-2 py-0.5 text-xs text-orange-700"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
} 