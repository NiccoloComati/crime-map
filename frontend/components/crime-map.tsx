"use client";

import { GeoJSON, MapContainer, TileLayer } from "react-leaflet";

import type { ChoroplethPayload, MetricFeatureProperties } from "@/lib/api";

type CrimeMapProps = {
  payload: ChoroplethPayload;
};

const COLOR_SCALE = [
  "rgba(117, 191, 255, 0.72)",
  "rgba(87, 186, 112, 0.72)",
  "rgba(255, 214, 64, 0.82)",
  "rgba(245, 146, 61, 0.8)",
  "rgba(220, 74, 58, 0.82)",
] as const;
const EMPTY_COLOR = "#d7dee6";
const RATE_SCALE = 1000;
const RATE_FORMATTERS = {
  coarse: new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 1,
  }),
  standard: new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }),
  precise: new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  }),
  ultra: new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  }),
};

function formatRate(value: number): string {
  const scaledValue = value * RATE_SCALE;
  if (scaledValue >= 10) {
    return RATE_FORMATTERS.coarse.format(scaledValue);
  }
  if (scaledValue >= 0.1) {
    return RATE_FORMATTERS.standard.format(scaledValue);
  }
  if (scaledValue >= 0.01) {
    return RATE_FORMATTERS.precise.format(scaledValue);
  }
  return RATE_FORMATTERS.ultra.format(scaledValue);
}

function getColor(value: number, maxValue: number): string {
  if (maxValue <= 0) {
    return EMPTY_COLOR;
  }

  const ratio = value / maxValue;
  if (ratio >= 0.8) return COLOR_SCALE[4];
  if (ratio >= 0.6) return COLOR_SCALE[3];
  if (ratio >= 0.4) return COLOR_SCALE[2];
  if (ratio >= 0.2) return COLOR_SCALE[1];
  return COLOR_SCALE[0];
}

function buildLegendStops(maxValue: number) {
  if (maxValue <= 0) {
    return [{ label: "No reported incidents", color: EMPTY_COLOR }];
  }

  return [
    { label: `${formatRate(maxValue * 0.8)}+`, color: COLOR_SCALE[4] },
    { label: `${formatRate(maxValue * 0.6)} - ${formatRate(maxValue * 0.8)}`, color: COLOR_SCALE[3] },
    { label: `${formatRate(maxValue * 0.4)} - ${formatRate(maxValue * 0.6)}`, color: COLOR_SCALE[2] },
    { label: `${formatRate(maxValue * 0.2)} - ${formatRate(maxValue * 0.4)}`, color: COLOR_SCALE[1] },
    { label: `0 - ${formatRate(maxValue * 0.2)}`, color: COLOR_SCALE[0] },
  ];
}

export default function CrimeMap({ payload }: CrimeMapProps) {
  const features = payload.geojson.features;
  const values = features.map((feature) => Number(feature.properties.metric_value || 0));
  const maxValue = values.length > 0 ? Math.max(...values) : 0;
  const legendStops = buildLegendStops(maxValue);

  return (
    <div className="map-panel">
      <MapContainer
        key={`${payload.municipality}-${payload.selected_macro}-${payload.start_date}-${payload.end_date}`}
        center={payload.center}
        zoom={payload.zoom}
        scrollWheelZoom
        className="map-canvas"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png"
        />
        <GeoJSON
          data={payload.geojson as never}
          style={(feature) => {
            const properties = feature?.properties as MetricFeatureProperties | undefined;
            const metricValue = Number(properties?.metric_value || 0);
            return {
              color: "#fbfcfd",
              weight: 1.15,
              opacity: 0.92,
              fillOpacity: 1,
              fillColor: getColor(metricValue, maxValue),
            };
          }}
          onEachFeature={(feature, layer) => {
            const properties = feature.properties as MetricFeatureProperties;
            const tooltip = `
              <div class="tooltip-shell">
                <strong>${properties.Mapped_Name}</strong>
                <span>${properties.City}</span>
                <span>${payload.selected_macro}: ${formatRate(Number(properties.metric_value || 0))} per 1,000 residents</span>
                <span>Population: ${Math.round(Number(properties.Population)).toLocaleString()}</span>
              </div>
            `;

            layer.bindTooltip(tooltip, {
              className: "crime-tooltip",
              direction: "top",
              sticky: false,
            });
          }}
        />
      </MapContainer>
      <div className="legend-card">
        <p className="legend-title">{payload.selected_macro}</p>
        <p className="legend-subtitle">Incidents per 1,000 residents</p>
        {legendStops.map((stop) => (
          <div key={stop.label} className="legend-row">
            <span className="legend-swatch" style={{ backgroundColor: stop.color }} />
            <span>{stop.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
