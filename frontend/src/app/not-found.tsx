"use client";

import React from "react";
import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-[calc(100vh-64px)] flex flex-col items-center justify-center p-6 text-center">
      <div className="w-16 h-16 rounded-3xl bg-indigo-600/10 border border-indigo-500/30 flex items-center justify-center text-2xl font-black text-indigo-600 mb-4">
        404
      </div>
      <h1 className="text-xl font-black text-slate-900 dark:text-white mb-2">
        Sayfa Bulunamadı
      </h1>
      <p className="text-xs text-slate-500 dark:text-gray-400 mb-6 max-w-sm">
        Aradığınız sayfa taşınmış veya kaldırılmış olabilir. Ana sayfaya veya Sohbet Studio'ya dönebilirsiniz.
      </p>
      <Link
        href="/"
        className="px-5 py-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition"
      >
        ← Ana Ekrana Dön
      </Link>
    </div>
  );
}
