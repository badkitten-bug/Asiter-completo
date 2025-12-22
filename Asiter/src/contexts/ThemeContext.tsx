"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";

export type ThemeColor = "blue" | "green" | "purple" | "orange" | "red";

interface ThemeContextType {
  themeColor: ThemeColor;
  setThemeColor: (color: ThemeColor) => void;
  getThemeClasses: () => {
    primary: string;
    hover: string;
    border: string;
    text: string;
    bg: string;
  };
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const themeClasses: Record<ThemeColor, {
  primary: string;
  hover: string;
  border: string;
  text: string;
  bg: string;
}> = {
  blue: {
    primary: "bg-blue-600",
    hover: "hover:bg-blue-700",
    border: "border-blue-600",
    text: "text-blue-600",
    bg: "bg-blue-50",
  },
  green: {
    primary: "bg-green-600",
    hover: "hover:bg-green-700",
    border: "border-green-600",
    text: "text-green-600",
    bg: "bg-green-50",
  },
  purple: {
    primary: "bg-purple-600",
    hover: "hover:bg-purple-700",
    border: "border-purple-600",
    text: "text-purple-600",
    bg: "bg-purple-50",
  },
  orange: {
    primary: "bg-orange-600",
    hover: "hover:bg-orange-700",
    border: "border-orange-600",
    text: "text-orange-600",
    bg: "bg-orange-50",
  },
  red: {
    primary: "bg-red-600",
    hover: "hover:bg-red-700",
    border: "border-red-600",
    text: "text-red-600",
    bg: "bg-red-50",
  },
};

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [themeColor, setThemeColorState] = useState<ThemeColor>("blue");

  useEffect(() => {
    // Cargar tema guardado
    const savedTheme = localStorage.getItem("asiter-theme") as ThemeColor;
    if (savedTheme && themeClasses[savedTheme]) {
      setThemeColorState(savedTheme);
    }
  }, []);

  const setThemeColor = (color: ThemeColor) => {
    setThemeColorState(color);
    localStorage.setItem("asiter-theme", color);
  };

  const getThemeClasses = () => themeClasses[themeColor];

  return (
    <ThemeContext.Provider value={{ themeColor, setThemeColor, getThemeClasses }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}

