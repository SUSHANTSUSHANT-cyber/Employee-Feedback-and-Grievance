import { apiUrl, arrayResponse, authRequest, notifyUnauthorized, objectResponse, request } from './client'
import * as XLSX from 'xlsx'

const encoded = value => encodeURIComponent(value)
const employeeFields = ['id', 'name', 'email', 'department']

function importError(response, body, fallback) {
  if (body && Object.hasOwn(body, 'detail')) {
    // FastAPI returns 422 details as an array. Keep that response visible in
    // the upload result instead of replacing it with a generic HTTP message.
    return typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
  }
  return fallback || `Request failed (${response.status})`
}

async function employeeRequest(path, method, body) {
  const response = await fetch(apiUrl(path), {
    method,
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(body),
  })
  const data = await response.json().catch(() => null)
  if (response.status === 401) notifyUnauthorized()
  return { response, data }
}

async function employeeRowsFromFile(file) {
  const name = (file.name || '').toLowerCase()
  if (!name.endsWith('.csv') && !name.endsWith('.xlsx')) {
    throw new Error('Upload a CSV or XLSX employee file.')
  }

  let workbook
  try {
    workbook = XLSX.read(await file.arrayBuffer(), { type: 'array' })
  } catch {
    throw new Error('Could not read the uploaded employee file.')
  }
  const sheet = workbook.Sheets[workbook.SheetNames[0]]
  if (!sheet) throw new Error('The uploaded employee file has no worksheet.')

  // raw:false uses the displayed spreadsheet value, preserving IDs such as
  // 00123 when Excel formats the cell with leading zeroes.
  const rows = XLSX.utils.sheet_to_json(sheet, { defval: '', raw: false, blankrows: false })
  const headers = new Set(rows.flatMap(row => Object.keys(row).map(key => key.trim())))
  if (!rows.length || !employeeFields.every(field => headers.has(field))) {
    throw new Error('File must include: id, name, email, department.')
  }

  return rows.map((row, index) => {
    const normalized = Object.fromEntries(Object.entries(row).map(([key, value]) => [key.trim(), value]))
    // This object intentionally mirrors EmployeeIn in app/schemas.py exactly.
    // Do not trim or otherwise transform id: it is an opaque employee key.
    const employee = {
      id: normalized.id == null ? '' : String(normalized.id),
      name: normalized.name == null ? '' : String(normalized.name),
      email: normalized.email == null ? '' : String(normalized.email),
      department: normalized.department == null ? '' : String(normalized.department),
      attendanceStatus: normalized.attendanceStatus === '' || normalized.attendanceStatus == null ? null : String(normalized.attendanceStatus),
      checkInTime: normalized.checkInTime === '' || normalized.checkInTime == null ? null : String(normalized.checkInTime),
      avatarSeed: normalized.avatarSeed === '' || normalized.avatarSeed == null ? null : String(normalized.avatarSeed),
    }
    return { employee, row: index + 2 }
  })
}

async function upsertEmployee(employee) {
  const update = await employeeRequest(`/employees/${encoded(employee.id)}`, 'PUT', employee)
  if (update.response.ok) return 'updated'
  if (update.response.status !== 404) throw new Error(importError(update.response, update.data))

  const create = await employeeRequest('/employees', 'POST', employee)
  if (create.response.ok) return 'created'
  throw new Error(importError(create.response, create.data))
}

const collection = name => ({
  list: async includeInactive => arrayResponse(await request(`/${name}?include_inactive=${includeInactive}`), `/${name}`),
  create: async body => objectResponse(await request(`/${name}`, { method: 'POST', body: JSON.stringify(body) }), `/${name}`),
  update: async (id, body) => objectResponse(await request(`/${name}/${encoded(id)}`, { method: 'PUT', body: JSON.stringify(body) }), `/${name}/${id}`),
  deactivate: async id => objectResponse(await request(`/${name}/${encoded(id)}/deactivate`, { method: 'POST' }), `/${name}/${id}/deactivate`),
  restore: async id => objectResponse(await request(`/${name}/${encoded(id)}/restore`, { method: 'POST' }), `/${name}/${id}/restore`),
})

export const api = {
  auth: {
    login: body => objectResponse(authRequest('/login', { method: 'POST', body: JSON.stringify(body) }), '/auth/login'),
    logout: () => authRequest('/logout', { method: 'POST' }),
    me: () => objectResponse(authRequest('/me'), '/auth/me'),
    changePassword: body => authRequest('/change-password', { method: 'POST', body: JSON.stringify(body) }),
  },
  employees: {
    ...collection('employees'),
    importFile: async file => {
      const rows = await employeeRowsFromFile(file)
      const result = { created: 0, updated: 0, failed: 0, errors: [] }

      for (const { employee, row } of rows) {
        if (!employee.id) {
          result.failed += 1
          result.errors.push(`Row ${row}: Employee ID is required.`)
          continue
        }
        try {
          result[await upsertEmployee(employee)] += 1
        } catch (error) {
          result.failed += 1
          result.errors.push(`Row ${row} (${employee.id}): ${error.message}`)
        }
      }
      return result
    },
  },
  categories: collection('categories'),
  presets: {
    ...collection('presets'),
    list: async includeInactive => arrayResponse(await request(`/presets?include_inactive=${includeInactive}`), '/presets'),
  },
  logs: {
    list: async () => arrayResponse(await request('/interaction-logs'), '/interaction-logs'),
    updateStatus: async (id, status, remarks) => objectResponse(await request(`/interaction-logs/${id}`, { method: 'PUT', body: JSON.stringify({ status, remarks }) }), `/interaction-logs/${id}`),
    getHistory: async id => arrayResponse(await request(`/interaction-logs/${id}/history`), `/interaction-logs/${id}/history`),
  },
  adminConfig: {
    get: async () => objectResponse(await request('/admin-config'), '/admin-config', true),
    create: async body => objectResponse(await request('/admin-config', { method: 'POST', body: JSON.stringify(body) }), '/admin-config'),
    update: async body => objectResponse(await request('/admin-config', { method: 'PUT', body: JSON.stringify(body) }), '/admin-config'),
  },
  translate: async (text, target) => objectResponse(await request('/translate', { method: 'POST', body: JSON.stringify({ text, target }) }), '/translate'),
}
