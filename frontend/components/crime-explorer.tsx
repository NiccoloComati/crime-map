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

type ScaleReference = "selected" | "metro";

const MUNICIPALITY_ORDER = ["All Metro", "Boston", "Cambridge", "Somerville"] as const;
const MUNICIPALITY_LABELS: Record<string, string> = {
  "All Metro": "Boston (All metro)",
  Boston: "Boston",
  Cambridge: "Cambridge",
  Somerville: "Somerville",
};
const DEFAULT_WINDOW_YEARS = 5;

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

function parseIsoDate(value: string): Date {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(Date.UTC(year, month - 1, day));
}

function formatIsoDate(value: Date): string {
  return value.toISOString().slice(0, 10);
}

function subtractYears(value: Date, years: number): Date {
  const nextValue = new Date(value);
  const targetMonth = nextValue.getUTCMonth();
  nextValue.setUTCFullYear(nextValue.getUTCFullYear() - years);

  if (nextValue.getUTCMonth() !== targetMonth) {
    nextValue.setUTCDate(0);
  }

  return nextValue;
}

function defaultWindowStartDate(minDate: string, maxDate: string): string {
  const minimumDate = parseIsoDate(minDate);
  const maximumDate = parseIsoDate(maxDate);
  const proposedStartDate = subtractYears(maximumDate, DEFAULT_WINDOW_YEARS);

  if (proposedStartDate < minimumDate) {
    return minDate;
  }

  return formatIsoDate(proposedStartDate);
}

export default function CrimeExplorer() {
  const [municipalities, setMunicipalities] = useState<string[]>([]);
  const [municipality, setMunicipality] = useState("");
  const [metadata, setMetadata] = useState<MunicipalityMetadata | null>(null);
  const [selectedMacro, setSelectedMacro] = useState("");
  const [scaleReference, setScaleReference] = useState<ScaleReference>("selected");
  const [startDate, setStartDate] = useState<string | null>(null);
  const [endDate, setEndDate] = useState<string | null>(null);
  const [payload, setPayload] = useState<ChoroplethPayload | null>(null);
  const [scalePayload, setScalePayload] = useState<ChoroplethPayload | null>(null);
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
        setEndDate(nextMetadata.max_date);
        setStartDate(defaultWindowStartDate(nextMetadata.min_date, nextMetadata.max_date));
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
        const scaleMunicipality =
          scaleReference === "metro" && municipality !== "All Metro" ? "All Metro" : municipality;
        const [nextPayload, nextScalePayload] = await Promise.all([
          fetchMunicipalityChoropleth({
            municipality,
            macro: selectedMacro,
            startDate,
            endDate,
          }),
          scaleMunicipality === municipality
            ? Promise.resolve<ChoroplethPayload | null>(null)
            : fetchMunicipalityChoropleth({
                municipality: scaleMunicipality,
                macro: selectedMacro,
                startDate,
                endDate,
              }),
        ]);
        if (cancelled) {
          return;
        }

        setPayload(nextPayload);
        setScalePayload(nextScalePayload ?? nextPayload);
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
  }, [municipality, metadata, selectedMacro, scaleReference, startDate, endDate]);

  return (
    <section className="explorer-shell">
      <div className="explorer-header">
        <p className="explorer-kicker">Official records. Comparable neighborhood rates.</p>
        <p className="explorer-note">
           Pick an area. Pick a crime type. Choose your horizon.<br />
           The map should do the rest.
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
          <label htmlFor="scale-reference">Scale Reference</label>
          <select
            id="scale-reference"
            value={scaleReference}
            onChange={(event) => setScaleReference(event.target.value as ScaleReference)}
          >
            <option value="selected">Selected area</option>
            <option value="metro">Metro area</option>
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
        <CrimeMap
          payload={payload}
          scalePayload={scalePayload ?? payload}
          scaleReferenceLabel={scaleReference === "metro" ? "Metro area scale" : "Selected area scale"}
        />
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
            The color scale can be anchored to the selected area or to the full metro area. Colors
            are assigned by where each neighborhood rate sits within that chosen reference set, and
            the legend shows the matching whole-number rate cutoffs for that reference.
          </p>
          <p>
            Areas with resident population below 100 are grayed out and excluded from rate ranking.
            Areas with resident population below 500 keep their computed crime score, but they are
            excluded from the scale calibration and flagged as unstable because a very small
            denominator can swing the rate sharply.
          </p>
          <p>
            Small-population areas still display their computed rate, but if they sit above or
            below the stable reference range they are clipped to the reddest or greenest end of the
            map rather than stretching the scale for everything else.
          </p>
        </div>
      </section>
    </section>
  );
}
