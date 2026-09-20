const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '')

export interface AuthResponse {
  access_token: string
  refresh_token?: string
  token_type?: string
  expires_in?: number
}

export interface RegisterPayload {
  email: string
  password: string
  business_name: string
  first_name?: string
  last_name?: string
}

type RequestOptions = RequestInit & { auth?: boolean }

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { auth = true, headers, ...init } = options

  const requestHeaders = new Headers(headers)
  if (init.body && !requestHeaders.has('Content-Type')) {
    requestHeaders.set('Content-Type', 'application/json')
  }

  if (auth) {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
    if (token) {
      requestHeaders.set('Authorization', `Bearer ${token}`)
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: requestHeaders,
    cache: 'no-store',
  })

  const contentType = response.headers.get('content-type') || ''
  const payload = contentType.includes('application/json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    const detail =
      typeof payload === 'object' && payload
        ? (payload.detail || payload.message || payload.error?.message)
        : null

    throw new Error(detail || `Request failed with status ${response.status}`)
  }

  return payload as T
}

export class ApiClient {
  static async login(email: string, password: string): Promise<AuthResponse> {
    return request<AuthResponse>('/auth/login', {
      method: 'POST',
      auth: false,
      body: JSON.stringify({ email, password }),
    })
  }

  static async register(payload: RegisterPayload): Promise<AuthResponse> {
    return request<AuthResponse>('/auth/register', {
      method: 'POST',
      auth: false,
      body: JSON.stringify(payload),
    })
  }

  static async forgotPassword(email: string): Promise<unknown> {
    return request('/auth/forgot-password', {
      method: 'POST',
      auth: false,
      body: JSON.stringify({ email }),
    })
  }

  static async resetPassword(token: string, password: string): Promise<unknown> {
    return request('/auth/reset-password', {
      method: 'POST',
      auth: false,
      body: JSON.stringify({ token, new_password: password }),
    })
  }

  static async getDncList(): Promise<any> {
    return request('/compliance/dnc')
  }

  static async addToDnc(payload: {
    phone_number: string
    reason?: string
    source?: string
  }): Promise<any> {
    return request('/compliance/dnc', {
      method: 'POST',
      body: JSON.stringify({
        phone_number: payload.phone_number,
        reason: payload.reason,
        source: payload.source || 'manual',
      }),
    })
  }

  static async importDncCsv(formData: FormData): Promise<any> {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
    const headers = new Headers()
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }

    const response = await fetch(`${API_BASE_URL}/compliance/dnc/import`, {
      method: 'POST',
      headers,
      body: formData,
      cache: 'no-store',
    })

    const contentType = response.headers.get('content-type') || ''
    const payload = contentType.includes('application/json')
      ? await response.json()
      : await response.text()

    if (!response.ok) {
      const detail =
        typeof payload === 'object' && payload
          ? (payload.detail || payload.message || payload.error?.message)
          : null
      throw new Error(detail || `Request failed with status ${response.status}`)
    }

