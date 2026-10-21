import { useState, useEffect } from 'react';
import { sandboxApi, policyApi } from '@/api/client';
import type { SandboxCreate, PolicyRule } from '@/types/api';

interface CreateSandboxModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export function CreateSandboxModal({ isOpen, onClose, onCreated }: CreateSandboxModalProps) {
  const [policies, setPolicies] = useState<PolicyRule[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<SandboxCreate>({
    name: '',
    policy_id: undefined,
    config: '{"memory": "512m", "cpu": "0.5"}',
  });
  const [formErrors, setFormErrors] = useState<Partial<Record<keyof SandboxCreate, string>>>({});

  useEffect(() => {
    if (isOpen) {
      fetchPolicies();
      setFormData({
        name: '',
        policy_id: undefined,
        config: '{"memory": "512m", "cpu": "0.5"}',
      });
      setFormErrors({});
    }
  }, [isOpen]);

  const fetchPolicies = async () => {
    try {
      const response = await policyApi.list(true);
      setPolicies(response.data.items);
    } catch (err) {
      console.error(err);
    }
  };

  const validateForm = () => {
    const errors: Partial<Record<keyof SandboxCreate, string>> = {};
    if (!formData.name.trim()) errors.name = 'Name is required';
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    setError(null);
    try {
      await sandboxApi.create(formData);
      onCreated();
      onClose();
    } catch (err: any) {
      if (err.response?.status === 409) {
        setFormErrors({ name: 'Sandbox with this name already exists' });
      } else {
        setError('Failed to create sandbox');
        console.error(err);
      }
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="create-sandbox-title">
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="card-header">
          <h2 id="create-sandbox-title" className="card-title">Create Sandbox</h2>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="card-body">
            {error && (
              <div className="alert alert-error" role="alert">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <span>{error}</span>
              </div>
            )}

            <div className="form-group">
              <label htmlFor="name" className="form-label">Name *</label>
              <input
                id="name"
                type="text"
                className="form-input"
                value={formData.name}
                onChange={e => setFormData(d => ({ ...d, name: e.target.value }))}
                placeholder="e.g., my-agent-sandbox"
                autoFocus
                aria-invalid={!!formErrors.name}
                aria-describedby={formErrors.name ? 'name-error' : undefined}
                disabled={loading}
              />
              {formErrors.name && (
                <span id="name-error" className="form-error" role="alert">{formErrors.name}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="policy_id" className="form-label">Policy (optional)</label>
              <select
                id="policy_id"
                className="form-select"
                value={formData.policy_id ?? ''}
                onChange={e => setFormData(d => ({ ...d, policy_id: e.target.value ? parseInt(e.target.value) : undefined }))}
                disabled={loading}
              >
                <option value="">No policy (default deny)</option>
                {policies.map(policy => (
                  <option key={policy.id} value={policy.id}>
                    {policy.name} ({policy.action})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="config" className="form-label">Configuration (JSON)</label>
              <textarea
                id="config"
                className="form-input form-textarea font-mono"
                value={formData.config}
                onChange={e => setFormData(d => ({ ...d, config: e.target.value }))}
                placeholder='{"memory": "512m", "cpu": "0.5"}'
                disabled={loading}
              />
              <span className="form-help">Sandbox resource limits and settings</span>
            </div>
          </div>
          <div className="card-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={loading}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading || !formData.name.trim()}>
              {loading ? (
                <>
                  <span className="spinner" style={{ width: '1rem', height: '1rem' }} aria-hidden="true" />
                  Creating...
                </>
              ) : (
                'Create Sandbox'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}