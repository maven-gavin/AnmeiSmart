'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';

import AppLayout from '@/components/layout/AppLayout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { useAuthContext } from '@/contexts/AuthContext';
import { usePermission } from '@/hooks/usePermission';
import { handleApiError } from '@/service/apiClient';
import { channelConfigService } from '@/service/channelConfigService';

const ARCHIVE_CHANNEL_TYPE = 'wechat_work_archive';
const CONTACT_CHANNEL_TYPE = 'wechat_work_contact';

export default function ChannelConfigsPage() {
  const { user } = useAuthContext();
  const { isAdmin } = usePermission();
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [isActive, setIsActive] = useState(true);
  const [name, setName] = useState('企业微信会话内容存档');
  const [corpId, setCorpId] = useState('');
  const [secret, setSecret] = useState('');
  const [privateKey, setPrivateKey] = useState('');
  const [token, setToken] = useState('');
  const [encodingAesKey, setEncodingAesKey] = useState('');
  const [pollEnabled, setPollEnabled] = useState(false);
  const [pollIntervalSeconds, setPollIntervalSeconds] = useState(60);
  const [pollLimit, setPollLimit] = useState(100);

  const [contactCorpId, setContactCorpId] = useState('');
  const [contactSecret, setContactSecret] = useState('');
  const [contactIsActive, setContactIsActive] = useState(true);

  useEffect(() => {
    if (user && !isAdmin) {
      router.push('/unauthorized');
    }
  }, [user, isAdmin, router]);

  const loadConfig = useCallback(async () => {
    setLoading(true);
    try {
      try {
        const cfg = await channelConfigService.getConfig(ARCHIVE_CHANNEL_TYPE);
        setIsActive(cfg.is_active);
        setName(cfg.name || '企业微信会话内容存档');
        const config = cfg.config || {};
        setCorpId(String(config.corp_id || ''));
        setSecret(String(config.secret || ''));
        setPrivateKey(String(config.private_key || ''));
        setToken(String(config.token || ''));
        setEncodingAesKey(String(config.encoding_aes_key || ''));
        setPollEnabled(Boolean(config.poll_enabled));
        setPollIntervalSeconds(Number(config.poll_interval_seconds || 60));
        setPollLimit(Number(config.poll_limit || 100));
      } catch (err) {
        handleApiError(err, '加载会话存档配置失败');
      }

      try {
        const contactCfg = await channelConfigService.getConfig(CONTACT_CHANNEL_TYPE);
        setContactIsActive(contactCfg.is_active);
        const c = contactCfg.config || {};
        setContactCorpId(String(c.corp_id || ''));
        setContactSecret(String(c.secret || ''));
      } catch (err) {
        handleApiError(err, '加载客户联系配置失败');
      }
    } catch (err) {
      handleApiError(err, '加载配置失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  const handleSave = useCallback(async () => {
    try {
      await channelConfigService.updateConfig(ARCHIVE_CHANNEL_TYPE, {
        name,
        is_active: isActive,
        config: {
          corp_id: corpId.trim(),
          secret: secret.trim(),
          private_key: privateKey.trim(),
          token: token.trim(),
          encoding_aes_key: encodingAesKey.trim(),
          poll_enabled: pollEnabled,
          poll_interval_seconds: pollIntervalSeconds,
          poll_limit: pollLimit,
        },
      });
      toast.success('保存成功');
    } catch (err) {
      handleApiError(err, '保存失败');
    }
  }, [corpId, isActive, name, pollEnabled, pollIntervalSeconds, pollLimit, privateKey, secret, token, encodingAesKey]);

  const handleSaveContact = useCallback(async () => {
    try {
      await channelConfigService.updateConfig(CONTACT_CHANNEL_TYPE, {
        name: '企业微信客户联系',
        is_active: contactIsActive,
        config: {
          corp_id: contactCorpId.trim(),
          secret: contactSecret.trim(),
        },
      });
      toast.success('客户联系配置已保存');
    } catch (err) {
      handleApiError(err, '保存客户联系配置失败');
    }
  }, [contactCorpId, contactIsActive, contactSecret]);

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="am-page">
        <div className="am-container">
          <div className="mb-6 flex items-center justify-between">
            <h1 className="am-page-title">会话内容存档配置</h1>
          </div>

          <div className="am-card p-4 space-y-4">
            {loading ? (
              <div className="flex items-center justify-center py-10">
                <div className="am-spinner"></div>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>配置名称</Label>
                    <Input className="am-field" value={name} onChange={(e) => setName(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label>是否启用</Label>
                    <div className="flex items-center gap-3">
                      <Switch checked={isActive} onCheckedChange={setIsActive} />
                      <span className="text-sm text-gray-500">{isActive ? '启用' : '停用'}</span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Corp ID</Label>
                    <Input className="am-field" value={corpId} onChange={(e) => setCorpId(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label>会话存档 Secret</Label>
                    <Input className="am-field" value={secret} onChange={(e) => setSecret(e.target.value)} />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>存档私钥（PEM）</Label>
                  <Textarea
                    className="am-field"
                    value={privateKey}
                    onChange={(e) => setPrivateKey(e.target.value)}
                    rows={6}
                    placeholder="-----BEGIN PRIVATE KEY-----"
                  />
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>回调 Token</Label>
                    <Input className="am-field" value={token} onChange={(e) => setToken(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label>EncodingAESKey</Label>
                    <Input className="am-field" value={encodingAesKey} onChange={(e) => setEncodingAesKey(e.target.value)} />
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label>自动拉取</Label>
                    <div className="flex items-center gap-3">
                      <Switch checked={pollEnabled} onCheckedChange={setPollEnabled} />
                      <span className="text-sm text-gray-500">{pollEnabled ? '开启' : '关闭'}</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>拉取间隔（秒）</Label>
                    <Input
                      className="am-field"
                      type="number"
                      min={10}
                      value={pollIntervalSeconds}
                      onChange={(e) => setPollIntervalSeconds(Number(e.target.value) || 60)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>每次拉取数量</Label>
                    <Input
                      className="am-field"
                      type="number"
                      min={1}
                      max={1000}
                      value={pollLimit}
                      onChange={(e) => setPollLimit(Number(e.target.value) || 100)}
                    />
                  </div>
                </div>

                <div className="flex items-center justify-end gap-2">
                  <Button className="am-btn-reset" onClick={loadConfig}>
                    重新加载
                  </Button>
                  <Button className="am-btn-primary" onClick={handleSave}>
                    保存配置
                  </Button>
                </div>
              </>
            )}
          </div>

          <div className="mt-6 am-card p-4 space-y-4">
            <div className="text-sm font-medium text-gray-900">客户联系配置</div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label>Corp ID</Label>
                <Input className="am-field" value={contactCorpId} onChange={(e) => setContactCorpId(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>客户联系 Secret</Label>
                <Input className="am-field" value={contactSecret} onChange={(e) => setContactSecret(e.target.value)} />
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Switch checked={contactIsActive} onCheckedChange={setContactIsActive} />
              <span className="text-sm text-gray-500">{contactIsActive ? '启用' : '停用'}</span>
            </div>
            <div className="flex items-center justify-end">
              <Button className="am-btn-primary" onClick={handleSaveContact}>
                保存客户联系配置
              </Button>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

