# Deploy

This repo is set up for the zero-cost test deployment path:

- frontend on Vercel Hobby
- API on Render Free

The active deployment files are:

- [render.yaml](render.yaml)
- [api/Dockerfile](api/Dockerfile)
- [frontend/vercel.json](frontend/vercel.json)

## Recommended order

1. Deploy the API on Render Free
2. Copy the Render public URL
3. Deploy the frontend on Vercel Hobby
4. Confirm the app works on the default `onrender.com` and `vercel.app` URLs
5. Add custom domains only after those URLs work

## Render Free details

[render.yaml](render.yaml) sets the API service plan to `free`.

That keeps the first hosted version at zero cost, but Free web services have important limits:

- they spin down after 15 minutes of inactivity
- the first request after idle is slower
- they are meant for testing, hobby, and preview use

If later you want an always-on backend, upgrade only the Render API service from `free` to `starter` in the Render dashboard. No code changes are required.

## 1. Frontend on Vercel

Create a Vercel project from this repository and set the root directory to `frontend`.

Set this environment variable in Vercel:

- `NEXT_PUBLIC_API_BASE_URL=https://your-render-api-domain`

Use the API origin only. Do not include a trailing slash or any path segment.

Apply it to:

- Production
- Preview
- Development

## 2. API on Render

Create the Render service from `render.yaml` at the repository root.

Set these Render environment variables:

- `CRIME_MAP_ALLOWED_ORIGINS=https://your-frontend-domain`
- `CRIME_MAP_ALLOWED_ORIGIN_REGEX=^https://.*\\.vercel\\.app$`

For `CRIME_MAP_ALLOWED_ORIGINS`, use the frontend origin only. Do not include a path.

`CRIME_MAP_ALLOWED_ORIGIN_REGEX` is optional, but useful if you want Vercel preview deployments to call the API before you finalize the production frontend domain.

## 3. Custom domains

Recommended setup:

1. Put the frontend on your public domain, for example `crime.yourdomain.com`, via Vercel.
2. Put the API on a separate subdomain, for example `crime-api.yourdomain.com`, via Render.
3. Set `NEXT_PUBLIC_API_BASE_URL` in Vercel to the Render API URL first, then later to the custom API domain.
4. Set `CRIME_MAP_ALLOWED_ORIGINS` in Render to the frontend URL.

## 4. Upgrade path

If the Free backend becomes too slow because of idle spin-down:

1. Open the Render API service
2. Change the instance type from `free` to `starter`
3. Save the change

The same service, domain, code, and environment variables continue to work.

## 5. Notes

- The frontend is a Next.js client-side map app and fits the Vercel Hobby tier well.
- The API is the only service that needs the Python geospatial stack.
- The retired Streamlit UI is archived under [old/legacy-streamlit-app](old/legacy-streamlit-app).
