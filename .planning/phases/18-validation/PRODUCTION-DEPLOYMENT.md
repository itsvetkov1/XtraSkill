# Production Deployment Guide: SPA Deep Linking

This guide documents server configuration requirements for deploying the BA Assistant Flutter web application with deep linking support.

## Overview

### Why SPA Routing Requires Server Configuration

Single-Page Applications (SPAs) like Flutter web apps handle routing client-side using JavaScript. When a user visits a deep link like `/projects/abc/threads/xyz`:

1. **Development (`flutter run`):** The development server knows to serve `index.html` for all routes, letting Flutter handle routing.

2. **Production (without configuration):** The web server looks for a literal file at `/projects/abc/threads/xyz`, finds nothing, and returns a server 404 error.

3. **Production (with configuration):** The web server is configured to serve `index.html` for all routes, letting Flutter handle routing just like development.

### What Happens Without Rewrite Rules

Without proper server configuration:

| Action | Result |
|--------|--------|
| Navigate to `/projects/abc` via link | Works (initial page load serves index.html) |
| Press F5 to refresh on `/projects/abc` | **Server 404 error** (server looks for literal path) |
| Paste `/projects/abc` in new tab | **Server 404 error** |
| Click browser back button | Works (client-side navigation) |

The server 404 is a raw server error page, not the Flutter NotFoundScreen. Users see an ugly technical error instead of a helpful navigation option.

## Flutter Build

### Build Command

```bash
# Standard production build
flutter build web --release

# Output location
build/web/
```

### Build Output Structure

```
build/web/
|-- index.html          # Entry point (all routes serve this)
|-- main.dart.js        # Compiled Dart application
|-- flutter.js          # Flutter engine
|-- assets/             # Application assets
|-- icons/              # App icons
|-- manifest.json       # PWA manifest
|-- flutter_service_worker.js  # Service worker
```

### Base Href Configuration

The `<base href>` tag in `index.html` tells Flutter where the app is deployed:

```html
<!-- For root domain deployment (https://example.com/) -->
<base href="/">

<!-- For subdirectory deployment (https://example.com/app/) -->
<base href="/app/">
```

**Build with custom base href:**

```bash
# Deploy to subdirectory /myapp/
flutter build web --release --base-href /myapp/
```

## Server Configurations

### Nginx

The most common production server for Flutter web apps.

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/flutter_app/build/web;
    index index.html;

    # Critical: SPA rewrite rule for deep linking
    # Serves index.html for all routes that don't match a file
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Recommended: Cache static assets for performance
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Key directive:** `try_files $uri $uri/ /index.html;`
- First, try to serve the literal file path (`$uri`)
- Then try as a directory (`$uri/`)
- Finally, fall back to `/index.html` (letting Flutter handle the route)

**With HTTPS (recommended for production):**

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    root /var/www/flutter_app/build/web;
    index index.html;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Apache (.htaccess)

Place this file in the web root directory (same directory as `index.html`).

```apache
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteBase /

    # Don't rewrite if the request is for an existing file
    RewriteCond %{REQUEST_FILENAME} !-f
    # Don't rewrite if the request is for an existing directory
    RewriteCond %{REQUEST_FILENAME} !-d

    # Rewrite everything else to index.html
    RewriteRule ^ index.html [L]
</IfModule>
```

**Requirements:**
- Apache mod_rewrite module enabled
- AllowOverride set to allow .htaccess

**For subdirectory deployment:**

```apache
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteBase /myapp/

    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteCond %{REQUEST_FILENAME} !-d
    RewriteRule ^ index.html [L]
</IfModule>
```

### Vercel

Create `vercel.json` in the project root.

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/" }
  ]
}
```

**Deployment steps:**

1. Build Flutter web: `flutter build web --release`
2. Create `vercel.json` in `build/web/` directory
3. Deploy: `cd build/web && vercel --prod`

**Or configure in Vercel dashboard:**
- Settings > Rewrites > Add rewrite
- Source: `/(.*)`
- Destination: `/`

### Firebase Hosting

Create or update `firebase.json` in the project root.

```json
{
  "hosting": {
    "public": "build/web",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=31536000, immutable"
          }
        ]
      }
    ]
  }
}
```

**Deployment steps:**

1. Install Firebase CLI: `npm install -g firebase-tools`
2. Login: `firebase login`
3. Initialize (if not done): `firebase init hosting`
4. Build Flutter web: `flutter build web --release`
5. Deploy: `firebase deploy --only hosting`

### Other Platforms

**AWS S3 + CloudFront:**
- Configure CloudFront to return `index.html` for 404 errors
- Set error page path: `/index.html`
- Set HTTP response code: `200`

**GitHub Pages:**
- Create a 404.html that redirects to index.html
- Or use a routing library that supports hash-based URLs

**Docker (with Nginx):**

```dockerfile
FROM nginx:alpine
COPY build/web /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

## Troubleshooting

### Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| 404 on page refresh | Missing rewrite rules | Add appropriate server configuration from above |
| Assets not loading | Wrong base href | Match `<base href>` to deployment path |
| Deep links go to server 404 | Server returns 404 before Flutter loads | Check server is serving `index.html` for all routes |
| OAuth callback fails | Redirect URI mismatch | Update OAuth app settings with production URL |
| Blank page after deploy | JavaScript errors | Check browser console; verify build completed successfully |
| Wrong route after OAuth | returnUrl not preserved | Verify sessionStorage works (same origin, not cleared) |

### Debugging Steps

1. **Verify build output exists:**
   ```bash
   ls -la build/web/index.html
   ```

2. **Check server is serving index.html:**
   ```bash
   curl -I https://your-domain.com/projects/abc
   # Should return 200, not 404
   ```

3. **Check base href matches deployment:**
   ```bash
   grep "base href" build/web/index.html
   ```

4. **Check browser console for errors:**
   - Open DevTools (F12)
   - Look for 404 errors on assets
   - Look for JavaScript errors

### Testing Deep Links

After deployment, test these scenarios:

1. **Direct navigation:** Open `/projects` in a new tab
2. **Refresh:** Navigate to `/settings`, press F5
3. **Share link:** Copy URL from browser, paste in incognito window
4. **OAuth flow:** Log out, click deep link, complete login

## Security Considerations

### HTTPS Required

- **Session storage is per-origin.** HTTPS and HTTP are different origins.
- **OAuth callbacks require HTTPS** in production (most providers).
- **Mixed content blocks.** HTTPS pages can't load HTTP resources.

### returnUrl Validation

The application already validates returnUrl to prevent open redirect attacks:

```dart
// Only accepts relative paths starting with /
if (returnUrl != null && returnUrl.startsWith('/')) {
  destination = returnUrl;
} else {
  destination = '/home';  // Safe fallback
}
```

External URLs like `https://evil.com` are rejected.

### Session Storage Isolation

- sessionStorage is isolated per origin (protocol + domain + port)
- No cross-site access to returnUrl
- Cleared when tab closes (by design)

### Content Security Policy

For production, consider adding CSP headers:

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';";
```

## Deployment Checklist

Before going live, verify:

- [ ] Flutter web built in release mode
- [ ] Base href matches deployment path
- [ ] Server rewrite rules configured
- [ ] HTTPS enabled
- [ ] OAuth redirect URIs updated for production domain
- [ ] Deep link refresh works (F5 on any route)
- [ ] Assets load correctly (no 404s in console)
- [ ] OAuth login flow completes successfully
- [ ] returnUrl preserved through OAuth flow

---

*Created: 2026-01-31*
*Phase: 18-validation (v1.7 URL & Deep Links)*
