export enum TransferMethod {
    all = 'all',
    local_file = 'local_file',
    remote_url = 'remote_url',
  }
  

export type VisionFile = {
    id?: string
    type: string
    transfer_method: TransferMethod
    url: string
    upload_file_id: string
    belongs_to?: string
  }
  