const Loader = ({ label = "Loading...", size = "md" }) => {
  const sizes = {
    sm: "h-4 w-4 border-2",
    md: "h-8 w-8 border-[3px]",
    lg: "h-12 w-12 border-4"
  };

  return (
    <div className="flex flex-col items-center justify-center gap-3 text-slate-300">
      <span
        className={`inline-block animate-spin rounded-full border-teal-400 border-t-transparent shadow-[0_0_24px_rgba(45,212,191,0.25)] ${sizes[size]}`}
      />
      <p className="text-sm font-medium tracking-wide">{label}</p>
    </div>
  );
};

export default Loader;
