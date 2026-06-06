export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function parseError(res: Response): Promise<never> {
  let message = `${res.status} ${res.statusText}`
  try {
    const body = await res.json()
    if (typeof body.detail === 'string') message = body.detail
  } catch {
    /* keep default message */
  }
  throw new ApiError(res.status, message)
}

export async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) return parseError(res)
  return res.json()
}

export async function postJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) return parseError(res)
  return res.json()
}

export async function postForm<T>(url: string, form: FormData): Promise<T> {
  const res = await fetch(url, { method: 'POST', body: form })
  if (!res.ok) return parseError(res)
  return res.json()
}

export async function del(url: string): Promise<void> {
  const res = await fetch(url, { method: 'DELETE' })
  if (!res.ok) return parseError(res)
}
