# FitXMatt — Nutrition Coaching Site

Single-file static landing page for FitXMatt (Matúš), a nutrition coach for busy IT professionals.

## Structure
- `index.html` — self-contained page (inline CSS + JS)
- `*.jpg` — client/coach photos
- Contact form wired to Web3Forms (free, no backend)

## Deploy (GitHub Pages)
1. Create a repo on GitHub (e.g. `fitxmatt`).
2. Push this folder:
   ```
   git remote add origin https://github.com/<you>/fitxmatt.git
   git branch -M main
   git push -u origin main
   ```
3. In repo **Settings → Pages → Build and deployment → Source: Deploy from a branch → main / root**.
4. Site goes live at `https://<you>.github.io/fitxmatt/`.

Custom domain (`fitxmatt.com`) can be added later in Settings → Pages.
