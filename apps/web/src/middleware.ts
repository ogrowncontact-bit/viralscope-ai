import { clerkMiddleware } from '@clerk/nextjs/server';

// Estabelece o contexto de autenticação para toda a aplicação. A proteção de rota em si
// é feita via `auth.protect()` dentro de cada layout/página protegida (padrão
// "resource-based auth" recomendado pela Clerk), não por path matching aqui.
export default clerkMiddleware();

export const config = {
  matcher: ['/((?!_next|.*\\..*).*)', '/(api|trpc)(.*)'],
};
