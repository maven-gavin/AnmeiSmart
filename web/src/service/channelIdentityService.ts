import { apiClient } from '@/service/apiClient';

export interface ChannelIdentity {
  id: string;
  channel_type: string;
  peer_id: string;
  user_id: string;
  peer_name?: string | null;
  extra_data?: Record<string, unknown> | null;
  first_seen_at: string;
  last_seen_at: string;
}

export interface ChannelIdentityBindRequest {
  channel_type: string;
  peer_id: string;
  customer_user_id: string;
  peer_name?: string;
  extra_data?: Record<string, unknown>;
  migrate_conversations?: boolean;
}

export interface ChannelCustomerMergeRequest {
  source_customer_user_id: string;
  target_customer_user_id: string;
  migrate_conversations?: boolean;
}

export const channelIdentityService = {
  async lookup(channelType: string, peerId: string): Promise<ChannelIdentity | null> {
    const resp = await apiClient.get<ChannelIdentity | null>('/channels/identities/lookup', {
      searchParams: { channel_type: channelType, peer_id: peerId },
    });
    return resp.data ?? null;
  },

  async listByCustomer(customerUserId: string): Promise<ChannelIdentity[]> {
    const resp = await apiClient.get<ChannelIdentity[]>(
      `/channels/identities/by-customer/${customerUserId}`
    );
    return resp.data ?? [];
  },

  async bind(payload: ChannelIdentityBindRequest): Promise<ChannelIdentity> {
    const resp = await apiClient.post<ChannelIdentity>('/channels/identities/bind', payload);
    return resp.data;
  },

  async mergeCustomers(payload: ChannelCustomerMergeRequest): Promise<{ moved_identities: number }> {
    const resp = await apiClient.post<{ moved_identities: number }>(
      '/channels/identities/merge-customers',
      payload
    );
    return resp.data;
  },
};

