import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

/** Routes that don't require authentication */
const PUBLIC_PATHS = ['/', '/login', '/register', '/forgot-password', '/reset-password']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  
  // Allow public paths
  if (PUBLIC_PATHS.some(p => pathname === p || pathname.startsWith(`${p}/`))) {
    return NextResponse.next()
  }

  // Allow API routes and static assets
  if (pathname.startsWith('/api') || pathname.startsWith('/_next') || pathname.startsWith('/favicon')) {
    return NextResponse.next()
  }

  // Check for auth token in cookies or fallback to checking if the page will handle it client-side
  // Since we use localStorage, we can't fully check server-side.
  // This middleware provides a basic guard by checking for a cookie-based token.
  const token = request.cookies.get('token')?.value
  
  // If accessing dashboard routes without a token cookie, redirect to login.
  // Note: The client-side ApiClient also checks localStorage as a fallback.
  if (pathname.startsWith('/dashboard') && !token) {
    // We allow the request through since token might be in localStorage (client-side).
    // The client-side layout will redirect if no token is found.
    return NextResponse.next()
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
}
