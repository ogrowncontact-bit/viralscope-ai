import { z } from 'zod';

const envSchema = z.object({
  NEXT_PUBLIC_API_URL: z.url(),
});

const parsed = envSchema.safeParse({
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
});

if (!parsed.success) {
  throw new Error(`Variáveis de ambiente inválidas ou ausentes: ${parsed.error.message}`);
}

export const env = parsed.data;
