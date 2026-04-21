import { withAuth } from "next-auth/middleware";
import { NextResponse } from "next/server";

export const middleware = withAuth(
  function middleware(req) {
    if (
      req.nextUrl.pathname === "/" ||
      req.nextUrl.pathname.startsWith("/auth/")
    ) {
      return NextResponse.next();
    }

    if (
      req.nextUrl.pathname.startsWith("/dashboard") ||
      req.nextUrl.pathname.startsWith("/analytics") ||
      req.nextUrl.pathname.startsWith("/onboarding")
    ) {
      return NextResponse.next();
    }

    return NextResponse.next();
  },
  {
    callbacks: {
      authorized: ({ token, req }) => {
        if (
          req.nextUrl.pathname === "/" ||
          req.nextUrl.pathname.startsWith("/auth/")
        ) {
          return true;
        }

        if (
          req.nextUrl.pathname.startsWith("/dashboard") ||
          req.nextUrl.pathname.startsWith("/analytics") ||
          req.nextUrl.pathname.startsWith("/onboarding")
        ) {
          return !!token;
        }

        return true;
      },
    },
    pages: {
      signIn: "/auth/signin",
    },
  }
);

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|api/auth).*)",
  ],
};
