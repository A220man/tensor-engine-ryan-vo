import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { sandboxApi } from '@/api/client';
import type { Sandbox, Execution, ExecutionCreate } from '@/types/api';

const statusBadges: Record<string, string> = {
  creating: 'badge-creating',
  running: 'badge-running',
  stopped: 'badge-stopped',
  error: 'badge-error',
  terminated: 'badge-terminated',
};

export function SandboxDetail() {
  const { sandboxId } = useParams<{ sandboxId: string }>();
  const navigate = useNavigate();
  const [sandbox, setSandbox] = useState<Sandbox | null>(null);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(true);
  const [execLoading, setExecLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [execPagination, setExecPagination] = useState({ page: 1, pageSize: 10, total: 0, totalPages: 0 });
  const [command, setCommand] = useState<string>('');
  const [args, setArgs] = useState<string>('');
  const [executing, setExecuting] = useState(false);
  const [execResult, setExecResult] = useState<Execution | null>(null);

  useEffect(() => {
    if (sandboxId) {
      fetchSandbox();
      fetchExecutions();
    }
  }, [sandboxId]);

  useEffect(() => {
    if (sandboxId) {
      fetchExecutions();
    }
  }, [sandboxId, execPagination.page]);

  const fetchSandbox = async () => {
    if (!sandboxId) return;
    try {
      const response = await sandboxApi.get(sandboxId);
      setSandbox(response.data);
    } catch (err) {
      setError('Failed to fetch sandbox');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchExecutions = async () => {
    if (!sandboxId) return;
    setExecLoading(true);
    try {
      const response = await sandboxApi.getExecutions(sandboxId, execPagination.page, execPagination.pageSize);
      setExecutions(response.data.items);
      setExecPagination({
        page: response.data.page,
        pageSize: response.data.page_size,
        total: response.data.total,
        totalPages: response.data.total_pages,
      });
    } catch (err) {
      console.error(err);
    } finally {
      setExecLoading(false);
    }
  };

  const handleStart = async () => {
    if (!sandboxId) return;
    try {
      const response = await sandboxApi.start(sandboxId);
      setSandbox(response.data);
    } catch (err) {
      setError('Failed to start sandbox');
      console.error(err);
    }
  };

  const handleStop = async () => {
    if (!sandboxId) return;
    try {
      const response = await sandboxApi.stop(sandboxId);
      setSandbox(response.data);
    } catch (err) {
      setError('Failed to stop sandbox');
      console.error(err);
    }
  };

  const handleTerminate = async () => {
    if (!sandboxId || !window.confirm('Terminate this sandbox? This cannot be undone.')) return;
    try {
      const response = await sandboxApi.terminate(sandboxId);
      setSandbox(response.data);
    } catch (err) {
      setError('Failed to terminate sandbox');
      console.error(err);
    }
  };

  const handleExecute = async (_e: React.FormEvent) => {
    try {
      const commandValue: string = command ? command.trim() : '';
      const argsValue: string = args ? args.trim() : '';
      const executeData: ExecutionCreate = { command: commandValue, args: argsValue ? argsValue.split(/\s+/) : [] };
      const response = await sandboxApi.execute(sandboxId as string, executeData);
      setExecResult(response.data);
      setArgs('');
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setError(axiosError.response?.data?.detail || 'Execution failed');
      console.error(err);
    } finally {
      setExecuting(false);
    }
  };

  if (loading && !sandbox) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading sandbox...</p>
      </div>
    );
  }

  if (error && !sandbox) {
    return (
      <div className="alert alert-error" role="alert">
        <span>{error}</span>
        <button className="btn btn-secondary" style={{ marginLeft: '1rem' }} onClick={() => navigate('/sandboxes')}>
          Back to Sandboxes
        </button>
      </div>
    );
  }

  if (!sandbox) return null;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <Link to="/sandboxes" className="btn btn-secondary" style={{ marginRight: '1rem' }}>
            ← Back
          </Link>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, display: 'inline', marginLeft: '0.5rem' }}>
            {sandbox.name}
          </h1>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {sandbox.status === 'stopped' && <button className="btn btn-primary" onClick={handleStart}>Start</button>}
          {sandbox.status === 'running' && <button className="btn btn-secondary" onClick={handleStop}>Stop</button>}
          {sandbox.status !== 'terminated' && <button className="btn btn-secondary" style={{ color: 'var(--error-color)' }} onClick={handleTerminate}>Terminate</button>}
        </div>
      </div>

      {error && (
        <div className="alert alert-error" role="alert" style={{ marginBottom: '1rem' }}>
          <span>{error}</span>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
        <div className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>Sandbox Info</h2>
          <dl style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0.5rem 1rem' }}>
            <dt style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Sandbox ID</dt>
            <dd style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{sandbox.sandbox_id}</dd>
            <dt style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Status</dt>
            <dd>
              <span className={`badge ${statusBadges[sandbox.status] || ''}`}>{sandbox.status}</span>
            </dd>
            <dt style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Policy</dt>
            <dd>
              {sandbox.policy ? (
                <span>{sandbox.policy.name} ({sandbox.policy.action})</span>
              ) : (
                <span style={{ color: 'var(--text-muted)' }}>No policy assigned</span>
              )}
            </dd>
            <dt style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Config</dt>
            <dd style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{sandbox.config}</dd>
            <dt style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Created</dt>
            <dd>{new Date(sandbox.created_at).toLocaleString()}</dd>
            <dt style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Started</dt>
            <dd>{sandbox.started_at ? new Date(sandbox.started_at).toLocaleString() : 'Never'}</dd>
            <dt style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Stopped</dt>
            <dd>{sandbox.stopped_at ? new Date(sandbox.stopped_at).toLocaleString() : 'N/A'}</dd>
          </dl>
        </div>

        <div className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>Execute Command</h2>
          <form onSubmit={handleExecute}>
            <div className="form-group" style={{ marginBottom: '1rem' }}>
              <label htmlFor="command" className="form-label">Command *</label>
              <input
                id="command"
                type="text"
                className="form-input"
                placeholder="echo hello"
                value={command}
                onChange={(e) => setCommand(e.target.value)}
                required
              />
            </div>
            <div className="form-group" style={{ marginBottom: '1rem' }}>
              <label htmlFor="args" className="form-label">Arguments</label>
              <input
                id="args"
                type="text"
                className="form-input"
                placeholder="--flag value"
                value={args}
                onChange={(e) => setArgs(e.target.value)}
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={executing || !command.trim()}>
              {executing ? 'Executing...' : 'Execute'}
            </button>
          </form>

          {execResult && (
            <div className="card" style={{ marginTop: '1.5rem' }}>
              <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>Last Execution Result</h3>
              <div style={{ fontSize: '0.875rem' }}>
                <div><strong>Exit Code:</strong> {execResult.exit_code}</div>
                <div><strong>Started:</strong> {new Date(execResult.started_at).toLocaleString()}</div>
                <div><strong>Completed:</strong> {execResult.completed_at ? new Date(execResult.completed_at).toLocaleString() : 'N/A'}</div>
                {execResult.trace_id && <div><strong>Trace ID:</strong> <code>{execResult.trace_id}</code></div>}
                {execResult.span_id && <div><strong>Span ID:</strong> <code>{execResult.span_id}</code></div>}
              </div>
              {execResult.stdout && (
                <div style={{ marginTop: '1rem' }}>
                  <strong>Stdout:</strong>
                  <pre style={{ fontSize: '0.75rem', background: 'var(--code-bg)', padding: '0.5rem', borderRadius: '4px', overflow: 'auto', maxHeight: '200px' }}>{execResult.stdout}</pre>
                </div>
              )}
              {execResult.stderr && (
                <div style={{ marginTop: '1rem' }}>
                  <strong>Stderr:</strong>
                  <pre style={{ fontSize: '0.75rem', background: 'var(--code-bg}', padding: '0.5rem', borderRadius: '4px', overflow: 'auto', maxHeight: '200px', color: 'var(--error-color)' }}>{execResult.stderr}</pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 600 }}>Execution History</h2>
        </div>

        {execLoading && executions.length === 0 ? (
          <div className="loading" style={{ padding: '2rem' }}>
            <div className="spinner"></div>
            <p>Loading executions...</p>
          </div>
        ) : (
          <>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>
                    <th style={{ padding: '0.75rem 1rem' }}>Command</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Exit Code</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Started</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Completed</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Trace ID</th>
                  </tr>
                </thead>
                <tbody>
                  {executions.length === 0 ? (
                    <tr>
                      <td colSpan={5} style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                        No executions yet
                      </td>
                    </tr>
                  ) : (
                    executions.map((exec) => (
                      <tr key={exec.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                        <td style={{ padding: '0.75rem 1rem' }}>
                          <code>{exec.command}</code>
                          {exec.args && <span style={{ color: 'var(--text-muted)', marginLeft: '0.5rem' }}>{exec.args}</span>}
                        </td>
                        <td style={{ padding: '0.75rem 1rem' }}>
                          <span className={exec.exit_code === 0 ? 'badge-running' : 'badge-error'}>
                            {exec.exit_code}
                          </span>
                        </td>
                        <td style={{ padding: '0.75rem 1rem' }}>{new Date(exec.started_at).toLocaleString()}</td>
                        <td style={{ padding: '0.75rem 1rem' }}>
                          {exec.completed_at ? new Date(exec.completed_at).toLocaleString() : 'Running...'}
                        </td>
                        <td style={{ padding: '0.75rem 1rem' }}>
                          {exec.trace_id ? <code style={{ fontSize: '0.75rem' }}>{exec.trace_id}</code> : <span style={{ color: 'var(--text-muted)' }}>N/A</span>}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {execPagination.totalPages > 1 && (
              <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginTop: '1rem' }}>
                <button
                  className="btn btn-secondary"
                  onClick={() => setExecPagination((p) => ({ ...p, page: p.page - 1 }))}
                  disabled={execPagination.page <= 1}
                >
                  Previous
                </button>
                <span style={{ display: 'flex', alignItems: 'center', padding: '0 0.5rem' }}>
                  Page {execPagination.page} of {execPagination.totalPages}
                </span>
                <button
                  className="btn btn-secondary"
                  onClick={() => setExecPagination((p) => ({ ...p, page: p.page + 1 }))}
                  disabled={execPagination.page >= execPagination.totalPages}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}