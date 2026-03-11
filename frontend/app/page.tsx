import CrimeExplorer from "@/components/crime-explorer";

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero-band">
        <p className="eyebrow">Metro Boston Crime Atlas</p>
        <div className="hero-grid">
          <div className="hero-copy-block">
            <h1>Crime intensity across metropolitan Boston, not another dashboard skin.</h1>
          </div>
          <div className="hero-side">
            <p className="hero-copy">
              Official police feeds and census-normalized neighborhood rates, rendered in a browser
              map stack that behaves like a real spatial product.
            </p>
            <p className="hero-note">
              Compare municipalities, shift crime families, tighten the date window, and read the
              pattern directly off the map.
            </p>
          </div>
        </div>
      </section>
      <CrimeExplorer />
    </main>
  );
}
