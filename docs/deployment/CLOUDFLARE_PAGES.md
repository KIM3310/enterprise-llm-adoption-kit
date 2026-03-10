# Cloudflare Pages Deploy

- Root directory: `app/frontend`
- Build command: `cd app/frontend && npm ci && npm run build`
- Output directory: `app/frontend/dist`

AdSense/Review automation:
- `tools/release_ops.sh cloudflare`
- `tools/release_ops.sh apply-adsense <ca-pub-xxxxxxxxxxxxxxxx> <slot-id>`
- `tools/release_ops.sh check`
