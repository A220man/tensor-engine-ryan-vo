import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  PolicyRule,
  PolicyRuleCreate,
  PolicyRuleUpdate,
  Sandbox,
  SandboxCreate,
  SandboxUpdate,
  Execution,
  ExecutionCreate,
  AuditLog,
  PaginatedResponse,
  HealthResponse,
} from '@/types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Handle unauthorized - could redirect to login
      console.error('Unauthorized access');
    }
    return Promise.reject(error);
  }
);

export const healthApi = {
  getHealth: () => api.get<HealthResponse>('/health'),
};

export const policyApi = {
  list: (enabledOnly = false, page = 1, pageSize = 20) =>
    api.get<PaginatedResponse<PolicyRule>>('/policies', {
      params: { enabled_only: enabledOnly, page, page_size: pageSize },
    }),
  get: (id: number) => api.get<PolicyRule>(`/policies/${id}`),
  create: (data: PolicyRuleCreate) => api.post<PolicyRule>('/policies', data),
  update: (id: number, data: PolicyRuleUpdate) => api.patch<PolicyRule>(`/policies/${id}`, data),
  delete: (id: number) => api.delete(`/policies/${id}`),
};

export const sandboxApi = {
  list: (status?: string, page = 1, pageSize = 20) =>
    api.get<PaginatedResponse<Sandbox>>('/sandboxes', {
      params: { status, page, page_size: pageSize },
    }),
  get: (id: string) => api.get<Sandbox>(`/sandboxes/${id}`),
  create: (data: SandboxCreate) => api.post<Sandbox>('/sandboxes', data),
  update: (id: string, data: SandboxUpdate) => api.patch<Sandbox>(`/sandboxes/${id}`, data),
  start: (id: string) => api.post<Sandbox>(`/sandboxes/${id}/start`),
  stop: (id: string) => api.post<Sandbox>(`/sandboxes/${id}/stop`),
  terminate: (id: string) => api.post<Sandbox>(`/sandboxes/${id}/terminate`),
  execute: (id: string, data: ExecutionCreate, traceId?: string, spanId?: string) =>
    api.post<Execution>(`/sandboxes/${id}/execute`, data, {
      params: { trace_id: traceId, span_id: spanId },
    }),
  getExecutions: (id: string, page = 1, pageSize = 20) =>
    api.get<PaginatedResponse<Execution>>(`/sandboxes/${id}/executions`, {
      params: { page, page_size: pageSize },
    }),
};

export const auditApi = {
  list: (eventType?: string, sandboxId?: string, page = 1, pageSize = 20) =>
    api.get<PaginatedResponse<AuditLog>>('/audit', {
      params: { event_type: eventType, sandbox_id: sandboxId, page, page_size: pageSize },
    }),
};

export default api;