import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { sandboxApi } from '@/api/client';
import type { Sandbox } from '@/types/api';

const statusBadges: Record<string, string> = {
  creating: 'badge-creating',
  running: 'badge-running',
  stopped: 'badge-stopped',
  error: 'badge-error',
  terminated: 'badge-terminated',
};

export function SandboxList() {
  const [sandboxes, setSandboxes] = useState<Sandbox[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 10, total: 0, totalPages: 0 });
  const [statusFilter, setStatusFilter] = useState<string>('');

  const fetchSandboxes = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await sandboxApi.list(statusFilter || undefined, pagination.page, pagination.pageSize);
      setSandboxes(response.data.items);
      setPagination({
        page: response.data.page,
        pageSize: response.data.page_size,
        total: response.data.total,
        totalPages: response.data.total_pages,
      });
    } catch (err) {
      setError('Failed to fetch sandboxes');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSandboxes();
  }, [pagination.page, statusFilter]);

  const handleStart = async (sandboxId: string) => {
    try {
      const response = await sandboxApi.start(sandboxId);
      setSandboxes((prev) => prev.map((s) => (s.sandbox_id === sandboxId ? response.data : s)));
    } catch (err) {
      setError('Failed to start sandbox');
      console.error(err);
    }
  };

  const handleStop = async (sandboxId: string) => {
    try {
      const response = await sandboxApi.stop(sandboxId);
      setSandboxes((prev) => prev.map((s) => (s.sandbox_id === sandboxId ? response.data : s)));
    } catch (err) {
      setError('Failed to stop sandbox');
      console.error(err);
    }
  };

  const handleTerminate = async (sandboxId: string) => {
    if (!window.confirm('Terminate this sandbox? This cannot be undone.')) return;
    try {
      const response = await sandboxApi.terminate(sandboxId);
      setSandboxes((prev) => prev.map((s) => (s.sandbox_id === sandboxId ? response.data : s)));
    } catch (err) {
      setError('Failed to terminate sandbox');
      console.error(err);
    }
  };

  if (loading && sandboxes.length === 0) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading sandboxes...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-error" role="alert">
        <span>{error}</span>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Sandboxes</h1>
        <Link to="/sandboxes/create" className="btn btn-primary">
          Create Sandbox
        </Link>
      </div>

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
          <div style={{ flex: 1, minWidth: '200px' }}>
            <label htmlFor="status-filter" className="form-label">Status Filter</label>
            <select
              id="status-filter"
              className="form-input"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All</option>
              <option value="creating">Creating</option>
              <option value="running">Running</option>
              <option value="stopped">Stopped</option>
              <option value="error">Error</option>
              <option value="terminated">Terminated</option>
            </select>
          </div>
        </div>
      </div>

      <div className="card">
        {sandboxes.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            <p style={{ fontSize: '1.125rem', marginBottom: '0.5rem' }}>No sandboxes found</p>
            <Link to="/sandboxes/create" className="btn btn-primary">
              Create your first sandbox
            </Link>
          </div>
        ) : (
          <>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>
                    <th style={{ padding: '0.75rem 1rem' }}>Name</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Sandbox ID</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Status</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Policy</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Created</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sandboxes.map((sandbox) => (
                    <tr key={sandbox.sandbox_id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <Link to={`/sandboxes/${sandbox.sandbox_id}`} style={{ fontWeight: 500 }}>
                          {sandbox.name}
                        </Link>
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <code style={{ fontSize: '0.875rem' }}>{sandbox.sandbox_id}</code>
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <span className={`badge ${statusBadges[sandbox.status] || ''}`}>{sandbox.status}</span>
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        {sandbox.policy ? (
                          <span>{sandbox.policy.name} ({sandbox.policy.action})</span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>None</span>
                        )}
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>{new Date(sandbox.created_at).toLocaleString()}</td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <div style={{ display: 'flex', gap: '0.25rem' }}>
                          <Link to={`/sandboxes/${sandbox.sandbox_id}`} className="btn btn-secondary" style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}>
                            Details
                          </Link>
                          {sandbox.status === 'stopped' && (
                            <button className="btn btn-secondary" style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }} onClick={() => handleStart(sandbox.sandbox_id)}>
                              Start
                            </button>
                          )}
                          {sandbox.status === 'running' && (
                            <button className="btn btn-secondary" style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }} onClick={() => handleStop(sandbox.sandbox_id)}>
                              Stop
                            </button>
                          )}
                          {sandbox.status !== 'terminated' && (
                            <button className="btn btn-secondary" style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem', color: 'var(--error-color)' }} onClick={() => handleTerminate(sandbox.sandbox_id)}>
                              Terminate
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {pagination.totalPages > 1 && (
              <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginTop: '1rem' }}>
                <button
                  className="btn btn-secondary"
                  onClick={() => setPagination((p) => ({ ...p, page: p.page - 1 }))}
                  disabled={pagination.page <= 1}
                >
                  Previous
                </button>
                <span style={{ display: 'flex', alignItems: 'center', padding: '0 0.5rem' }}>
                  Page {pagination.page} of {pagination.totalPages}
                </span>
                <button
                  className="btn btn-secondary"
                  onClick={() => setPagination((p) => ({ ...p, page: p.page + 1 }))}
                  disabled={pagination.page >= pagination.totalPages}
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