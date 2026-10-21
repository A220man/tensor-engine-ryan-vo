import React from 'react';
import { useState, useEffect } from 'react';
import { policyApi } from '@/api/client';
import type { PolicyRule, PolicyRuleCreate } from '@/types/api';

export function PolicyList() {
  const [policies, setPolicies] = useState<PolicyRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 10, total: 0, totalPages: 0 });
  const [showModal, setShowModal] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState<PolicyRule | null>(null);
  const [formData, setFormData] = useState<PolicyRuleCreate>({
    name: '',
    description: '',
    action: 'deny',
    destination_host: '',
    destination_port: undefined,
    protocol: '',
    command_pattern: '',
    priority: 0,
    enabled: true,
  });
  const [formErrors, setFormErrors] = useState<Partial<Record<keyof PolicyRuleCreate, string>>>({});

  const fetchPolicies = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await policyApi.list(false, pagination.page, pagination.pageSize);
      setPolicies(response.data.items);
      setPagination({
        page: response.data.page,
        pageSize: response.data.page_size,
        total: response.data.total,
        totalPages: response.data.total_pages,
      });
    } catch (err) {
      setError('Failed to fetch policies');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicies();
  }, [pagination.page]);

  const openCreateModal = () => {
    setEditingPolicy(null);
    setFormData({
      name: '',
      description: '',
      action: 'deny',
      destination_host: '',
      destination_port: undefined,
      protocol: '',
      command_pattern: '',
      priority: 0,
      enabled: true,
    });
    setFormErrors({});
    setShowModal(true);
  };

  const openEditModal = (policy: PolicyRule) => {
    setEditingPolicy(policy);
    setFormData({
      name: policy.name,
      description: policy.description || '',
      action: policy.action,
      destination_host: policy.destination_host || '',
      destination_port: policy.destination_port ?? undefined,
      protocol: policy.protocol || '',
      command_pattern: policy.command_pattern || '',
      priority: policy.priority,
      enabled: policy.enabled,
    });
    setFormErrors({});
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingPolicy(null);
  };

  const validateForm = () => {
    const errors: Partial<Record<keyof PolicyRuleCreate, string>> = {};
    if (!formData.name.trim()) errors.name = 'Name is required';
    if (!formData.action) errors.action = 'Action is required';
    if (formData.action === 'allow' || formData.action === 'deny') {
      if (!formData.destination_host && !formData.command_pattern) {
        errors.destination_host = 'Either destination host or command pattern is required';
      }
    }
    if (formData.destination_port !== undefined && formData.destination_port !== null && (formData.destination_port < 1 || formData.destination_port > 65535)) {
      errors.destination_port = 'Port must be between 1 and 65535';
    }
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    try {
      if (editingPolicy) {
        await policyApi.update(editingPolicy.id, formData);
      } else {
        await policyApi.create(formData);
      }
      closeModal();
      fetchPolicies();
    } catch (err) {
      setError('Failed to save policy');
      console.error(err);
    }
  };

  const handleDelete = async (policy: PolicyRule) => {
    if (!window.confirm(`Delete policy "${policy.name}"?`)) return;
    try {
      await policyApi.delete(policy.id);
      fetchPolicies();
    } catch (err) {
      setError('Failed to delete policy');
      console.error(err);
    }
  };

  if (loading && policies.length === 0) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading policies...</p>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Network & Process Policies</h1>
        <button className="btn btn-primary" onClick={openCreateModal}>
          Create Policy
        </button>
      </div>

      {error && (
        <div className="alert alert-error" role="alert" style={{ marginBottom: '1rem' }}>
          <span>{error}</span>
        </div>
      )}

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>
                <th style={{ padding: '0.75rem 1rem' }}>Name</th>
                <th style={{ padding: '0.75rem 1rem' }}>Action</th>
                <th style={{ padding: '0.75rem 1rem' }}>Destination</th>
                <th style={{ padding: '0.75rem 1rem' }}>Port</th>
                <th style={{ padding: '0.75rem 1rem' }}>Protocol</th>
                <th style={{ padding: '0.75rem 1rem' }}>Command Pattern</th>
                <th style={{ padding: '0.75rem 1rem' }}>Priority</th>
                <th style={{ padding: '0.75rem 1rem' }}>Enabled</th>
                <th style={{ padding: '0.75rem 1rem' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {policies.length === 0 ? (
                <tr>
                  <td colSpan={9} style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No policies configured
                  </td>
                </tr>
              ) : (
                policies.map((policy) => (
                  <tr key={policy.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <strong>{policy.name}</strong>
                      {policy.description && <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{policy.description}</div>}
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <span className={`badge ${policy.action === 'allow' ? 'badge-running' : 'badge-error'}`}>
                        {policy.action.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      {policy.destination_host || <span style={{ color: 'var(--text-muted)' }}>Any</span>}
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      {policy.destination_port !== null && policy.destination_port !== undefined ? (
                        <code>{policy.destination_port}</code>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>Any</span>
                      )}
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      {policy.protocol || <span style={{ color: 'var(--text-muted)' }}>Any</span>}
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      {policy.command_pattern ? <code>{policy.command_pattern}</code> : <span style={{ color: 'var(--text-muted)' }}>Any</span>}
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>{policy.priority}</td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <span className={policy.enabled ? 'badge-running' : 'badge-stopped'}>
                        {policy.enabled ? 'Yes' : 'No'}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <button className="btn btn-secondary" style={{ marginRight: '0.5rem', padding: '0.25rem 0.5rem', fontSize: '0.8rem' }} onClick={() => openEditModal(policy)}>
                        Edit
                      </button>
                      <button className="btn btn-secondary" style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem', color: 'var(--error-color)' }} onClick={() => handleDelete(policy)}>
                        Delete
                      </button>
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

      {showModal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ marginBottom: '1.5rem' }}>{editingPolicy ? 'Edit Policy' : 'Create Policy'}</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label htmlFor="name" className="form-label">Name *</label>
                <input
                  id="name"
                  type="text"
                  className="form-input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
                {formErrors.name && <span className="form-error">{formErrors.name}</span>}
              </div>

              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label htmlFor="description" className="form-label">Description</label>
                <textarea
                  id="description"
                  className="form-input"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                />
              </div>

              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label htmlFor="action" className="form-label">Action *</label>
                <select
                  id="action"
                  className="form-input"
                  value={formData.action}
                  onChange={(e) => setFormData({ ...formData, action: e.target.value as 'allow' | 'deny' })}
                >
                  <option value="allow">Allow</option>
                  <option value="deny">Deny</option>
                </select>
              </div>

              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label htmlFor="destination_host" className="form-label">Destination Host</label>
                <input
                  id="destination_host"
                  type="text"
                  className="form-input"
                  placeholder="api.example.com"
                  value={formData.destination_host}
                  onChange={(e) => setFormData({ ...formData, destination_host: e.target.value })}
                />
                {formErrors.destination_host && <span className="form-error">{formErrors.destination_host}</span>}
              </div>

              <div style={{ display: 'flex', gap: '1rem' }}>
                <div className="form-group" style={{ marginBottom: '1rem', flex: 1 }}>
                  <label htmlFor="destination_port" className="form-label">Destination Port</label>
                  <input
                    id="destination_port"
                    type="number"
                    className="form-input"
                    placeholder="443"
                    min="1"
                    max="65535"
                    value={formData.destination_port ?? ''}
                    onChange={(e) => setFormData({ ...formData, destination_port: e.target.value ? parseInt(e.target.value, 10) : undefined })}
                  />
                  {formErrors.destination_port && <span className="form-error">{formErrors.destination_port}</span>}
                </div>

                <div className="form-group" style={{ marginBottom: '1rem', flex: 1 }}>
                  <label htmlFor="protocol" className="form-label">Protocol</label>
                  <select
                    id="protocol"
                    className="form-input"
                    value={formData.protocol}
                    onChange={(e) => setFormData({ ...formData, protocol: e.target.value })}
                  >
                    <option value="">Any</option>
                    <option value="tcp">TCP</option>
                    <option value="udp">UDP</option>
                    <option value="icmp">ICMP</option>
                  </select>
                </div>
              </div>

              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label htmlFor="command_pattern" className="form-label">Command Pattern (glob)</label>
                <input
                  id="command_pattern"
                  type="text"
                  className="form-input"
                  placeholder="npm * or python *.py"
                  value={formData.command_pattern}
                  onChange={(e) => setFormData({ ...formData, command_pattern: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                <div className="form-group" style={{ marginBottom: '1rem', flex: 1 }}>
                  <label htmlFor="priority" className="form-label">Priority</label>
                  <input
                    id="priority"
                    type="number"
                    className="form-input"
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value, 10) || 0 })}
                    min="0"
                  />
                </div>

                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={formData.enabled}
                    onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                  />
                  Enabled
                </label>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={closeModal}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingPolicy ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}