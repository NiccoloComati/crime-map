import CrimeExplorer from "@/components/crime-explorer";

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero-band">
        <p className="eyebrow">Metro Crime Atlas</p>
        <div className="hero-grid">
          <div className="hero-copy-block">
            <h1>Neighborhood crime rates, mapped without the clutter.</h1>
          </div>
          <div className="hero-side">
            <p className="hero-copy">
              Official Police and Census data.<br />
              Population-adjusted rates.<br />
              Clearly-ranked neighborhoods.
            </p>
          </div>
        </div>
      </section>
      <CrimeExplorer />
    </main>
  );
}
