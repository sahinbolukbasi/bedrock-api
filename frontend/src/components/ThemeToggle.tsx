"use client";

import React from "react";
import { Sun, Moon } from "lucide-react";
import { useTheme } from "./ThemeProvider";

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
      className="p-2 rounded-lg border transition text-gray-400 hover:text-gray-200 bg-gray-900/60 border-gray-800 hover:bg-gray-800 dark:bg-gray-900/60 dark:border-gray-800 dark:hover:bg-gray-800 light:bg-gray-100 light:border-gray-200 light:text-gray-700 light:hover:bg-gray-200"
    >
      {theme === "dark" ? (
        <Sun className="w-4 h-4 text-amber-400" />
      ) : (
        <Moon className="w-4 h-4 text-indigo-600" />
      )}
    </button>
  );
}
