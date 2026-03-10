"use client";

import { GeoJSON, MapContainer, TileLayer } from "react-leaflet";

import type { ChoroplethPayload, MetricFeatureProperties } from "@/lib/api";

type CrimeMapProps = {
  payload: ChoroplethPayload;
};

function getColor(value: number, maxValue: number): string {
  if (maxValue <= 0) {
    return "#f9edc6";
  }

  const ratio = value / maxValue;
  if (ratio >= 0.8) return "#8f1d14";
  if (ratio >= 0.6) return "#c84b27";
  if (ratio >= 0.4) return "#e58e2f";
  if (ratio >= 0.2) return "#f4bf52";
  return "#f9edc6";
}

export default function CrimeMap({ payload }: CrimeMapProps) {
  const features = payload.geojson.features;
  const values = features.map((feature) => Number(feature.properties.metric_value || 0));
  const maxValue = values.length > 0 ? Math.max(...values) : 0;
  const legendStops = [
    { label: "80-100%", color: getColor(maxValue * 0.9, maxValue) },
    { label: "60-80%", color: getColor(maxValue * 0.7, maxValue) },
    { label: "40-60%", color: getColor(maxValue * 0.5, maxValue) },
    { label: "20-40%", color: getColor(maxValue * 0.3, maxValue) },
    { label: "0-20%", color: getColor(maxValue * 0.1, maxValue) },
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
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />
        <GeoJSON
          data={payload.geojson as never}
          style={(feature) => {
            const properties = feature?.properties as MetricFeatureProperties | undefined;
            const metricValue = Number(properties?.metric_value || 0);
            return {
              color: "#332919",
              weight: 1,
              opacity: 0.45,
              fillOpacity: 0.75,
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
