export interface PolicyRule {
  id: number;
  name: string;
  description: string | null;
  action: 'allow' | 'deny';
  destination_host: string | null;
  destination_port: number | null;
  protocol: string | null;
  command_pattern: string | null;
  priority: number;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface PolicyRuleCreate {
  name: string;
  description?: string;
  action: 'allow' | 'deny';
  destination_host?: string;
  destination_port?: number;
  protocol?: string;
  command_pattern?: string;
  priority?: number;
  enabled?: boolean;
}

export interface PolicyRuleUpdate {
  description?: string;
  action?: 'allow' | 'deny';
  destination_host?: string;
  destination_port?: number;
  protocol?: string;
  command_pattern?: string;
  priority?: number;
  enabled?: boolean;
}

export interface Sandbox {
  id: number;
  name: string;
  sandbox_id: string;
  status: 'creating' | 'running' | 'stopped' | 'error' | 'terminated';
  policy_id: number | null;
  config: string | null;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  stopped_at: string | null;
  policy: PolicyRule | null;
}

export interface SandboxCreate {
  name: string;
  policy_id?: number;
  config?: string;
}

export interface SandboxUpdate {
  name?: string;
  policy_id?: number;
  config?: string;
}

export interface Execution {
  id: number;
  sandbox_id: number;
  command: string;
  args: string | null;
  stdout: string | null;
  stderr: string | null;
  exit_code: number | null;
  started_at: string;
  completed_at: string | null;
  trace_id: string | null;
  span_id: string | null;
}

export interface ExecutionCreate {
  command: string;
  args?: string[];
}

export interface AuditLog {
  id: number;
  event_type: string;
  sandbox_id: string | null;
  policy_id: number | null;
  decision: string | null;
  details: string | null;
  trace_id: string | null;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  database: string;
  telemetry: string;
}