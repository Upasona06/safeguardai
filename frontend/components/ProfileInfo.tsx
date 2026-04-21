"use client";

import { useSession } from "next-auth/react";

interface ProfileInfoProps {
  compact?: boolean;
}

export default function ProfileInfo({ compact = false }: ProfileInfoProps) {
  const { data: session } = useSession();

  if (!session?.user) return null;

  if (compact) {
    return (
      <div className="glass rounded-2xl border border-white/80 p-4 md:min-w-fit dark:border-slate-700/60 dark:bg-slate-800/50">
        <div className="flex items-center gap-3">
          <div className="relative">
            {session.user.image ? (
              <img
                src={session.user.image}
                alt={session.user.name || "User"}
                className="h-10 w-10 rounded-full border-2 border-orange-400 object-cover"
              />
            ) : (
              <div className="h-10 w-10 rounded-full border-2 border-orange-400 bg-gradient-to-br from-orange-400 to-amber-500 flex items-center justify-center text-white text-xs font-bold">
                {session.user.name?.charAt(0).toUpperCase() || "U"}
              </div>
            )}
          </div>
          <div className="text-sm">
            <p className="font-semibold text-slate-900 dark:text-white">{session.user.name}</p>
            <p className="text-xs text-slate-600 dark:text-slate-400">{session.user.email}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass rounded-3xl border border-white/80 p-6 md:p-8 dark:border-slate-700/60 dark:bg-slate-800/50">
      <h2 className="mb-6 text-xl font-bold text-slate-900 dark:text-white">Profile Information</h2>

      <div className="space-y-6">
        <div className="flex items-center gap-4 border-b border-slate-200 pb-6 dark:border-slate-700">
          <div className="relative">
            {session.user.image ? (
              <img
                src={session.user.image}
                alt={session.user.name || "User"}
                className="h-20 w-20 rounded-full border-2 border-orange-400 object-cover"
              />
            ) : (
              <div className="h-20 w-20 rounded-full border-2 border-orange-400 bg-gradient-to-br from-orange-400 to-amber-500 flex items-center justify-center text-white text-2xl font-bold">
                {session.user.name?.charAt(0).toUpperCase() || "U"}
              </div>
            )}
          </div>
          <div>
            <p className="text-lg font-bold text-slate-900 dark:text-white">{session.user.name}</p>
            <p className="text-sm text-slate-600 dark:text-slate-400">{session.user.email}</p>
          </div>
        </div>

      </div>
    </div>
  );
}
