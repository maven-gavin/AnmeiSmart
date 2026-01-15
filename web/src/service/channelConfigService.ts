import { apiClient } from '@/service/apiClient';

export interface ChannelConfig {
  id: string;
  channel_type: string;
  name: string;
  config: Record<string, unknown>;
  is_active: boolean;
}

export interface ChannelConfigUpdate {
  name?: string;
  config?: Record<string, unknown>;
  is_active?: boolean;
}

export const channelConfigService = {
  async getConfig(channelType: string): Promise<ChannelConfig> {
    const resp = await apiClient.get<ChannelConfig>(`/channels/configs/${channelType}`);
    return resp.data;
  },

  async updateConfig(channelType: string, payload: ChannelConfigUpdate): Promise<ChannelConfig> {
    const resp = await apiClient.put<ChannelConfig>(`/channels/configs/${channelType}`, payload);
    return resp.data;
  },
};

