import { useEffect, useState } from "react";

export interface UserProfile {
  gender?: string;
  dob?: string;
  organization?: string;
  role?: string;
}

export function useUserProfile() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("userProfile");
      if (saved) {
        try {
          setProfile(JSON.parse(saved));
        } catch (error) {
          console.error("Failed to parse user profile:", error);
          setProfile(null);
        }
      }
      setLoading(false);
    }
  }, []);

  const updateProfile = (newProfile: Partial<UserProfile>) => {
    const updated = { ...profile, ...newProfile };
    setProfile(updated);
    if (typeof window !== "undefined") {
      localStorage.setItem("userProfile", JSON.stringify(updated));
    }
  };

  return { profile, loading, updateProfile };
}
