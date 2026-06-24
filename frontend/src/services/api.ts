import type {
  GpsPayload,
  LoginResponse,
  MonthlyClosure,
  PhotoEvidence,
  ReportItem,
  ReverseGeocodeResponse,
  SignupApprovePayload,
  SignupRequest,
  SignupRequestPayload,
  StatusSolicitacaoCadastro,
  Trip,
  User,
  Vehicle,
  VehicleInRoute,
} from '../types/domain'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) || ''

interface RequestOptions extends RequestInit {
  token?: string
}

export class ApiError extends Error {
  status: number
  details: unknown

  constructor(status: number, message: string, details: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers)
  if (options.token) {
    headers.set('Authorization', `Bearer ${options.token}`)
  }
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    credentials: 'include',
  })

  if (!response.ok) {
    let details: unknown
    try {
      details = await response.json()
    } catch {
      details = await response.text()
    }
    throw new ApiError(response.status, extractErrorMessage(details, response.status), details)
  }

  if (response.status === 204) {
    return undefined as T
  }

  const contentType = response.headers.get('Content-Type') || ''
  if (!contentType.includes('application/json')) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

function extractErrorMessage(details: unknown, status: number) {
  if (typeof details === 'object' && details !== null && 'detail' in details) {
    const detail = (details as { detail: unknown }).detail
    if (typeof detail === 'string') {
      return detail
    }
    if (Array.isArray(detail) && detail.length > 0) {
      return 'Confira os campos obrigatorios.'
    }
  }
  return `Erro ${status} na API.`
}

function multipart(payload: object, foto: File) {
  const form = new FormData()
  form.set('payload', JSON.stringify(payload))
  form.set('foto_hodometro', foto)
  return form
}

