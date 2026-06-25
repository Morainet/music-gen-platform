import { useEffect, useState } from "react";

export type Theme = "dark" | "light";

function current(): Theme {
  return document.documentElement.classList.contains("dark")
    ? "dark"
    : "light";
}

function apply(theme: Theme) {
  document.documentElement.classList.toggle("dark", theme === "dark");
  localStorage.setItem("theme", theme);
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(current);

  useEffect(() => {
    apply(theme);
  }, [theme]);

  const toggle = () =>
    setTheme((t) => (t === "dark" ? "light" : "dark"));

  return { theme, toggle };
}
