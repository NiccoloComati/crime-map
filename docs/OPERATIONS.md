# Operations

## Goal

Use local secrets so Codex can access Render and Vercel from the terminal without storing credentials in git.

## Recommended Secret Variables

- `RENDER_API_KEY`
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

For this repo, `.vercel/project.json` already provides:

- `VERCEL_ORG_ID=team_omNjpTPpFiQnbjXRyj6enhHF`
- `VERCEL_PROJECT_ID=prj_oq7J0vRhr1aPLXrRBav8wcILREcr`

## Best Setup On Windows

Set persistent user environment variables once, then restart the terminal and Codex session:

```powershell
setx RENDER_API_KEY "your-render-api-key"
setx VERCEL_TOKEN "your-vercel-token"
setx VERCEL_ORG_ID "team_omNjpTPpFiQnbjXRyj6enhHF"
setx VERCEL_PROJECT_ID "prj_oq7J0vRhr1aPLXrRBav8wcILREcr"
```

Notes:

- `setx` updates future shells, not the current one.
- After setting them, fully restart the terminal or IDE session that launches Codex.

## Repo-Local Alternative

If you do not want machine-wide variables, create an untracked local file from `.env.codex.example.ps1`:

```powershell
Copy-Item .env.codex.example.ps1 .env.codex.ps1
```

Fill in the real values, then load it before starting work:

```powershell
. .\.env.codex.ps1
```

That file is ignored by git.

## Verification

In a new PowerShell session:

```powershell
echo $env:RENDER_API_KEY
echo $env:VERCEL_TOKEN
echo $env:VERCEL_ORG_ID
echo $env:VERCEL_PROJECT_ID
```

The secret values should print if the environment is loaded.

## Deployment Notes

- Render service: `crime-map-api`
- Render URL: `https://crime-map-api-epxb.onrender.com`
- Render `autoDeploy` was observed as `off` on 2026-03-12
- Vercel project name: `crime-map`

## Codex Usage

- Codex can use these credentials if they are present in the shell environment.
- Do not paste secrets into chat unless absolutely necessary.
- Rotate any key that has been pasted into chat or committed anywhere by mistake.