    return payload
  }

  static async removeFromDnc(phoneNumber: string): Promise<void> {
    await request<void>(`/compliance/dnc/${encodeURIComponent(phoneNumber)}`, {
      method: 'DELETE',
    })
  }

  static async removeDnc(phoneNumber: string): Promise<void> {
    return this.removeFromDnc(phoneNumber)
  }

  static async getCalls(params: Record<string, string | number | undefined> = {}): Promise<any> {
    const query = Object.entries(params)
      .filter(([, value]) => value !== undefined && value !== null && value !== '')
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
      .join('&')
    return request(query ? `/calls?${query}` : '/calls')
  }

  static async getCall(callId: string): Promise<any> {
    return request(`/calls/${encodeURIComponent(callId)}`)
  }

  static async getCallTranscript(callId: string): Promise<any> {
    return request(`/calls/${encodeURIComponent(callId)}/transcript`)
  }

  static async getCampaigns(params: Record<string, string | number | undefined> = {}): Promise<any> {
    const query = Object.entries(params)
      .filter(([, value]) => value !== undefined && value !== null && value !== '')
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
      .join('&')
    return request(query ? `/campaigns?${query}` : '/campaigns')
  }

  static async getCampaign(campaignId: string): Promise<any> {
    return request(`/campaigns/${encodeURIComponent(campaignId)}`)
  }

  static async createCampaign(payload: any): Promise<any> {
    return request('/campaigns', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  static async updateCampaign(campaignId: string, payload: any): Promise<any> {
    return request(`/campaigns/${encodeURIComponent(campaignId)}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    })
  }

  static async getContacts(params: Record<string, string | number | undefined> = {}): Promise<any> {
    const query = Object.entries(params)
      .filter(([, value]) => value !== undefined && value !== null && value !== '')
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
      .join('&')
    return request(query ? `/contacts?${query}` : '/contacts')
  }

  static async createContact(payload: {
    phone_number: string
    email?: string
    first_name?: string
    last_name?: string
    company?: string
    timezone?: string
    tags?: string[]
    custom_fields?: Record<string, unknown>
    notes?: string
    status?: string
    do_not_call?: boolean
  }): Promise<any> {
    return request('/contacts', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  static async deleteContact(contactId: string): Promise<void> {
    await request<void>(`/contacts/${encodeURIComponent(contactId)}`, {
      method: 'DELETE',
    })
  }

  static async importContactsCsv(formData: FormData): Promise<any> {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
    const headers = new Headers()
    if (token) headers.set('Authorization', `Bearer ${token}`)

    const response = await fetch(`${API_BASE_URL}/contacts/import`, {
      method: 'POST',
      headers,
      body: formData,
      cache: 'no-store',
    })

    const contentType = response.headers.get('content-type') || ''
    const payload = contentType.includes('application/json')
      ? await response.json()
      : await response.text()

    if (!response.ok) {
      const detail =
        typeof payload === 'object' && payload
          ? (payload.detail || payload.message || payload.error?.message)
          : null
      throw new Error(detail || `Request failed with status ${response.status}`)
    }

    return payload
  }

  static async getKnowledgeBases(): Promise<any> {
    return request('/knowledge-bases')
  }

  static async createKnowledgeBase(payload: {
    name: string
    description?: string
    agent_id?: string
  }): Promise<any> {
    return request('/knowledge-bases', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  static async uploadDocument(kbId: string, formData: FormData): Promise<any> {
    const data = formData
    const title = formData.get('title')
    const sourceType = formData.get('source_type')
    const content = formData.get('content')

    // The backend knowledge upload endpoint currently expects JSON metadata,
    // not multipart/form-data. Preserve the browser API while adapting here.
    return request(`/knowledge-bases/${encodeURIComponent(kbId)}/documents`, {
      method: 'POST',
      body: JSON.stringify({
        title: typeof title === 'string' && title ? title : 'Uploaded document',
        source_type: typeof sourceType === 'string' && sourceType ? sourceType : 'text',
        content: typeof content === 'string' ? content : null,
      }),
    })
  }

  static async searchKnowledgeBase(kbId: string, query: string): Promise<any> {
    return request(`/knowledge-bases/${encodeURIComponent(kbId)}/search`, {
      method: 'POST',
      body: JSON.stringify({
        query,
        knowledge_base_id: kbId,
        max_results: 5,
        min_relevance: 0.7,
      }),
    })
  }

  static async deleteKnowledgeBase(kbId: string): Promise<void> {
    await request<void>(`/knowledge-bases/${encodeURIComponent(kbId)}`, {
      method: 'DELETE',
    })
  }

  static async getPhoneNumbers(params: Record<string, string | number | undefined> = {}): Promise<any> {
    const query = Object.entries(params)
      .filter(([, value]) => value !== undefined && value !== null && value !== '')
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
      .join('&')
    return request(query ? `/phone-numbers?${query}` : '/phone-numbers')
  }

  static async searchPhoneNumbers(params: Record<string, string | number | undefined> = {}): Promise<any> {
    return request('/phone-numbers/search', { method: 'GET' })
  }

  static async provisionPhoneNumber(payload: any): Promise<any> {
    return request('/phone-numbers', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  static async releasePhoneNumber(id: string): Promise<void> {
    await request<void>(`/phone-numbers/${encodeURIComponent(id)}/release`, {
      method: 'POST',
    })
  }

  static async getWebhookEndpoints(): Promise<any> {
    return request('/webhooks')
  }

  static async createWebhookEndpoint(payload: any): Promise<any> {
    return request('/webhooks', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  static async deleteWebhookEndpoint(id: string): Promise<void> {
    await request<void>(`/webhooks/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    })
  }

  static async getUsers(params: Record<string, string | number | undefined> = {}): Promise<any> {
    const query = Object.entries(params)
      .filter(([, value]) => value !== undefined && value !== null && value !== '')
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
      .join('&')
    return request(query ? `/users?${query}` : '/users')
  }

  static async inviteUser(payload: any): Promise<any> {
    return request('/users', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  static async deleteUser(id: string): Promise<void> {
    await request<void>(`/users/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    })
  }

  static async updateUserRole(id: string, role: string): Promise<any> {
    return request(`/users/${encodeURIComponent(id)}/role`, {
      method: 'PUT',
      body: JSON.stringify({ role }),
    })
  }

  static async getAgents(): Promise<any> {
    return request('/agents')
  }

  static async createAgent(payload: { name: string; description?: string }): Promise<any> {
    return request('/agents', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  static async getAnalytics(days = 30): Promise<any> {
    return request(`/analytics/dashboard?days=${encodeURIComponent(days)}`)
  }

  static setToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', token)
    }
  }

  static getToken(): string | null {
    return typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
  }

  static setRefreshToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('refresh_token', token)
    }
  }

  static getRefreshToken(): string | null {
    return typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null
  }

  static async getSubscription(): Promise<any> {
    return request('/billing/subscription')
  }

  static async getBillingUsage(): Promise<any> {
    return request('/billing/usage')
  }

  static async getBillingPlans(): Promise<any> {
    return request('/billing/plans', { auth: false })
  }

  static async createCheckoutSession(payload: any): Promise<any> {
    return request('/billing/checkout', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  static async openBillingPortal(returnUrl: string): Promise<any> {
    return request('/billing/portal?return_url=' + encodeURIComponent(returnUrl), {
      method: 'POST',
    })
  }

  static clearTokens(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('token')
    }
  }
}
