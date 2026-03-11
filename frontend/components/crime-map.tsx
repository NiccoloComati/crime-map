"use client";

import { GeoJSON, MapContainer, TileLayer } from "react-leaflet";

import type { ChoroplethPayload, MetricFeatureProperties } from "@/lib/api";

type CrimeMapProps = {
  payload: ChoroplethPayload;
};

const COLOR_SCALE = ["#ffe08a", "#ffb347", "#e76f2d", "#bf3b1f", "#74140d"] as const;

function getColor(value: number, maxValue: number): string {
  if (maxValue <= 0) {
    return "#8e7f68";
  }

  const ratio = value / maxValue;
  if (ratio >= 0.8) return COLOR_SCALE[4];
  if (ratio >= 0.6) return COLOR_SCALE[3];
  if (ratio >= 0.4) return COLOR_SCALE[2];
  if (ratio >= 0.2) return COLOR_SCALE[1];
  return COLOR_SCALE[0];
}

export default function CrimeMap({ payload }: CrimeMapProps) {
  const features = payload.geojson.features;
  const values = features.map((feature) => Number(feature.properties.metric_value || 0));
  const maxValue = values.length > 0 ? Math.max(...values) : 0;
  const legendStops = [
    { label: "Peak", color: getColor(maxValue * 0.9, maxValue) },
    { label: "High", color: getColor(maxValue * 0.7, maxValue) },
    { label: "Elevated", color: getColor(maxValue * 0.5, maxValue) },
    { label: "Low", color: getColor(maxValue * 0.3, maxValue) },
    { label: "Near zero", color: getColor(maxValue * 0.1, maxValue) },
  ];

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
          url="https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png"
        />
        <GeoJSON
          data={payload.geojson as never}
          style={(feature) => {
            const properties = feature?.properties as MetricFeatureProperties | undefined;
            const metricValue = Number(properties?.metric_value || 0);
            return {
              color: "#efe5cf",
              weight: 1.05,
              opacity: 0.7,
              fillOpacity: 0.82,
              fillColor: getColor(metricValue, maxValue),
            };
          }}
          onEachFeature={(feature, layer) => {
            const properties = feature.properties as MetricFeatureProperties;
            const tooltip = `
              <div class="tooltip-shell">
                <strong>${properties.Mapped_Name}</strong>
                <span>${properties.City}</span>
                <span>${payload.selected_macro}: ${Number(properties.metric_value).toFixed(6)}</span>
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
