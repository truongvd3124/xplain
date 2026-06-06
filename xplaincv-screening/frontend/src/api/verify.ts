import { postForm } from './client'
import type { VerifyResponse } from './types'

export const verifyImage = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return postForm<VerifyResponse>('/api/verify', form)
}
