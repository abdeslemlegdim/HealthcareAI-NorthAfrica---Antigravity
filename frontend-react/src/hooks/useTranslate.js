import en from "../locales/en.json";
import fr from "../locales/fr.json";
import ar from "../locales/ar.json";
import { useLanguageStore } from "../store/languageStore";

const translations = { en, fr, ar };

export const useTranslate = () => {
  const { language } = useLanguageStore();

  return (key, values = {}) => {
    const table = translations[language] || translations.en;
    const template = table[key] || translations.en[key] || key;

    if (typeof template !== "string") {
      return String(template);
    }

    return template.replace(/\{\{\s*([\w.-]+)\s*\}\}/g, (_, name) => {
      const value = values?.[name];
      return value === null || value === undefined ? "" : String(value);
    });
  };
};
