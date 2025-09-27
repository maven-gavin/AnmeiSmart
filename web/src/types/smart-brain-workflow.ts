
export type AgentLogResponse = {
    task_id: string
    event: string
    data: AgentLogItemWithChildren
  }

  export type AgentLogItemWithChildren = AgentLogItem & {
    hasCircle?: boolean
    children: AgentLogItemWithChildren[]
  }

  export type AgentLogItem = {
    node_execution_id: string,
    id: string,
    node_id: string,
    parent_id?: string,
    label: string,
    data: object, // debug data
    error?: string,
    status: string,
    metadata?: {
      elapsed_time?: number
      provider?: string
      icon?: string
    },
  }
  
  export type IterationFinishedResponse = {
    task_id: string
    workflow_run_id: string
    event: string
    data: NodeTracing
  }
 

export enum BlockEnum {
    Start = 'start',
    End = 'end',
    Answer = 'answer',
    LLM = 'llm',
    KnowledgeRetrieval = 'knowledge-retrieval',
    QuestionClassifier = 'question-classifier',
    IfElse = 'if-else',
    Code = 'code',
    TemplateTransform = 'template-transform',
    HttpRequest = 'http-request',
    VariableAssigner = 'variable-assigner',
    VariableAggregator = 'variable-aggregator',
    Tool = 'tool',
    ParameterExtractor = 'parameter-extractor',
    Iteration = 'iteration',
    DocExtractor = 'document-extractor',
    ListFilter = 'list-operator',
    IterationStart = 'iteration-start',
    Assigner = 'assigner', // is now named as VariableAssigner
    Agent = 'agent',
    Loop = 'loop',
    LoopStart = 'loop-start',
    LoopEnd = 'loop-end',
  }
  
  
export type NodeTracing = {
    id: string
    index: number
    predecessor_node_id: string
    node_id: string
    iteration_id?: string
    loop_id?: string
    node_type: BlockEnum
    title: string
    inputs: any
    process_data: any
    outputs?: Record<string, any>
    status: string
    parallel_run_id?: string
    error?: string
    elapsed_time: number
    execution_metadata?: {
      total_tokens: number
      total_price: number
      currency: string
      iteration_id?: string
      iteration_index?: number
      loop_id?: string
      loop_index?: number
      parallel_id?: string
      parallel_start_node_id?: string
      parent_parallel_id?: string
      parent_parallel_start_node_id?: string
      parallel_mode_run_id?: string
      iteration_duration_map?: IterationDurationMap
      loop_duration_map?: LoopDurationMap
      error_strategy?: ErrorHandleTypeEnum
      agent_log?: AgentLogItem[]
      tool_info?: {
        agent_strategy?: string
        icon?: string
      }
      loop_variable_map?: Record<string, any>
    }
    metadata: {
      iterator_length: number
      iterator_index: number
      loop_length: number
      loop_index: number
    }
    created_at: number
    created_by: {
      id: string
      name: string
      email: string
    }
    iterDurationMap?: IterationDurationMap
    loopDurationMap?: LoopDurationMap
    finished_at: number
    extras?: any
    expand?: boolean // for UI
    details?: NodeTracing[][] // iteration or loop detail
    retryDetail?: NodeTracing[] // retry detail
    retry_index?: number
    parallelDetail?: { // parallel detail. if is in parallel, this field will be set
      isParallelStartNode?: boolean
      parallelTitle?: string
      branchTitle?: string
      children?: NodeTracing[]
    }
    parallel_id?: string
    parallel_start_node_id?: string
    parent_parallel_id?: string
    parent_parallel_start_node_id?: string
    agentLog?: AgentLogItemWithChildren[] // agent log
  }
  export type IterationDurationMap = Record<string, number>
  export type LoopDurationMap = Record<string, number>
  export enum ErrorHandleTypeEnum {
    none = 'none',
    failBranch = 'fail-branch',
    defaultValue = 'default-value',
  }
  
  export type IterationNextResponse = {
    task_id: string
    workflow_run_id: string
    event: string
    data: NodeTracing
  }

  export type IterationStartedResponse = {
    task_id: string
    workflow_run_id: string
    event: string
    data: NodeTracing
  }
  
  export type LoopFinishedResponse = {
    task_id: string
    workflow_run_id: string
    event: string
    data: NodeTracing
  }

  export type LoopNextResponse = {
    task_id: string
    workflow_run_id: string
    event: string
    data: NodeTracing
  }
  
  export type LoopStartedResponse = {
    task_id: string
    workflow_run_id: string
    event: string
    data: NodeTracing
  }
  
  export type NodeFinishedResponse = {
    task_id: string
    workflow_run_id: string
    event: string
    data: NodeTracing
  }

  export type NodeStartedResponse = {
    task_id: string
    workflow_run_id: string
    event: string
    data: NodeTracing
  }
  export type ParallelBranchFinishedResponse = {
    task_id: string
    workflow_run_id: string
    event: string
    data: NodeTracing
  }
  export type ParallelBranchStartedResponse = {
    task_id: string
    workflow_run_id: string
    event: string
    data: NodeTracing
  }
  export type TextChunkResponse = {
    task_id: string
    workflow_run_id: string
    event: string
    data: {
      text: string
    }
  }
  export type TextReplaceResponse = {
    task_id: string
    workflow_run_id: string
    event: string
    data: {
      text: string
    }
  }
  export type WorkflowFinishedResponse = {
    task_id: string
    workflow_run_id: string
    event: string
    data: {
      id: string
      workflow_id: string
      status: string
      outputs: any
      error: string
      elapsed_time: number
      total_tokens: number
      total_steps: number
      created_at: number
      created_by: {
        id: string
        name: string
        email: string
      }
      finished_at: number
      files?: FileResponse[]
    }
  }
  export type FileResponse = {
    related_id: string
    extension: string
    filename: string
    size: number
    mime_type: string
    transfer_method: TransferMethod
    type: string
    url: string
    upload_file_id: string
    remote_url: string
  }
  export enum TransferMethod {
    all = 'all',
    local_file = 'local_file',
    remote_url = 'remote_url',
  }
  export type WorkflowStartedResponse = {
    task_id: string
    workflow_run_id: string
    event: string
    data: {
      id: string
      workflow_id: string
      created_at: number
    }
  }
            
  