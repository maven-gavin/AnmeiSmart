export const DATASET_LABELS: Record<string, string> = {
  trading_calendar: '交易日历',
  security_master: '证券主数据',
  market_daily: '日线行情',
  money_flow: '资金流向',
  sector_members: '板块成分',
  financial_summary: '财务摘要',
}

export function getDatasetLabelZh(key: string, labelZh?: string | null): string {
  return labelZh || DATASET_LABELS[key] || key
}

export function formatDatasetLabel(key: string, labelZh?: string | null): string {
  const zh = getDatasetLabelZh(key, labelZh)
  if (zh === key) return key
  return `${zh} (${key})`
}
