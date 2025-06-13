'use client';

interface ProfileTabsProps {
  activeTab: 'basic' | 'history' | 'risk';
  onTabChange: (tab: 'basic' | 'history' | 'risk') => void;
  consultationCount: number;
  riskCount: number;
}

export function ProfileTabs({ activeTab, onTabChange, consultationCount, riskCount }: ProfileTabsProps) {
  const tabs = [
    {
      id: 'basic' as const,
      label: '基本信息',
      count: 0
    },
    {
      id: 'history' as const,
      label: '咨询历史',
      count: consultationCount
    },
    {
      id: 'risk' as const,
      label: '风险提示',
      count: riskCount
    }
  ];

  return (
    <div className="flex border-b border-gray-200 sticky top-0 bg-white">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`px-4 py-2 text-sm font-medium ${
            activeTab === tab.id
              ? 'text-orange-500 border-b-2 border-orange-500'
              : 'text-gray-500 hover:text-gray-700'
          }`}
          onClick={() => onTabChange(tab.id)}
        >
          {tab.label}
          {tab.count > 0 && (
            <span className={`ml-1 rounded-full px-2 py-0.5 text-xs ${
              tab.id === 'risk'
                ? 'bg-red-100 text-red-600'
                : 'bg-orange-100 text-orange-600'
            }`}>
              {tab.count}
            </span>
          )}
        </button>
      ))}
    </div>
  );
} 