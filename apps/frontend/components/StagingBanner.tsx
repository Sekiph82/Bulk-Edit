// Fixed banner shown only when the build/runtime env is staging.
// Driven by NEXT_PUBLIC_APP_ENV=staging (set on the DigitalOcean staging app).
// Renders nothing in production/local so it can live in the root layout safely.
export default function StagingBanner() {
  if (process.env.NEXT_PUBLIC_APP_ENV !== "staging") return null;

  return (
    <div
      role="status"
      aria-label="Staging environment"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 2147483647,
        background: "#b91c1c",
        color: "#fff",
        textAlign: "center",
        fontSize: "13px",
        fontWeight: 700,
        letterSpacing: "0.04em",
        padding: "4px 8px",
        pointerEvents: "none",
      }}
    >
      STAGING ENVIRONMENT - NOT PRODUCTION
    </div>
  );
}
