'use client';

import { useCallback, useState } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';

import AppLayout from '@/components/layout/AppLayout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useAuthContext } from '@/contexts/AuthContext';
import { usePermission } from '@/hooks/usePermission';
import { handleApiError } from '@/service/apiClient';
import { channelIdentityService, type ChannelIdentity } from '@/service/channelIdentityService';

const CHANNEL_TYPES = [
  { value: 'wechat_work_kf', label: '企业微信-客服' },
  { value: 'wechat_work', label: '企业微信-应用消息' },
];

export default function ChannelIdentitiesAdminPage() {
  const { user } = useAuthContext();
  const { isAdmin } = usePermission();
  const router = useRouter();

  const [channelType, setChannelType] = useState<string>('wechat_work_kf');
  const [peerId, setPeerId] = useState('');

  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupResult, setLookupResult] = useState<ChannelIdentity | null>(null);

  const [customerUserIdForList, setCustomerUserIdForList] = useState('');
  const [listLoading, setListLoading] = useState(false);
  const [listResult, setListResult] = useState<ChannelIdentity[]>([]);

  const [bindTargetCustomerUserId, setBindTargetCustomerUserId] = useState('');
  const [bindPeerName, setBindPeerName] = useState('');
  const [bindExtraDataJson, setBindExtraDataJson] = useState('');
  const [bindLoading, setBindLoading] = useState(false);

  const [mergeSourceCustomerUserId, setMergeSourceCustomerUserId] = useState('');
  const [mergeTargetCustomerUserId, setMergeTargetCustomerUserId] = useState('');
  const [mergeLoading, setMergeLoading] = useState(false);

  // 复用现有 admin 鉴权风格（非 admin 直接跳 unauthorized）
  if (user && !isAdmin) {
    router.push('/unauthorized');
  }

  const handleLookup = useCallback(async () => {
    if (!peerId.trim()) {
      toast.error('peer_id 不能为空');
      return;
    }
    setLookupLoading(true);
    try {
      const r = await channelIdentityService.lookup(channelType, peerId.trim());
      setLookupResult(r);
      toast.success(r ? '查询成功' : '未找到映射');
    } catch (err) {
      handleApiError(err, '查询失败');
    } finally {
      setLookupLoading(false);
    }
  }, [channelType, peerId]);

  const handleListByCustomer = useCallback(async () => {
    if (!customerUserIdForList.trim()) {
      toast.error('customer_user_id 不能为空');
      return;
    }
    setListLoading(true);
    try {
      const items = await channelIdentityService.listByCustomer(customerUserIdForList.trim());
      setListResult(items);
      toast.success(`加载完成：${items.length} 条`);
    } catch (err) {
      handleApiError(err, '查询失败');
    } finally {
      setListLoading(false);
    }
  }, [customerUserIdForList]);

  const handleBind = useCallback(async () => {
    if (!peerId.trim()) {
      toast.error('peer_id 不能为空');
      return;
    }
    if (!bindTargetCustomerUserId.trim()) {
      toast.error('customer_user_id 不能为空');
      return;
    }

    let extra: Record<string, unknown> | undefined;
    const raw = bindExtraDataJson.trim();
    if (raw) {
      try {
        extra = JSON.parse(raw) as Record<string, unknown>;
      } catch {
        toast.error('extra_data 不是合法 JSON');
        return;
      }
    }

    setBindLoading(true);
    try {
      const identity = await channelIdentityService.bind({
        channel_type: channelType,
        peer_id: peerId.trim(),
        customer_user_id: bindTargetCustomerUserId.trim(),
        peer_name: bindPeerName.trim() || undefined,
        extra_data: extra,
        migrate_conversations: true,
      });
      setLookupResult(identity);
      toast.success('绑定成功');
    } catch (err) {
      handleApiError(err, '绑定失败');
    } finally {
      setBindLoading(false);
    }
  }, [bindExtraDataJson, bindPeerName, bindTargetCustomerUserId, channelType, peerId]);

  const handleMergeCustomers = useCallback(async () => {
    if (!mergeSourceCustomerUserId.trim() || !mergeTargetCustomerUserId.trim()) {
      toast.error('source/target customer_user_id 不能为空');
      return;
    }
    if (mergeSourceCustomerUserId.trim() === mergeTargetCustomerUserId.trim()) {
      toast.error('source 与 target 不能相同');
      return;
    }
    setMergeLoading(true);
    try {
      const r = await channelIdentityService.mergeCustomers({
        source_customer_user_id: mergeSourceCustomerUserId.trim(),
        target_customer_user_id: mergeTargetCustomerUserId.trim(),
        migrate_conversations: true,
      });
      toast.success(`合并完成：迁移 ${r.moved_identities} 条`);
    } catch (err) {
      handleApiError(err, '合并失败');
    } finally {
      setMergeLoading(false);
    }
  }, [mergeSourceCustomerUserId, mergeTargetCustomerUserId]);

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="am-page">
        <div className="am-container">
          <div className="mb-6 flex items-center justify-between">
            <h1 className="am-page-title">渠道身份映射</h1>
          </div>

          <div className="am-filter-bar space-y-4">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label>渠道类型</Label>
                <Select value={channelType} onValueChange={setChannelType}>
                  <SelectTrigger className="am-field">
                    <SelectValue placeholder="选择渠道类型" />
                  </SelectTrigger>
                  <SelectContent>
                    {CHANNEL_TYPES.map((x) => (
                      <SelectItem key={x.value} value={x.value}>
                        {x.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>peer_id</Label>
                <Input className="am-field" value={peerId} onChange={(e) => setPeerId(e.target.value)} placeholder="外部用户标识" />
              </div>
              <div className="flex items-end gap-2">
                <Button className="am-btn-primary" onClick={handleLookup} disabled={lookupLoading}>
                  {lookupLoading ? '查询中...' : '按 peer 查询'}
                </Button>
                <Button
                  className="am-btn-reset"
                  onClick={() => {
                    setLookupResult(null);
                    setListResult([]);
                    toast.success('已清空结果');
                  }}
                >
                  清空结果
                </Button>
              </div>
            </div>

            {lookupResult ? (
              <div className="am-card p-4">
                <div className="grid grid-cols-1 gap-2 text-sm md:grid-cols-2">
                  <div className="text-gray-500">映射 ID</div>
                  <div className="am-mono">{lookupResult.id}</div>
                  <div className="text-gray-500">customer_user_id</div>
                  <div className="am-mono">{lookupResult.user_id}</div>
                  <div className="text-gray-500">peer_name</div>
                  <div>{lookupResult.peer_name || '-'}</div>
                  <div className="text-gray-500">last_seen_at</div>
                  <div className="am-mono">{lookupResult.last_seen_at}</div>
                </div>
              </div>
            ) : (
              <div className="text-sm text-gray-500">暂无查询结果</div>
            )}
          </div>

          <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
            <div className="am-card p-4 space-y-3">
              <div className="text-sm font-medium text-gray-900">绑定 / 迁移到已有 customer</div>
              <div className="space-y-2">
                <Label>目标 customer_user_id</Label>
                <Input
                  className="am-field"
                  value={bindTargetCustomerUserId}
                  onChange={(e) => setBindTargetCustomerUserId(e.target.value)}
                  placeholder="users.id"
                />
              </div>
              <div className="space-y-2">
                <Label>peer_name（可选）</Label>
                <Input className="am-field" value={bindPeerName} onChange={(e) => setBindPeerName(e.target.value)} placeholder="展示名" />
              </div>
              <div className="space-y-2">
                <Label>extra_data（可选 JSON）</Label>
                <Textarea
                  className="am-field"
                  value={bindExtraDataJson}
                  onChange={(e) => setBindExtraDataJson(e.target.value)}
                  rows={4}
                  placeholder='例如：{"union_id":"xxx","phone":"138..."}'
                />
              </div>
              <Button className="am-btn-primary w-full" onClick={handleBind} disabled={bindLoading}>
                {bindLoading ? '绑定中...' : '绑定/迁移'}
              </Button>
              <div className="text-xs text-gray-500">
                默认会同步修正历史渠道会话 owner 与 extra_metadata.channel.customer_user_id。
              </div>
            </div>

            <div className="am-card p-4 space-y-3">
              <div className="text-sm font-medium text-gray-900">按 customer 查询绑定的渠道身份</div>
              <div className="space-y-2">
                <Label>customer_user_id</Label>
                <Input
                  className="am-field"
                  value={customerUserIdForList}
                  onChange={(e) => setCustomerUserIdForList(e.target.value)}
                  placeholder="users.id"
                />
              </div>
              <Button className="am-btn-outline w-full" onClick={handleListByCustomer} disabled={listLoading}>
                {listLoading ? '加载中...' : '查询列表'}
              </Button>

              <div className="space-y-2">
                {listResult.length === 0 ? (
                  <div className="text-sm text-gray-500">暂无绑定记录</div>
                ) : (
                  <div className="space-y-2">
                    {listResult.map((x) => (
                      <div key={x.id} className="rounded-md border border-gray-200 bg-white p-3">
                        <div className="flex items-center justify-between">
                          <div className="text-sm font-medium text-gray-900">
                            {x.channel_type} / {x.peer_id}
                          </div>
                          <div className="text-xs text-gray-500">{x.peer_name || '-'}</div>
                        </div>
                        <div className="mt-1 text-xs text-gray-500">
                          customer: <span className="am-mono">{x.user_id}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="mt-6 am-card p-4 space-y-3">
            <div className="text-sm font-medium text-gray-900">合并两个 customer 的渠道身份</div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label>source_customer_user_id</Label>
                <Input className="am-field" value={mergeSourceCustomerUserId} onChange={(e) => setMergeSourceCustomerUserId(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>target_customer_user_id</Label>
                <Input className="am-field" value={mergeTargetCustomerUserId} onChange={(e) => setMergeTargetCustomerUserId(e.target.value)} />
              </div>
              <div className="flex items-end">
                <Button className="am-btn-primary w-full" onClick={handleMergeCustomers} disabled={mergeLoading}>
                  {mergeLoading ? '合并中...' : '合并'}
                </Button>
              </div>
            </div>
            <div className="text-xs text-gray-500">合并会迁移 source 的所有 ChannelIdentity 到 target，并同步修正相关渠道会话 owner。</div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

