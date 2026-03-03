import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./style.css";

class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error) {
    console.error("frontend render failed", error);
  }

  render() {
    if (this.state.error) {
      return (
        <div
          style={{
            maxWidth: "1120px",
            margin: "0 auto",
            padding: "24px 18px 56px",
            fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
          }}
        >
          <section
            style={{
              border: "1px solid rgba(15, 23, 42, 0.12)",
              borderRadius: "24px",
              background: "rgba(255, 255, 255, 0.92)",
              padding: "22px",
              boxShadow: "0 18px 48px rgba(15, 23, 42, 0.08)",
            }}
          >
            <p
              style={{
                display: "inline-flex",
                alignItems: "center",
                padding: "8px 12px",
                borderRadius: "999px",
                background: "rgba(220, 38, 38, 0.1)",
                color: "#dc2626",
                fontSize: "13px",
                fontWeight: 700,
                margin: 0,
              }}
            >
              Front-end fallback
            </p>
            <h1
              style={{
                margin: "12px 0 10px",
                fontFamily: '"Space Grotesk", "IBM Plex Sans", system-ui, sans-serif',
                fontSize: "clamp(2rem, 4vw, 3rem)",
                lineHeight: 1,
                letterSpacing: "-0.04em",
                color: "#0b1220",
              }}
            >
              The interactive console hit a render error.
            </h1>
            <p style={{ color: "#475467", lineHeight: 1.6, margin: 0 }}>
              Refresh the page or open the export summary path while the interactive surface recovers.
            </p>
          </section>
        </div>
      );
    }

    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AppErrorBoundary>
      <App />
    </AppErrorBoundary>
  </React.StrictMode>
);
