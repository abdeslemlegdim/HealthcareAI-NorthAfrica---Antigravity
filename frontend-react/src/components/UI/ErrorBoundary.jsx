import React from "react";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, message: "" };
  }

  handleRetry = () => {
    this.setState({ hasError: false, message: "" });
  };

  static getDerivedStateFromError(error) {
    return {
      hasError: true,
      message: error?.message || "Unexpected UI error"
    };
  }

  componentDidCatch(error, errorInfo) {
    // Keep diagnostic details in console for debugging without crashing to a blank page.
    // eslint-disable-next-line no-console
    console.error("UI runtime error:", error, errorInfo);
  }

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <div className="mx-auto mt-8 max-w-2xl rounded-3xl border border-red-400/20 bg-slate-950/85 p-6 text-red-100 shadow-[0_24px_80px_rgba(0,0,0,0.4)] backdrop-blur-2xl">
        <h2 className="text-lg font-bold">Something went wrong on this screen</h2>
        <p className="mt-2 text-sm text-red-100/80">The interface recovered safely, but this section needs a retry.</p>
        <p className="mt-2 rounded-2xl border border-white/10 bg-white/5 p-3 text-xs text-slate-200">{this.state.message}</p>
        <div className="mt-4 flex gap-2">
          <button
            type="button"
            onClick={this.handleRetry}
            className="rounded-xl bg-gradient-to-r from-red-500 to-rose-600 px-4 py-2 text-sm font-semibold text-white transition hover:scale-[1.01]"
          >
            Retry
          </button>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-slate-100 transition hover:bg-white/10"
          >
            Hard Reload
          </button>
        </div>
      </div>
    );
  }
}

export default ErrorBoundary;
