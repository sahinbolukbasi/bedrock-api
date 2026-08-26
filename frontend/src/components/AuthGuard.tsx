"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getAuthToken } from "../lib/api";
import { Loader2 } from "lucide-react";

interface AuthGuardProps {
  children: React.ReactNode;
  adminOnly?: boolean;
}

export default function AuthGuard({ children, adminOnly = false }: AuthGuardProps) {
  const router = useRouter();
  const [authorized, setAuthorized] = useState<boolean>(false);

  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      router.replace("/login");
      return;
    }

    if (adminOnly) {
      const userRaw = localStorage.getItem("bedrock_gateway_user");
      if (userRaw) {
        try {
          const user = JSON.parse(userRaw);
          if (user.role !== "admin") {
            router.replace("/chat");
            return;
          }
        } catch {
          // ignore
        }
      }
    }

    setAuthorized(true);
  }, [router, adminOnly]);

  if (!authorized) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center gap-3">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
        <span className="text-sm text-gray-400 font-medium">Verifying authorization...</span>
      </div>
    );
  }

  return <>{children}</>;
}
