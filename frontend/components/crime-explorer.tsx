"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

import {
  ChoroplethPayload,
  MunicipalityMetadata,
  fetchMunicipalities,
  fetchMunicipalityChoropleth,
  fetchMunicipalityMetadata,
} from "@/lib/api";

const CrimeMap = dynamic(() => import("@/components/crime-map"), {
  ssr: false,
  loading: () => <div className="map-loading">Loading browser map...</div>,
});

export default function CrimeExplorer() {
  const [municipalities, setMunicipalities] = useState<string[]>([]);
  const [municipality, setMunicipality] = useState("");
  const [metadata, setMetadata] = useState<MunicipalityMetadata | null>(null);
  const [selectedMacro, setSelectedMacro] = useState("");
  const [startDate, setStartDate] = useState<string | null>(null);
  const [endDate, setEndDate] = useState<string | null>(null);
  const [payload, setPayload] = useState<ChoroplethPayload | null>(null);
  const [loadingMessage, setLoadingMessage] = useState("Loading municipalities...");
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadMunicipalities() {
      try {
        const nextMunicipalities = await fetchMunicipalities();
        if (cancelled) {
          return;
        }

        setMunicipalities(nextMunicipalities);
        setMunicipality(nextMunicipalities[0] ?? "");
        setError("");
      } catch (nextError) {
        if (cancelled) {
          return;
        }
        setError(nextError instanceof Error ? nextError.message : "Failed to load municipalities.");
      }
    }

    loadMunicipalities();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!municipality) {
      return;
    }

    let cancelled = false;
    setLoadingMessage("Loading municipality metadata...");

    async function loadMetadata() {
      try {
        const nextMetadata = await fetchMunicipalityMetadata(municipality);
        if (cancelled) {
          return;
        }

        setMetadata(nextMetadata);
        setSelectedMacro(nextMetadata.default_macro);
        setStartDate(nextMetadata.min_date);
        setEndDate(nextMetadata.max_date);
        setError("");
      } catch (nextError) {
        if (cancelled) {
          return;
        }
        setError(nextError instanceof Error ? nextError.message : "Failed to load municipality metadata.");
      }
    }

    loadMetadata();
    return () => {
      cancelled = true;
    };
  }, [municipality]);

  useEffect(() => {
    if (!municipality || !metadata || !selectedMacro || !startDate || !endDate) {
      return;
    }

    let cancelled = false;
    setLoadingMessage("Calculating rates and preparing map payload...");

    async function loadMap() {
      try {
        const nextPayload = await fetchMunicipalityChoropleth({
          municipality,
          macro: selectedMacro,
          startDate,
          endDate,
        });
        if (cancelled) {
          return;
        }

        setPayload(nextPayload);
        setError("");
      } catch (nextError) {
        if (cancelled) {
          return;
        }
        setError(nextError instanceof Error ? nextError.message : "Failed to load map payload.");
      }
    }

    loadMap();
    return () => {
      cancelled = true;
    };
  }, [municipality, metadata, selectedMacro, startDate, endDate]);

  return (
    <section className="explorer-shell">
      <div className="controls-grid">
        <div className="control">
          <label htmlFor="municipality">Municipality</label>
          <select
            id="municipality"
            value={municipality}
            onChange={(event) => setMunicipality(event.target.value)}
          >
            {municipalities.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>
        <div className="control">
          <label htmlFor="macro">Crime Macro</label>
          <select
            id="macro"
            value={selectedMacro}
            onChange={(event) => setSelectedMacro(event.target.value)}
            disabled={!metadata}
          >
            {(metadata?.macro_options ?? []).map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>
        <div className="control">
          <label htmlFor="start-date">Start Date</label>
          <input
            id="start-date"
            type="date"
            min={metadata?.min_date}
            max={metadata?.max_date}
            value={startDate ?? ""}
            onChange={(event) => setStartDate(event.target.value)}
            disabled={!metadata}
          />
        </div>
        <div className="control">
          <label htmlFor="end-date">End Date</label>
          <input
            id="end-date"
            type="date"
            min={metadata?.min_date}
            max={metadata?.max_date}
            value={endDate ?? ""}
            onChange={(event) => setEndDate(event.target.value)}
            disabled={!metadata}
          />
        </div>
      </div>

      <div className="stats-bar">
        <article className="stat-card">
          <p className="stat-label">Active City</p>
          <p className="stat-value">{payload?.municipality || municipality || "..."}</p>
        </article>
        <article className="stat-card">
          <p className="stat-label">Filtered Incidents</p>
          <p className="stat-value">
            {payload ? payload.incident_count.toLocaleString() : "..."}
          </p>
        </article>
        <article className="stat-card">
          <p className="stat-label">Population Baseline</p>
          <p className="stat-value">{payload?.population_year ?? metadata?.population_year ?? "..."}</p>
        </article>
      </div>

      {error ? (
        <div className="map-error">
          <p>
            <strong>Request failed.</strong>
            <br />
            {error}
          </p>
        </div>
      ) : payload ? (
        <CrimeMap payload={payload} />
      ) : (
        <div className="map-loading">{loadingMessage}</div>
      )}
    </section>
  );
}
