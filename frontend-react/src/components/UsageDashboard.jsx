import React, { useEffect, useState } from 'react';
import { getAccountSummary } from '../services/usageApi';

export default function UsageDashboard({ accountId }) {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    setError(null);
    setSummary(null);
    getAccountSummary(accountId)
      .then((s) => mounted && setSummary(s))
      .catch((e) => mounted && setError(e.message));
    return () => (mounted = false);
  }, [accountId]);

  if (error) return <div className="usage-dashboard error">Error: {error}</div>;
  if (!summary) return <div className="usage-dashboard loading">Loading usage…</div>;

  const { available_credits, reserved_credits, lifetime_earned, lifetime_spent } = summary;

  return (
    <div className="usage-dashboard">
      <h3>Usage & Credits</h3>
      <div>Available: <strong>{available_credits}</strong></div>
      <div>Reserved: <strong>{reserved_credits}</strong></div>
      <div>Lifetime earned: <strong>{lifetime_earned}</strong></div>
      <div>Lifetime spent: <strong>{lifetime_spent}</strong></div>
    </div>
  );
}
