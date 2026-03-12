const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000").replace(
  /\/+$/,
  "",
);

export type MetricFeatureProperties = {
  City: string;
  Mapped_Name: string;
  GeoKey: string;
  Population: number;
  metric_value: number | null;
  is_rate_valid?: boolean;
};

export type ChoroplethFeatureCollection = {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    geometry: Record<string, unknown>;
    properties: MetricFeatureProperties;
  }>;
};

export type MunicipalityMetadata = {
  municipality: string;
  macro_options: string[];
  default_macro: string;
  zoom: number;
  center: [number, number];
  population_year: string;
  min_date: string;
  max_date: string;
};

export type CoverageEntry = {
  name: string;
  label: string;
  status: string;
  geography_level: string;
  temporal_granularity: string;
  source_kind: string;
  included_in_current_aggregate: boolean;
  notes: string;
  official_source_urls: string[];
};

export type CoveragePayload = {
  official_metro_reference_name: string;
  official_metro_reference_url: string;
  current_aggregate_name: string;
  current_aggregate_label: string;
  current_aggregate_members: string[];
  municipalities: CoverageEntry[];
};

export type ChoroplethPayload = {
  municipality: string;
  selected_macro: string;
  zoom: number;
  center: [number, number];
  population_year: string;
  start_date: string | null;
  end_date: string | null;
  scale_max?: number;
  excluded_area_count?: number;
  incident_count: number;
  geojson: ChoroplethFeatureCollection;
};

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;

    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // Fall back to the generic message above.
    }

    throw new Error(detail);
  }

  return (await response.json()) as T;
}

function apiUrl(path: string): string {
  return new URL(path, `${API_BASE_URL}/`).toString();
}

export async function fetchMunicipalities(): Promise<string[]> {
  const response = await fetch(apiUrl("api/v1/municipalities"), {
    cache: "no-store",
  });
  const payload = await parseJson<{ municipalities: string[] }>(response);
  return payload.municipalities;
}

export async function fetchCoverage(): Promise<CoveragePayload> {
  const response = await fetch(apiUrl("api/v1/coverage"), {
    cache: "no-store",
  });
  return parseJson<CoveragePayload>(response);
}

export async function fetchMunicipalityMetadata(
  municipality: string,
): Promise<MunicipalityMetadata> {
  const response = await fetch(
    apiUrl(`api/v1/municipalities/${encodeURIComponent(municipality)}/metadata`),
    {
      cache: "no-store",
    },
  );
  return parseJson<MunicipalityMetadata>(response);
}

export async function fetchMunicipalityChoropleth(params: {
  municipality: string;
  macro: string;
  startDate: string | null;
  endDate: string | null;
}): Promise<ChoroplethPayload> {
  const search = new URLSearchParams();
  search.set("macro", params.macro);

  if (params.startDate) {
    search.set("start_date", params.startDate);
  }
  if (params.endDate) {
    search.set("end_date", params.endDate);
  }

  const response = await fetch(
    `${apiUrl(`api/v1/municipalities/${encodeURIComponent(params.municipality)}/choropleth`)}?${search.toString()}`,
    {
      cache: "no-store",
    },
  );
  return parseJson<ChoroplethPayload>(response);
}
