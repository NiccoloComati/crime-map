"use client";

import { GeoJSON, MapContainer, Pane, TileLayer } from "react-leaflet";

import type { ChoroplethPayload, MetricFeatureProperties } from "@/lib/api";

type CrimeMapProps = {
  payload: ChoroplethPayload;
};

type ColorStop = {
  position: number;
  color: [number, number, number];
  alpha: number;
};

const COLOR_STOPS: ColorStop[] = [
  { position: 0, color: [54, 172, 90], alpha: 0.52 },
  { position: 0.45, color: [236, 214, 68], alpha: 0.74 },
  { position: 0.72, color: [242, 145, 55], alpha: 0.8 },
  { position: 1, color: [215, 65, 52], alpha: 0.84 },
];
const EMPTY_COLOR = "#cfd6de";
const MIN_RATE_POPULATION = 100;
const SAFE_SCALE_PERCENTILE = 0.98;
const SAFE_SCALE_MIN_FEATURES = 8;
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

function rgba([red, green, blue]: [number, number, number], alpha: number): string {
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}

function interpolateChannel(start: number, end: number, ratio: number): number {
  return Math.round(start + (end - start) * ratio);
}

function getColorAtRatio(ratio: number): string {
  const clampedRatio = Math.max(0, Math.min(1, ratio));

  for (let index = 1; index < COLOR_STOPS.length; index += 1) {
    const previousStop = COLOR_STOPS[index - 1];
    const nextStop = COLOR_STOPS[index];

    if (clampedRatio <= nextStop.position) {
      const localRatio =
        (clampedRatio - previousStop.position) / (nextStop.position - previousStop.position);
      return rgba(
        [
          interpolateChannel(previousStop.color[0], nextStop.color[0], localRatio),
          interpolateChannel(previousStop.color[1], nextStop.color[1], localRatio),
          interpolateChannel(previousStop.color[2], nextStop.color[2], localRatio),
        ],
        previousStop.alpha + (nextStop.alpha - previousStop.alpha) * localRatio,
      );
    }
  }

  const finalStop = COLOR_STOPS[COLOR_STOPS.length - 1];
  return rgba(finalStop.color, finalStop.alpha);
}

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

function isFiniteMetricValue(value: number | null | undefined): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isRateValid(properties: MetricFeatureProperties): boolean {
  if (typeof properties.is_rate_valid === "boolean") {
    return properties.is_rate_valid && isFiniteMetricValue(properties.metric_value);
  }

  return isFiniteMetricValue(properties.metric_value) && Number(properties.Population) >= MIN_RATE_POPULATION;
}

function safeScaleMax(values: number[]): number {
  if (values.length === 0) {
    return 0;
  }

  const sortedValues = [...values].sort((left, right) => left - right);
  const absoluteMax = sortedValues[sortedValues.length - 1];
  if (sortedValues.length < SAFE_SCALE_MIN_FEATURES) {
    return absoluteMax;
  }

  const percentileIndex = Math.min(
    sortedValues.length - 1,
    Math.max(0, Math.ceil(sortedValues.length * SAFE_SCALE_PERCENTILE) - 1),
  );
  const percentileMax = sortedValues[percentileIndex];
  if (!Number.isFinite(percentileMax) || percentileMax <= 0) {
    return absoluteMax;
  }

  return Math.min(absoluteMax, Math.max(percentileMax, absoluteMax * 0.4));
}

function getColor(value: number, maxValue: number): string {
  if (maxValue <= 0) {
    return EMPTY_COLOR;
  }

  return getColorAtRatio(value / maxValue);
}

function buildLegendTicks(maxValue: number, hasClippedValues: boolean) {
  const ratios = [0, 0.25, 0.5, 0.75, 1];
  return ratios.map((ratio, index) => {
    const label = formatRate(maxValue * ratio);
    if (hasClippedValues && index === ratios.length - 1) {
      return { ratio, label: `${label}+` };
    }

    return { ratio, label };
  });
}

function buildLegendGradient(): string {
  return `linear-gradient(90deg, ${COLOR_STOPS.map(
    (stop) => `${rgba(stop.color, stop.alpha)} ${Math.round(stop.position * 100)}%`,
  ).join(", ")})`;
}

export default function CrimeMap({ payload }: CrimeMapProps) {
  const features = payload.geojson.features;
  const values = features.flatMap((feature) => {
    if (!isRateValid(feature.properties) || feature.properties.metric_value === null) {
      return [];
    }

    return [Number(feature.properties.metric_value)];
  });
  const absoluteMaxValue = values.length > 0 ? Math.max(...values) : 0;
  const maxValue = payload.scale_max && payload.scale_max > 0 ? payload.scale_max : safeScaleMax(values);
  const excludedAreaCount =
    typeof payload.excluded_area_count === "number"
      ? payload.excluded_area_count
      : features.filter((feature) => !isRateValid(feature.properties)).length;
  const legendTicks = buildLegendTicks(maxValue, absoluteMaxValue > maxValue);
  const legendGradient = buildLegendGradient();

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
          url="https://{s}.basemaps.cartocdn.com/voyager_nolabels/{z}/{x}/{y}{r}.png"
        />
        <Pane name="labels" style={{ zIndex: 450, pointerEvents: "none" }}>
          <TileLayer
            attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/voyager_only_labels/{z}/{x}/{y}{r}.png"
            opacity={0.8}
          />
        </Pane>
        <GeoJSON
          data={payload.geojson as never}
          style={(feature) => {
            const properties = feature?.properties as MetricFeatureProperties | undefined;
            const metricValue = properties?.metric_value ?? null;
            const rateIsValid = properties ? isRateValid(properties) : false;
            return {
              color: rateIsValid ? "#f8fbfd" : "#e8edf2",
              weight: rateIsValid ? 1.2 : 1,
              opacity: rateIsValid ? 0.95 : 0.88,
              fillOpacity: 1,
              fillColor: rateIsValid && metricValue !== null ? getColor(metricValue, maxValue) : EMPTY_COLOR,
            };
          }}
          onEachFeature={(feature, layer) => {
            const properties = feature.properties as MetricFeatureProperties;
            const rateIsValid = isRateValid(properties) && properties.metric_value !== null;
            const metricSummary = rateIsValid
              ? `${payload.selected_macro}: ${formatRate(Number(properties.metric_value))} per 1,000 residents`
              : "Rate unavailable: resident population is too small for a stable comparison";
            const tooltip = `
              <div class="tooltip-shell">
                <strong>${properties.Mapped_Name}</strong>
                <span>${properties.City}</span>
                <span>${metricSummary}</span>
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
        {maxValue > 0 ? (
          <>
            <div className="legend-scale" style={{ backgroundImage: legendGradient }} />
            <div className="legend-ticks" aria-hidden="true">
              {legendTicks.map((tick) => (
                <span key={tick.ratio}>{tick.label}</span>
              ))}
            </div>
          </>
        ) : (
          <div className="legend-row">
            <span className="legend-swatch" style={{ backgroundColor: EMPTY_COLOR }} />
            <span>{excludedAreaCount > 0 ? "No reported incidents in ranked areas" : "No reported incidents"}</span>
          </div>
        )}
        {excludedAreaCount > 0 ? (
          <div className="legend-row legend-row-muted">
            <span className="legend-swatch" style={{ backgroundColor: EMPTY_COLOR }} />
            <span>Excluded from rate ranking</span>
          </div>
        ) : null}
      </div>
    </div>
  );
}
