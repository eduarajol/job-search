# Job Search

Página personal para revisar cada día las ofertas de Game Design y UX de los estudios de videojuegos que me interesan.

## Cómo funciona

- `companies.json`: lista de empresas, su web de empleo y, cuando existe, el portal público del que se leen sus ofertas (Greenhouse, Lever, SmartRecruiters, Workable, Teamtailor, Ashby, Personio, Workday, Phenom, Avature, Pentasia, WordPress o la propia web de la empresa).
- `scripts/fetch_jobs.py`: consulta esos portales y genera `jobs.json`. Guarda las ofertas de diseño y UX de cualquier lugar, y todas las de Barcelona, España o remoto.
- `.github/workflows/update-jobs.yml`: ejecuta el script cada día a las 7:30 y a las 19:30 (hora de Barcelona) y guarda el resultado.
- `details.json`: descripción completa de las ofertas de diseño y UX en Barcelona o remoto.
- `picks.json`: el Top-10 de ofertas que mejor encajan, que Claude elige en una tarea programada a las 7:45 y a las 19:45.
- `applied.json`: candidaturas enviadas. Cada una lleva la clave `companyId:jobId`, el puesto, la fecha, el estado (`applied`, `process`, `offer`, `rejected` o `withdrawn`), en qué punto estoy, qué envié, el referral y los pasos del proceso. La página de ofertas las marca con «Aplicada».
- `applied.html`: página «Aplicadas», el histórico de candidaturas. Se genera desde `src/applied.html`.
- `people.json` y `people.html`: página «Personas», la gente de los estudios con la que quiero contactar. Cada persona lleva nombre, enlace a LinkedIn, empresa (`id` de `companies.json`), equipo o juego, cargo, por qué encaja, ubicación según su LinkedIn (`location`), grado de conexión (`degree`), estado (`todo`, `contacted`, `replied`, `talked` o `noreply`), fecha de contacto y notas. Un campo con valor `""` se muestra como «Falta», para acordarme de rellenarlo. Se genera desde `src/people.html`.
- `games.json` y `games.html`: página «Empresas y juegos», con los juegos de cada empresa y su web. Se genera desde `src/games.html`.
- `index.html`: la página. Lee `jobs.json`. Se genera desde `src/page.html` con `python scripts/build_page.py`.

- `icons/`: icono de la web (pestaña del navegador y pantalla de inicio del móvil).
- `logos/`: logos SVG guardados en el repositorio. En `companies.json`, el campo `logos` lista las imágenes que la página prueba en orden. Si ninguna carga, usa el favicon en alta resolución y, si tampoco, las iniciales.

Las empresas sin portal público aparecen solo con el enlace a su web de empleo.

## Puesta en marcha

1. Sube esta carpeta a un repositorio nuevo, por ejemplo `eduarajol/job-search`.
2. En el repositorio: **Settings → Pages → Build and deployment**, elige *Deploy from a branch*, rama `main`, carpeta `/ (root)`.
3. En **Actions**, abre *Update jobs* y pulsa **Run workflow** para la primera actualización.
4. La página queda en `https://eduarajol.github.io/job-search/`.

## Añadir o quitar empresas

Edita `companies.json`. Para una empresa sin portal público, deja `"source": null`.
