# Deploy

This repo is now deployed as two services:

- frontend on Vercel
- API on Render

## 1. Frontend on Vercel

Create a Vercel project from this repository and set the project root directory to `frontend`.

Set this environment variable in Vercel:

- `NEXT_PUBLIC_API_BASE_URL=https://your-render-api-domain`

Use the custom domain you want for the frontend in the Vercel dashboard after the first deploy succeeds.

## 2. API on Render

Create the Render service from `render.yaml` at the repository root.

The blueprint uses:

- [render.yaml](render.yaml)
- [api/Dockerfile](api/Dockerfile)

Set these Render environment variables:

- `CRIME_MAP_ALLOWED_ORIGINS=https://your-frontend-domain`
- `CRIME_MAP_ALLOWED_ORIGIN_REGEX=^https://.*\\.vercel\\.app$`

`CRIME_MAP_ALLOWED_ORIGIN_REGEX` is optional, but useful if you want Vercel preview deployments to call the API.

## 3. Custom domains

Recommended setup:

1. Put the frontend on your public domain, for example `crime.yourdomain.com`, via Vercel.
2. Put the API on a separate subdomain, for example `crime-api.yourdomain.com`, via Render.
3. Set `NEXT_PUBLIC_API_BASE_URL` in Vercel to the Render API URL.
4. Set `CRIME_MAP_ALLOWED_ORIGINS` in Render to the frontend URL.

## 4. Deploy order

1. Deploy the Render API first and get its public URL.
2. Set `NEXT_PUBLIC_API_BASE_URL` in Vercel.
3. Deploy the Vercel frontend.
4. Add custom domains in both dashboards.
5. Update `CRIME_MAP_ALLOWED_ORIGINS` on Render to the final frontend domain.

## 5. Notes

- The frontend is static Next.js output plus client-side map logic.
- The API is the only service that needs the Python geospatial stack.
- The retired Streamlit UI is archived under [old/legacy-streamlit-app](old/legacy-streamlit-app).
