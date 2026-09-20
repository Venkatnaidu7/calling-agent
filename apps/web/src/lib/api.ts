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
