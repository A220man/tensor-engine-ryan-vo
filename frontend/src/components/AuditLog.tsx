import { useState, useEffect } from 'react';
import { auditApi } from '@/api/client';
import type { AuditLog } from '@/types/api';

export function AuditLogList() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0, totalPages: 0 });
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [sandboxIdFilter, setSandboxIdFilter] = useState('');

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await auditApi.list(eventTypeFilter || undefined, sandboxIdFilter || undefined, pagination.page, pagination.pageSize);
      setLogs(response.data.items);
      setPagination({
        page: response.data.page,
        pageSize: response.data.page_size,
        total: response.data.total,
        totalPages: response.data.total_pages,
      });
    } catch (err) {
      setError('Failed to fetch audit logs');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [pagination.page, eventTypeFilter, sandboxIdFilter]);

  if (loading && logs.length === 0) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading audit logs...</p>
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
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Audit Logs</h1>
      </div>

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>Filters</h2>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div style={{ flex: 1, minWidth: '200px' }}>
            <label htmlFor="event-type-filter" className="form-label">Event Type</label>
            <input
              id="event-type-filter"
              type="text"
              className="form-input"
              placeholder="Filter by event type (e.g. policy_evaluation)"
              value={eventTypeFilter}
              onChange={(e) => setEventTypeFilter(e.target.value)}
            />
          </div>
          <div style={{ flex: 1, minWidth: '200px' }}>
            <label htmlFor="sandbox-id-filter" className="form-label">Sandbox ID</label>
            <input
              id="sandbox-id-filter"
              type="text"
              className="form-input"
              placeholder="Filter by sandbox ID"
              value={sandboxIdFilter}
              onChange={(e) => setSandboxIdFilter(e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="card">
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>
                <th style={{ padding: '0.75rem 1rem' }}>Time</th>
                <th style={{ padding: '0.75rem 1rem' }}>Event Type</th>
                <th style={{ padding: '0.75rem 1rem' }}>Sandbox ID</th>
                <th style={{ padding: '0.75rem 1rem' }}>Decision</th>
                <th style={{ padding: '0.75rem 1rem' }}>Details</th>
                <th style={{ padding: '0.75rem 1rem' }}>Trace ID</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No audit logs found
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '0.75rem 1rem', whiteSpace: 'nowrap' }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <code style={{ fontSize: '0.875rem' }}>{log.event_type}</code>
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      {log.sandbox_id || <span style={{ color: 'var(--text-muted)' }}>N/A</span>}
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      {log.decision ? (
                        <span className={`badge ${log.decision === 'allow' ? 'badge-running' : log.decision === 'deny' ? 'badge-error' : 'badge-info'}`}>
                          {log.decision.toUpperCase()}
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>N/A</span>
                      )}
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <pre style={{ fontSize: '0.75rem', maxHeight: '100px', overflow: 'auto', margin: 0 }}>{log.details || 'N/A'}</pre>
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      {log.trace_id ? <code style={{ fontSize: '0.75rem' }}>{log.trace_id}</code> : <span style={{ color: 'var(--text-muted)' }}>N/A</span>}
                    </td>
                  </tr>
                ))
              )}
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
      </div>
    </div>
  );
}