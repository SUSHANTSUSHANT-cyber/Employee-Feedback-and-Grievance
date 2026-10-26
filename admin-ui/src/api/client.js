// Keep API calls same-origin in the deployed FastAPI build.  VITE_API_BASE_URL
// is available for a separately hosted UI; the Vite development proxy handles
// the default relative path locally.
export const BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api/rest').replace(/\/+$/, '')
export const AUTH_BASE_URL = BASE_URL.replace(/\/rest$/, '') + '/auth'

export const apiUrl = path => `${BASE_URL}${path}`
export const authUrl = path => `${AUTH_BASE_URL}${path}`

export class ApiContractError extends Error {}

export function notifyUnauthorized() {
  window.dispatchEvent(new Event('auth-required'))
}

function errorDetail(body, fallback) {
  return body && typeof body.detail === 'string' ? body.detail : fallback
}

export async function request(path, options = {}) {
  const response = await fetch(apiUrl(path), {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    credentials: 'include',
    ...options,
  })
  const body = response.status === 204 ? null : await response.json().catch(() => null)
  if (response.status === 401) notifyUnauthorized()
  if (!response.ok) throw new Error(errorDetail(body, `Request failed (${response.status})`))
  return body
}

export async function authRequest(path, options = {}) {
  const response = await fetch(authUrl(path), {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    credentials: 'include',
    ...options,
  })
  const body = response.status === 204 ? null : await response.json().catch(() => null)
  if (!response.ok) throw new Error(errorDetail(body, `Request failed (${response.status})`))
  return body
}

export function arrayResponse(value, endpoint) {
  if (Array.isArray(value)) return value
  console.error(`API contract error for ${endpoint}: expected an array.`, value)
  throw new ApiContractError(`Unexpected response from ${endpoint}: expected a list.`)
}

export function objectResponse(value, endpoint, allowNull = false) {
  if ((allowNull && value === null) || (value && typeof value === 'object' && !Array.isArray(value))) return value
  console.error(`API contract error for ${endpoint}: expected an object.`, value)
  throw new ApiContractError(`Unexpected response from ${endpoint}: expected an object.`)
}
