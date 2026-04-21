"use client";

import { useSession, signOut } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Loader2, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function OnboardingPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [organization, setOrganization] = useState("");
  const [role, setRole] = useState("analyst");
  const [gender, setGender] = useState("");
  const [dob, setDob] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/auth/signin");
    }
  }, [status, router]);

  const handleComplete = async () => {
    setLoading(true);
    try {
      const userProfile = {
        gender,
        dob,
        organization,
        role,
      };
      localStorage.setItem("userProfile", JSON.stringify(userProfile));
      router.push("/dashboard");
    } finally {
      setLoading(false);
    }
  };

  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orange-50 via-white to-sky-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-900">
        <Loader2 className="w-8 h-8 animate-spin text-orange-600" />
      </div>
    );
  }

  if (!session?.user) {
    return null;
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-orange-50 via-white to-sky-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-900">
      <div className="orb left-[-180px] top-[-120px] h-[340px] w-[340px] bg-orange-400/20 dark:bg-orange-400/5" />
      <div className="orb right-[-120px] bottom-[10%] h-[260px] w-[260px] bg-sky-300/25 dark:bg-sky-300/5" />

      <div className="fixed top-0 left-0 right-0 h-1 bg-gradient-to-r from-orange-400 via-amber-400 to-orange-500 z-50" />

      <div className="relative z-10 flex items-center justify-center min-h-screen px-4">
        <div className="w-full max-w-2xl">
          <div className="flex items-center justify-between mb-12">
            <div>
              <h1 className="mb-2 text-4xl font-bold text-slate-900 dark:text-white">
                Welcome, {session.user.name}! 👋
              </h1>
              <p className="text-lg text-slate-600 dark:text-slate-400">
                Let&apos;s set up your SafeGuard profile
              </p>
            </div>
            <button
              onClick={() => signOut({ callbackUrl: "/" })}
              className="text-sm font-semibold text-slate-600 transition hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
            >
              Sign Out
            </button>
          </div>

          <div className="grid md:grid-cols-2 gap-6 mb-8">
            <div className="glass rounded-3xl border border-white/80 p-8 dark:border-slate-700/60 dark:bg-slate-800/50">
              <h2 className="mb-6 text-xl font-bold text-slate-900 dark:text-white">Profile</h2>

              <div className="space-y-5">
                <div className="flex items-center gap-4">
                  {session.user.image && (
                    <img
                      src={session.user.image}
                      alt={session.user.name || "User"}
                      className="h-16 w-16 rounded-full border-2 border-orange-400"
                    />
                  )}
                  <div>
                    <p className="font-semibold text-slate-900 dark:text-white">
                      {session.user.name}
                    </p>
                    <p className="text-sm text-slate-600 dark:text-slate-400">{session.user.email}</p>
                  </div>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-900 dark:text-slate-200">
                    Gender
                  </label>
                  <select
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                    className="w-full rounded-xl border border-slate-300 bg-white/70 px-4 py-2 text-slate-900 transition focus:border-orange-400 focus:outline-none focus:ring-2 focus:ring-orange-400/20 dark:border-slate-600 dark:bg-slate-800/70 dark:text-slate-100"
                  >
                    <option value="">Select Gender</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                    <option value="prefer-not-to-say">Prefer not to say</option>
                  </select>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-900 dark:text-slate-200">
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    value={dob}
                    onChange={(e) => setDob(e.target.value)}
                    className="w-full rounded-xl border border-slate-300 bg-white/70 px-4 py-2 text-slate-900 placeholder-slate-500 transition focus:border-orange-400 focus:outline-none focus:ring-2 focus:ring-orange-400/20 dark:border-slate-600 dark:bg-slate-800/70 dark:text-slate-100 dark:placeholder-slate-400"
                  />
                </div>
              </div>
            </div>

            <div className="glass rounded-3xl border border-white/80 p-8 dark:border-slate-700/60 dark:bg-slate-800/50">
              <h2 className="mb-6 text-xl font-bold text-slate-900 dark:text-white">
                Organization
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-900 dark:text-slate-200">
                    Organization Name
                  </label>
                  <input
                    type="text"
                    value={organization}
                    onChange={(e) => setOrganization(e.target.value)}
                    placeholder="e.g., NGO, School, Police Department"
                    className="w-full rounded-xl border border-slate-300 bg-white/70 px-4 py-2 text-slate-900 placeholder-slate-500 transition focus:border-orange-400 focus:outline-none focus:ring-2 focus:ring-orange-400/20 dark:border-slate-600 dark:bg-slate-800/70 dark:text-slate-100 dark:placeholder-slate-400"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-900 dark:text-slate-200">
                    Your Role
                  </label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    className="w-full rounded-xl border border-slate-300 bg-white/70 px-4 py-2 text-slate-900 transition focus:border-orange-400 focus:outline-none focus:ring-2 focus:ring-orange-400/20 dark:border-slate-600 dark:bg-slate-800/70 dark:text-slate-100"
                  >
                    <option value="analyst">Safety Analyst</option>
                    <option value="reviewer">Content Reviewer</option>
                    <option value="admin">Administrator</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          <div className="glass mb-8 rounded-3xl border border-white/80 p-8 dark:border-slate-700/60 dark:bg-slate-800/50">
            <h2 className="mb-6 text-xl font-bold text-slate-900 dark:text-white">
              What you can do
            </h2>

            <div className="grid md:grid-cols-2 gap-6">
              {[
                {
                  icon: "📋",
                  title: "Analyze Content",
                  desc: "Scan text, images, and conversations for harmful content in real-time",
                },
                {
                  icon: "⚖️",
                  title: "Legal Mapping",
                  desc: "Automatically map incidents to relevant Indian laws and sections",
                },
                {
                  icon: "📊",
                  title: "Analytics Dashboard",
                  desc: "Track patterns, trends, and case progression over time",
                },
                {
                  icon: "🔐",
                  title: "Secure Reports",
                  desc: "Generate legally valid FIR reports with evidence preservation",
                },
              ].map((feature, i) => (
                <div key={i} className="flex gap-4">
                  <span className="text-3xl">{feature.icon}</span>
                  <div>
                    <h3 className="font-semibold text-slate-900 dark:text-white">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-slate-600 dark:text-slate-400">{feature.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4">
            <button
              onClick={handleComplete}
              disabled={loading || !organization || !gender || !dob}
              className="flex-1 inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-orange-600 to-amber-500 px-6 py-3 text-sm font-bold text-white shadow-[0_16px_30px_rgba(249,115,22,0.3)] transition hover:translate-y-[-1px] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Setting up...
                </>
              ) : (
                <>
                  Get Started
                  <ArrowRight size={16} />
                </>
              )}
            </button>

            <Link
              href="/auth/signin"
              onClick={() => signOut({ callbackUrl: "/" })}
              className="flex-1 inline-flex items-center justify-center gap-2 rounded-2xl border border-slate-300 bg-white/75 px-6 py-3 text-sm font-semibold text-slate-700 transition hover:bg-white dark:border-slate-600 dark:bg-slate-800/60 dark:text-slate-300 dark:hover:bg-slate-700"
            >
              Use Different Account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
