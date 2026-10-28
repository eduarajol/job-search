# Job Search

Página personal para revisar cada día las ofertas de Game Design y UX de los estudios de videojuegos que me interesan.

## Cómo funciona

- `companies.json`: lista de empresas, su web de empleo y, cuando existe, el portal público del que se leen sus ofertas (Greenhouse, Lever, SmartRecruiters o Workable).
- `scripts/fetch_jobs.py`: consulta esos portales y genera `jobs.json`. Guarda las ofertas de diseño y UX de cualquier lugar, y todas las de Barcelona, España o remoto.
- `.github/workflows/update-jobs.yml`: ejecuta el script cada día a las 7:30 y a las 19:30 (hora de Barcelona) y guarda el resultado.
- `index.html`: la página. Lee `jobs.json`. Se genera desde `src/page.html` con `python scripts/build_page.py`.

Las empresas sin portal público aparecen solo con el enlace a su web de empleo.

## Puesta en marcha

1. Sube esta carpeta a un repositorio nuevo, por ejemplo `eduarajol/job-search`.
2. En el repositorio: **Settings → Pages → Build and deployment**, elige *Deploy from a branch*, rama `main`, carpeta `/ (root)`.
3. En **Actions**, abre *Update jobs* y pulsa **Run workflow** para la primera actualización.
4. La página queda en `https://eduarajol.github.io/job-search/`.

## Añadir o quitar empresas

Edita `companies.json`. Para una empresa sin portal público, deja `"source": null`.
