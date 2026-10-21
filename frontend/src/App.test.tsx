import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from './App';

// Mock the API client
vi.mock('./api/client', () => ({
  sandboxApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    start: vi.fn(),
    stop: vi.fn(),
    terminate: vi.fn(),
    execute: vi.fn(),
    getExecutions: vi.fn(),
    update: vi.fn(),
  },
  policyApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
  auditApi: {
    list: vi.fn(),
  },
}));

import { sandboxApi, policyApi, auditApi } from './api/client';

const mockSandboxes = {
  items: [
    { id: 1, name: 'test-sandbox', sandbox_id: 'sb-abc123', status: 'running', policy_id: null, config: '{}', created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z', started_at: '2024-01-01T00:00:00Z', stopped_at: null, policy: null },
  ],
  total: 1,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

const mockPolicies = {
  items: [
    { id: 1, name: 'allow-api', description: 'Allow API egress', action: 'allow', destination_host: 'api.example.com', destination_port: 443, protocol: 'tcp', command_pattern: null, priority: 10, enabled: true, created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z' },
  ],
  total: 1,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

const mockAuditLogs = {
  items: [
    { id: 1, event_type: 'policy_evaluation', sandbox_id: 'sb-abc123', policy_id: 1, decision: 'allow', details: '{"destination": "api.example.com:443"}', trace_id: null, timestamp: '2024-01-01T00:00:00Z' },
  ],
  total: 1,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

const mockExecution = {
  id: 1,
  sandbox_id: 'sb-abc123',
  command: 'echo hello',
  exit_code: 0,
  stdout: 'hello\n',
  stderr: '',
  started_at: '2024-01-01T00:00:00Z',
  completed_at: '2024-01-01T00:00:01Z',
  trace_id: null,
  span_id: null,
};

const mockSandboxDetail = {
  id: 1,
  name: 'test-sandbox',
  sandbox_id: 'sb-abc123',
  status: 'running',
  policy_id: 1,
  config: '{"memory": "512m", "cpu": "0.5"}',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  started_at: '2024-01-01T00:00:00Z',
  stopped_at: null,
  policy: mockPolicies.items[0],
};

beforeEach(() => {
  vi.clearAllMocks();
  sandboxApi.list.mockResolvedValue({ data: mockSandboxes });
  sandboxApi.get.mockResolvedValue({ data: mockSandboxDetail });
  sandboxApi.getExecutions.mockResolvedValue({ data: { items: [mockExecution], total: 1, page: 1, page_size: 20, total_pages: 1 } });
  sandboxApi.execute.mockResolvedValue({ data: mockExecution });
  sandboxApi.start.mockResolvedValue({ data: mockSandboxDetail });
  sandboxApi.stop.mockResolvedValue({ data: { ...mockSandboxDetail, status: 'stopped' } });
  sandboxApi.terminate.mockResolvedValue({ data: { ...mockSandboxDetail, status: 'terminated' } });
  policyApi.list.mockResolvedValue({ data: mockPolicies });
  auditApi.list.mockResolvedValue({ data: mockAuditLogs });
});

describe('App', () => {
  it('renders header with OpenShell brand', () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );
    expect(screen.getByText('OpenShell')).toBeInTheDocument();
  });

  it('shows navigation links', () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );
    expect(screen.getByText('Sandboxes')).toBeInTheDocument();
    expect(screen.getByText('Policies')).toBeInTheDocument();
    expect(screen.getByText('Audit Logs')).toBeInTheDocument();
  });

  it('loads and displays sandboxes list', async () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );
    await waitFor(() => {
      expect(screen.getByText('test-sandbox')).toBeInTheDocument();
      expect(screen.getByText('sb-abc123')).toBeInTheDocument();
      expect(screen.getByText('running')).toBeInTheDocument();
    });
  });

  it('navigates to sandbox detail on click', async () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );
    await waitFor(() => {
      expect(screen.getByText('test-sandbox')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('test-sandbox'));
    await waitFor(() => {
      expect(screen.getByText('Sandbox Info')).toBeInTheDocument();
      expect(screen.getByText('sb-abc123')).toBeInTheDocument();
    });
  });

  it('shows policies list', async () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );
    fireEvent.click(screen.getByText('Policies'));
    await waitFor(() => {
      expect(screen.getByText('allow-api')).toBeInTheDocument();
      expect(screen.getByText('Allow API egress')).toBeInTheDocument();
    });
  });

  it('shows audit log', async () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );
    fireEvent.click(screen.getByText('Audit Logs'));
    await waitFor(() => {
      expect(screen.getByText('policy_evaluation')).toBeInTheDocument();
      expect(screen.getByText('ALLOW')).toBeInTheDocument();
    });
  });
});