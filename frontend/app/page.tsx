import CrimeExplorer from "@/components/crime-explorer";

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero-band">
        <p className="eyebrow">Metro Crime Atlas</p>
        <div className="hero-grid">
          <div className="hero-copy-block">
            <h1>Neighborhood crime rates, mapped without the dashboard clutter.</h1>
          </div>
          <div className="hero-side">
            <p className="hero-copy">
              Official police data. Population-normalized rates. A map first, everything else
              second.
            </p>
            <p className="hero-note">
              Pick an area. Pick a crime type. Tighten the dates. The pattern should be visible
              without explanation.
            </p>
          </div>
        </div>
      </section>
      <CrimeExplorer />
    </main>
  );
}
