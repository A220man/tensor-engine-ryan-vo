import { useState } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { SandboxList } from '@/components/SandboxList';
import { SandboxDetail } from '@/components/SandboxDetail';
import { PolicyList } from '@/components/PolicyList';
import { AuditLogList } from '@/components/AuditLog';
import { CreateSandboxModal } from '@/components/CreateSandboxModal';

const navigation = [
  { path: '/sandboxes', label: 'Sandboxes' },
  { path: '/policies', label: 'Policies' },
  { path: '/audit', label: 'Audit Logs' },
];

export default function App() {
  const location = useLocation();
  const [showCreateModal, setShowCreateModal] = useState(false);

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="header-brand">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 12a8 8 0 018-8 8 8 0 018 8 8 8 0 01-8 8 8 8 0 01-8-8z" />
            </svg>
            <span>OpenShell</span>
          </div>
          <nav className="header-nav" aria-label="Main navigation">
            {navigation.map(item => (
              <Link
                key={item.path}
                to={item.path}
                className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <button
            className="btn btn-primary"
            onClick={() => setShowCreateModal(true)}
            aria-label="Create new sandbox"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
            New Sandbox
          </button>
        </div>
      </header>

      <main className="main-content">
        <Routes>
          <Route path="/sandboxes" element={<SandboxList />} />
          <Route path="/sandboxes/:sandboxId" element={<SandboxDetail />} />
          <Route path="/policies" element={<PolicyList />} />
          <Route path="/audit" element={<AuditLogList />} />
          <Route path="/" element={<SandboxList />} />
        </Routes>
      </main>

      <CreateSandboxModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreated={() => {}}
      />
    </div>
  );
}