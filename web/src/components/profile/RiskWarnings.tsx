'use client';

interface RiskNote {
  type: string;
  description: string;
  level: 'low' | 'medium' | 'high';
}

interface RiskWarningsProps {
  riskNotes?: RiskNote[];
}

export function RiskWarnings({ riskNotes }: RiskWarningsProps) {
  if (!riskNotes || riskNotes.length === 0) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-800">风险提示</h3>
        <div className="flex flex-col items-center justify-center py-12 text-gray-500">
          <svg className="h-12 w-12 text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p>未发现风险</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-800">风险提示</h3>
      
      {/* 风险等级说明 */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h4 className="mb-3 text-sm font-medium text-gray-700">风险等级说明</h4>
        <div className="space-y-2 text-sm">
          <div className="flex items-center">
            <span className="inline-block h-3 w-3 rounded-full bg-red-500 mr-2"></span>
            <span className="text-gray-700">高风险 - 需特别关注，可能对治疗造成重大影响</span>
          </div>
          <div className="flex items-center">
            <span className="inline-block h-3 w-3 rounded-full bg-orange-500 mr-2"></span>
            <span className="text-gray-700">中风险 - 需要注意并评估对治疗的影响</span>
          </div>
          <div className="flex items-center">
            <span className="inline-block h-3 w-3 rounded-full bg-yellow-500 mr-2"></span>
            <span className="text-gray-700">低风险 - 需要记录但对治疗影响较小</span>
          </div>
        </div>
      </div>
      
      {/* 风险列表 */}
      <div className="space-y-3">
        {riskNotes.map((risk, index) => (
          <div 
            key={index}
            className={`rounded-lg p-4 ${
              risk.level === 'high' 
                ? 'bg-red-50 border border-red-200' 
                : risk.level === 'medium'
                ? 'bg-orange-50 border border-orange-200'
                : 'bg-yellow-50 border border-yellow-200'
            }`}
          >
            <div className="flex items-center mb-2">
              <span className={`inline-block h-3 w-3 rounded-full mr-2 ${
                risk.level === 'high' ? 'bg-red-500' : 
                risk.level === 'medium' ? 'bg-orange-500' : 'bg-yellow-500'
              }`}></span>
              <span className={`font-medium ${
                risk.level === 'high' ? 'text-red-700' : 
                risk.level === 'medium' ? 'text-orange-700' : 'text-yellow-700'
              }`}>{risk.type}</span>
            </div>
            <p className={`text-sm ${
              risk.level === 'high' ? 'text-red-600' : 
              risk.level === 'medium' ? 'text-orange-600' : 'text-yellow-600'
            }`}>{risk.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
} 