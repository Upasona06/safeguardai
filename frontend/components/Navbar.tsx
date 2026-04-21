"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, Menu, ShieldCheck, X, Settings, Moon, Sun } from "lucide-react";
import { useSession, signOut } from "next-auth/react";
import { useTheme } from "@/hooks/useTheme";

const links = [
  { href: "#features", label: "Capabilities" },
  { href: "#how-it-works", label: "Workflow" },
  { href: "#demo", label: "Live Demo" },
  { href: "/analytics", label: "Analytics" },
];

export default function Navbar() {
  const { data: session, status } = useSession();
  const { theme, toggleTheme, mounted } = useTheme();
  const [menuOpen, setMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 28);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav className="fixed inset-x-0 top-0 z-50 px-4 pt-4 md:px-8">
      <div
        className={`mx-auto flex max-w-7xl items-center justify-between rounded-2xl border px-4 py-3 transition-all duration-300 md:px-6 ${
          scrolled
            ? "glass border-slate-300/60 shadow-[0_16px_40px_rgba(31,41,55,0.12)]"
            : "border-transparent bg-transparent"
        }`}
      >
        <Link href="/" className="flex items-center gap-3">
          <div className="hero-ring">
            <div className="flex h-9 w-9 items-center justify-center">
              <ShieldCheck size={18} className="text-orange-600" />
            </div>
          </div>
          <span className="text-[15px] font-bold tracking-tight text-slate-900 dark:text-white md:text-base">
            Safe<span className="gradient-text">Guard</span> AI
          </span>
        </Link>

        <div className="hidden items-center gap-1 rounded-full border border-slate-300/60 dark:border-slate-600/40 bg-white/55 dark:bg-slate-800/40 p-1.5 backdrop-blur md:flex">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-full px-4 py-2 text-xs font-semibold tracking-wide text-slate-600 dark:text-slate-400 transition hover:bg-white dark:hover:bg-slate-700 hover:text-slate-900 dark:hover:text-white"
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className="hidden items-center gap-3 md:flex">
          <button
            onClick={toggleTheme}
            className="rounded-full p-2 text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            aria-label="Toggle dark mode"
          >
            {mounted && (
              theme === "light" ? <Moon size={18} /> : <Sun size={18} />
            )}
          </button>
          {status === "authenticated" && session?.user ? (
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-orange-600 to-amber-500 p-0.5"
              >
                {session.user.image ? (
                  <img
                    src={session.user.image}
                    alt={session.user.name || "User"}
                    className="h-8 w-8 rounded-full"
                  />
                ) : (
                  <div className="h-8 w-8 rounded-full bg-orange-400 flex items-center justify-center text-white text-xs font-bold">
                    {session.user.name?.charAt(0).toUpperCase() || "U"}
                  </div>
                )}
              </button>

              {userMenuOpen && (
                <div className="absolute right-0 mt-2 w-56 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-lg dark:border-slate-700 dark:bg-slate-900">
                  <div className="border-b border-slate-200 p-4 dark:border-slate-700">
                    <p className="text-sm font-semibold text-slate-900 dark:text-white">
                      {session.user.name}
                    </p>
                    <p className="text-xs text-slate-600 dark:text-slate-400">{session.user.email}</p>
                  </div>
                  <div className="p-2 space-y-1">
                    <Link
                      href="/dashboard"
                      className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-700 transition hover:bg-orange-50 dark:text-slate-300 dark:hover:bg-slate-800"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      <span>📊</span> Dashboard
                    </Link>
                    <button
                      className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-700 transition hover:bg-orange-50 dark:text-slate-300 dark:hover:bg-slate-800"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      <Settings size={14} /> Settings
                    </button>
                    <button
                      onClick={() => {
                        setUserMenuOpen(false);
                        signOut({ callbackUrl: "/" });
                      }}
                      className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-red-600 transition hover:bg-red-50 dark:hover:bg-red-950/30"
                    >
                      <span>🚪</span> Sign Out
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <>
              <Link
                href="/auth/signin"
                className="rounded-full border border-slate-300 dark:border-slate-600 bg-white/75 dark:bg-slate-800/60 px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-300 transition hover:border-slate-400 dark:hover:border-slate-500 hover:bg-white dark:hover:bg-slate-700"
              >
                Sign In
              </Link>
              <Link
                href="/auth/signup"
                className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-orange-600 to-amber-500 px-4 py-2 text-xs font-bold text-white shadow-[0_10px_24px_rgba(249,115,22,0.35)] transition hover:scale-[1.02]"
              >
                Get Started
                <ArrowUpRight size={14} />
              </Link>
            </>
          )}
        </div>

        <button
          type="button"
          className="rounded-xl border border-slate-300 bg-white/80 p-2 text-slate-700 md:hidden dark:border-slate-600 dark:bg-slate-800/70 dark:text-slate-300"
          onClick={() => setMenuOpen((open) => !open)}
          aria-label="Toggle navigation menu"
        >
          {menuOpen ? <X size={19} /> : <Menu size={19} />}
        </button>
      </div>

      {menuOpen && (
        <div className="mx-auto mt-3 max-w-7xl rounded-2xl border border-slate-300/70 bg-white/95 dark:bg-slate-900/95 dark:border-slate-700/70 p-4 shadow-[0_20px_50px_rgba(30,41,59,0.18)] dark:shadow-[0_20px_50px_rgba(0,0,0,0.3)] backdrop-blur">
          <div className="flex justify-between items-center mb-3 pb-3 border-b border-slate-200 dark:border-slate-700">
            <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">Theme</span>
            <button
              onClick={toggleTheme}
              className="rounded-full p-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
              aria-label="Toggle dark mode"
            >
              {mounted && (
                theme === "light" ? <Moon size={18} /> : <Sun size={18} />
              )}
            </button>
          </div>
          <div className="flex flex-col gap-1">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="rounded-xl px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                onClick={() => setMenuOpen(false)}
              >
                {link.label}
              </Link>
            ))}
            <div className="my-2 border-t border-slate-200 dark:border-slate-700" />
            {status === "authenticated" && session?.user ? (
              <>
                <div className="mb-1 px-3 py-2 text-sm font-semibold text-slate-900 dark:text-white">
                  {session.user.name}
                </div>
                <Link
                  href="/dashboard"
                  className="block rounded-xl px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                  onClick={() => setMenuOpen(false)}
                >
                  Dashboard
                </Link>
                <button
                  onClick={() => {
                    setMenuOpen(false);
                    signOut({ callbackUrl: "/" });
                  }}
                  className="w-full rounded-xl px-3 py-2 text-left text-sm font-medium text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30"
                >
                  Sign Out
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/auth/signin"
                  className="block rounded-xl px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                  onClick={() => setMenuOpen(false)}
                >
                  Sign In
                </Link>
                <Link
                  href="/auth/signup"
                  className="mt-2 rounded-xl bg-gradient-to-r from-orange-600 to-amber-500 px-3 py-2 text-center text-sm font-semibold text-white"
                  onClick={() => setMenuOpen(false)}
                >
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
