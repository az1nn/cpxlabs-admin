export type ApiErrorCode =
  | 'validation'
  | 'authentication'
  | 'authorization'
  | 'not_found'
  | 'conflict'
  | 'rate_limit'
  | 'infrastructure'
  | 'unknown'
  | 'AUTHENTICATION_REQUIRED'
  | 'ACCESS_DISABLED'
  | 'FORBIDDEN'
  | 'WORKFLOW_INVALID_TRANSITION'
  | 'WORKFLOW_CONFLICT'

export type ApiErrorBody = {
  code: ApiErrorCode
  message: string
  details?: unknown
  requestId?: string
}

export type ApiErrorEnvelope = {
  error: ApiErrorBody
}
