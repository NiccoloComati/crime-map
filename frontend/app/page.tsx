import CrimeExplorer from "@/components/crime-explorer";

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero-card">
        <p className="eyebrow">Metro Boston Crime Atlas</p>
        <h1>Live municipal crime rates with an actual web map stack.</h1>
        <p className="hero-copy">
          The frontend is now separate from the data engine. Python handles ingestion and rate
          computation; the browser handles interaction and mapping.
        </p>
      </section>
      <CrimeExplorer />
    </main>
  );
}
