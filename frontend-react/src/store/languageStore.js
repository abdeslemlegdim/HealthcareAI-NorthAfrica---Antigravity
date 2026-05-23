import { create } from "zustand";

const getInitialLanguage = () => {
  const fromStorage = localStorage.getItem("language");
  if (fromStorage === "en" || fromStorage === "fr" || fromStorage === "ar") {
    return fromStorage;
  }
  return "en";
};

export const useLanguageStore = create((set) => ({
  language: getInitialLanguage(),
  setLanguage: (lang) => {
    if (lang !== "en" && lang !== "fr" && lang !== "ar") return;
    localStorage.setItem("language", lang);
    set({ language: lang });
  }
}));
