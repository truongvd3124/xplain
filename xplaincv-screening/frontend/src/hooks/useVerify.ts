import { useMutation } from '@tanstack/react-query'
import { verifyImage } from '../api/verify'

export const useVerify = () =>
  useMutation({ mutationFn: (file: File) => verifyImage(file) })
