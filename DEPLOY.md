# Publicar cambios - Museo Pumapungo

Guia minima para traer cambios al servidor y reconstruir los contenedores.

---

## Pasos

```bash
# 1. Entrar al servidor
ssh srv-serendipia@pumapungo

# 2. Ir al repo
cd ~/Tesis

# 3. Traer cambios
git pull origin main

# 4. Reconstruir y levantar
docker compose up -d --build

# 5. Ver que este arriba
docker compose ps
docker compose logs --tail=50 backend
```

Listo. Frontend: `http://pumapungo/pumapungo`.

---

## Si `git pull` falla por cambios locales

```bash
git diff <archivo>   # ver que cambio
```

- Diff chico y legitimo -> `git stash && git pull origin main && git stash pop`
- Diff grande / archivo viejo -> `git checkout -- <archivo> && git pull origin main`

---

## Contexto (reverse proxy)

El frontend se compila con `VITE_API_URL=/pumapungo/api/v1`, asi que el reverse
proxy del host enruta:

- `/pumapungo/api/*` -> contenedor `backend:8000`
- `/pumapungo/*`     -> contenedor `frontend:80`

Si cambias el prefijo `/pumapungo`, hay que ajustar **los tres**: `docker-compose.yaml`
(build arg `VITE_API_URL`), la config del reverse proxy, y el Router del frontend.

---

## Casos extremos: rebuild sin cache

Si el `up -d --build` no refleja los cambios (layer cache o deps nuevas en
`requirements.txt` / `package.json`), fuerza rebuild completo:

```bash
# Solo frontend
docker compose build --no-cache frontend
docker compose up -d frontend

# Solo backend
docker compose build --no-cache backend
docker compose up -d backend

# Todo
docker compose build --no-cache
docker compose up -d --force-recreate
```

Si sigue sin verse, limpia imagenes huerfanas:

```bash
docker image prune -a --filter "until=168h"
docker builder prune -a
```

---

## Si algo falla

```bash
# Logs completos
docker compose logs -f backend

# Rollback al commit anterior
git log --oneline -5
git reset --hard <commit-hash>
docker compose up -d --build
```