export const api = {
  login(email: string, senha: string) {
    return request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, senha }),
    })
  },
  logout(token: string) {
    return request<void>('/auth/logout', {
      method: 'POST',
      token,
    })
  },
  changePassword(token: string, senhaAtual: string, novaSenha: string) {
    return request<void>('/auth/change-password', {
      method: 'POST',
      token,
      body: JSON.stringify({ senha_atual: senhaAtual, nova_senha: novaSenha }),
    })
  },
  forgotPassword(email: string) {
    return request<void>('/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    })
  },
  resetPassword(resetToken: string, novaSenha: string) {
    return request<void>('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token: resetToken, nova_senha: novaSenha }),
    })
  },
  createSignupRequest(payload: SignupRequestPayload) {
    return request<SignupRequest>('/signup-requests', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  signupRequests(token: string, status?: StatusSolicitacaoCadastro) {
    const params = new URLSearchParams()
    if (status) {
      params.set('status', status)
    }
    const query = params.toString()
    return request<SignupRequest[]>(`/signup-requests${query ? `?${query}` : ''}`, { token })
  },
  approveSignupRequest(token: string, requestId: string, payload: SignupApprovePayload) {
    return request<SignupRequest>(`/signup-requests/${requestId}/approve`, {
      method: 'POST',
      token,
      body: JSON.stringify(payload),
    })
  },
  rejectSignupRequest(token: string, requestId: string, motivo: string) {
    return request<SignupRequest>(`/signup-requests/${requestId}/reject`, {
      method: 'POST',
      token,
      body: JSON.stringify({ motivo }),
    })
  },
  adminResetPassword(token: string, usuarioId: string, novaSenha: string) {
    return request<void>(`/users/${usuarioId}/reset-password`, {
      method: 'POST',
      token,
      body: JSON.stringify({ nova_senha: novaSenha }),
    })
  },
  pendingSignupCount(token: string) {
    return request<{ count: number }>('/signup-requests/pending-count', { token })
  },
  allVehicles(token: string) {
    return request<Vehicle[]>('/vehicles/all', { token })
  },
  patchUser(token: string, usuarioId: string, data: Record<string, unknown>) {
    return request<User>(`/users/${usuarioId}`, {
      method: 'PATCH',
      token,
      body: JSON.stringify(data),
    })
  },
  patchVehicle(token: string, veiculoId: string, data: Record<string, unknown>) {
    return request<Vehicle>(`/vehicles/${veiculoId}`, {
      method: 'PATCH',
      token,
      body: JSON.stringify(data),
    })
  },
  me(token: string) {
    return request<User>('/auth/me', { token })
  },
  users(token: string) {
    return request<User[]>('/users', { token })
  },
  vehicles(token: string) {
    return request<Vehicle[]>('/vehicles', { token })
  },
  vehiclesInRoute(token: string) {
    return request<VehicleInRoute[]>('/vehicles/in-route', { token })
  },
  trips(token: string) {
    return request<Trip[]>('/trips', { token })
  },
  reverseGeocode(token: string, latitude: number, longitude: number, signal?: AbortSignal) {
    const params = new URLSearchParams({
      latitude: String(latitude),
      longitude: String(longitude),
    })
    return request<ReverseGeocodeResponse>(`/geocoding/reverse?${params.toString()}`, { token, signal })
  },
  tripPhotos(token: string, tripId: string) {
    return request<PhotoEvidence[]>(`/trips/${tripId}/photos`, { token })
  },
  startTrip(token: string, veiculoId: string, kmInicial: number, gps: GpsPayload, foto: File) {
    return request<Trip>('/trips/start', {
      method: 'POST',
      token,
      body: multipart(
        {
          veiculo_id: veiculoId,
          km_inicial: kmInicial,
          gps,
        },
        foto,
      ),
    })
  },
  finishTrip(token: string, tripId: string, kmFinal: number, rotaUtilizada: string, gps: GpsPayload, foto: File) {
    return request<Trip>(`/trips/${tripId}/finish`, {
      method: 'POST',
      token,
      body: multipart(
        {
          km_final: kmFinal,
          rota_utilizada: rotaUtilizada,
          gps,
        },
        foto,
      ),
    })
  },
  patchTrip(token: string, tripId: string, data: { km_inicial?: number; km_final?: number; rota_utilizada?: string }) {
    return request<Trip>(`/trips/${tripId}`, {
      method: 'PATCH',
      token,
      body: JSON.stringify(data),
    })
  },
  monthlyReport(token: string, ano: number, mes: number, motoristaId?: string, veiculoId?: string) {
    const params = new URLSearchParams({ ano: String(ano), mes: String(mes) })
    if (motoristaId) {
      params.set('motorista_id', motoristaId)
    }
    if (veiculoId) {
      params.set('veiculo_id', veiculoId)
    }
    return request<ReportItem[]>(`/reports/monthly?${params.toString()}`, { token })
  },
  monthlyClosures(token: string, ano: number, mes: number, motoristaId?: string) {
    const params = new URLSearchParams({ ano: String(ano), mes: String(mes) })
    if (motoristaId) {
      params.set('motorista_id', motoristaId)
    }
    return request<MonthlyClosure[]>(`/reports/monthly/closures?${params.toString()}`, { token })
  },
  closeClosure(token: string, motoristaId: string, ano: number, mes: number, observacao?: string) {
    return request<MonthlyClosure>(`/reports/monthly/closures/${motoristaId}/close?ano=${ano}&mes=${mes}`, {
      method: 'POST',
      token,
      body: JSON.stringify({ observacao }),
    })
  },
  async exportMonthly(token: string, ano: number, mes: number, motoristaId?: string, veiculoId?: string) {
    const params = new URLSearchParams({ ano: String(ano), mes: String(mes) })
    if (motoristaId) {
      params.set('motorista_id', motoristaId)
    }
    if (veiculoId) {
      params.set('veiculo_id', veiculoId)
    }
    return fetchBlob(`/reports/monthly/export?${params.toString()}`, token)
  },
  photo(token: string, downloadUrl: string) {
    return fetchBlob(downloadUrl, token)
  },
}

async function fetchBlob(path: string, token: string) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    credentials: 'include',
  })
  if (!response.ok) {
    throw new ApiError(response.status, `Erro ${response.status} na API.`, await response.text())
  }
  return response.blob()
}
