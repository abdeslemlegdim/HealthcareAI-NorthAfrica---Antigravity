import API from './api';

export async function getAccountSummary(accountId) {
  const normalizedId = String(accountId || '').trim();
  if (!normalizedId) {
    const meResp = await API.get('/api/v1/accounts/me/summary');
    return meResp.data;
  }

  const url = `/api/v1/accounts/${encodeURIComponent(normalizedId)}/summary`;
  const resp = await API.get(url);
  return resp.data;
}
