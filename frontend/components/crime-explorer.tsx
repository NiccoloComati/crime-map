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
  loading: () => <div className="map-loading">Loading map...</div>,
});

const MUNICIPALITY_ORDER = ["All Metro", "Boston", "Cambridge", "Somerville"] as const;
const MUNICIPALITY_LABELS: Record<string, string> = {
  "All Metro": "Boston (All metro)",
  Boston: "Boston",
  Cambridge: "Cambridge",
  Somerville: "Somerville",
};

function orderMunicipalities(options: string[]): string[] {
  const known = MUNICIPALITY_ORDER.filter((option) => options.includes(option));
  const extras = options.filter((option) => !MUNICIPALITY_ORDER.includes(option as (typeof MUNICIPALITY_ORDER)[number]));
  return [...known, ...extras];
}

function municipalityLabel(option: string): string {
  return MUNICIPALITY_LABELS[option] ?? option;
}

function municipalityDropdownLabel(option: string): string {
  if (option === "All Metro") {
    return municipalityLabel(option);
  }

  return `\u00A0\u00A0${municipalityLabel(option)}`;
}

function populationBaselineLabel(populationYear: string | null | undefined): string {
  if (!populationYear) {
    return "...";
  }

  return populationYear.replace(/\s*\(.+\)\s*$/, "");
}

export default function CrimeExplorer() {
  const [municipalities, setMunicipalities] = useState<string[]>([]);
  const [municipality, setMunicipality] = useState("");
  const [metadata, setMetadata] = useState<MunicipalityMetadata | null>(null);
  const [selectedMacro, setSelectedMacro] = useState("");
  const [startDate, setStartDate] = useState<string | null>(null);
  const [endDate, setEndDate] = useState<string | null>(null);
  const [payload, setPayload] = useState<ChoroplethPayload | null>(null);
  const [loadingMessage, setLoadingMessage] = useState("Loading areas...");
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadMunicipalities() {
      try {
        const nextMunicipalities = await fetchMunicipalities();
        if (cancelled) {
          return;
        }

        const orderedMunicipalities = orderMunicipalities(nextMunicipalities);
        setMunicipalities(orderedMunicipalities);
        setMunicipality(orderedMunicipalities[0] ?? "");
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
    setLoadingMessage("Loading area details...");

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
    setLoadingMessage("Preparing map...");

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
      <div className="explorer-header">
        <p className="explorer-kicker">Official records. Comparable neighborhood rates.</p>
        <p className="explorer-note">
          Choose an area, pick a crime type, and tighten the dates. The map should do the rest.
        </p>
      </div>
      <div className="controls-grid">
        <div className="control">
          <label htmlFor="municipality">Area</label>
          <select
            id="municipality"
            value={municipality}
            onChange={(event) => setMunicipality(event.target.value)}
          >
            {municipalities.map((option) => (
              <option key={option} value={option}>
                {municipalityDropdownLabel(option)}
              </option>
            ))}
          </select>
        </div>
        <div className="control">
          <label htmlFor="macro">Crime Type</label>
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
          <p className="stat-label">Active Area</p>
          <p className="stat-value">
            {municipalityLabel(payload?.municipality || municipality || "...")}
          </p>
        </article>
        <article className="stat-card">
          <p className="stat-label">Incidents in Range</p>
          <p className="stat-value">
            {payload ? payload.incident_count.toLocaleString() : "..."}
          </p>
        </article>
        <article className="stat-card">
          <p className="stat-label">Population Baseline</p>
          <p className="stat-value">
            {populationBaselineLabel(payload?.population_year ?? metadata?.population_year)}
          </p>
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

      <section className="methodology-section" aria-labelledby="methodology-title">
        <div className="methodology-header">
          <p className="methodology-eyebrow">Methodology</p>
          <h2 id="methodology-title">How it works</h2>
        </div>
        <div className="methodology-grid">
          <p>
            Crime totals come from official municipal police open-data feeds for the areas
            currently covered by the app. The metro view combines those same local feeds into one
            regional map.
          </p>
          <p>
            The backend stores daily incident counts by neighborhood and crime family. The selected
            date window is applied to those aggregates before rates are calculated.
          </p>
          <p>
            Population normalization uses 2020 Census block counts. When a census block crosses
            neighborhood boundaries, its population is area-allocated across those polygons.
          </p>
          <p>
            Colors are relative to the current selection. The legend shows incidents per 1,000
            residents for the active area, crime type, and date range.
          </p>
        </div>
      </section>
    </section>
  );
}
