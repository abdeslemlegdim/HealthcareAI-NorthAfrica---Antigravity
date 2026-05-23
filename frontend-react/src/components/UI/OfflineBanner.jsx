import { WifiOff } from "lucide-react";
import { useRuntime } from "../../context/RuntimeContext";

const OfflineBanner = () => {
  const { isOffline } = useRuntime();

  if (!isOffline) return null;

  return (
    <div className="sticky top-16 z-50 mx-auto mt-2 w-[calc(100%-1.5rem)] max-w-7xl rounded-2xl border border-amber-200 bg-amber-50 px-4 py-2 text-sm font-semibold text-amber-800 shadow-sm dark:border-amber-900 dark:bg-amber-950/50 dark:text-amber-300">
      <span className="inline-flex items-center gap-2">
        <WifiOff size={16} /> You are offline. Some actions may fail until connection is restored.
      </span>
    </div>
  );
};

export default OfflineBanner;
