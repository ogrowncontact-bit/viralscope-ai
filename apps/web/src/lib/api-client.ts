import { env } from '@/lib/env';

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

interface ApiFetchOptions extends RequestInit {
  token?: string | null;
}

export async function apiFetch<TResponse>(
  path: string,
  { token, headers, ...init }: ApiFetchOptions = {},
): Promise<TResponse> {
  const response = await fetch(`${env.NEXT_PUBLIC_API_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  if (!response.ok) {
    const detail = await extractErrorDetail(response);
    throw new ApiError(
      detail ?? `Falha ao chamar ${path}: ${response.statusText}`,
      response.status,
    );
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }

  return response.json() as Promise<TResponse>;
}

function hasStringDetail(body: unknown): body is { detail: string } {
  return (
    typeof body === 'object' &&
    body !== null &&
    'detail' in body &&
    typeof (body as Record<string, unknown>).detail === 'string'
  );
}

async function extractErrorDetail(response: Response): Promise<string | null> {
  try {
    const body: unknown = await response.json();
    return hasStringDetail(body) ? body.detail : null;
  } catch {
    return null;
  }
}
