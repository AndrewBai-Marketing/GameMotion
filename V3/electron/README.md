# GameMotion Electron Wrapper

Place this `electron/` folder alongside your `backend/` and `frontend/` folders.

## Dev
1) Backend
```
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install fastapi "uvicorn[standard]"
```
Ensure your backend exposes **GET /health** on 127.0.0.1:8000.

2) Frontend
```
cd ..\frontend
npm i
# .env.local -> NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
```

3) Electron
```
cd ..\electron
npm i
npm run dev
```

## Production
- **Static**: `next.config.js` → `output: 'export'`, then `npx next export`, Electron will load `frontend/out/index.html`.
- **Server**: `npm run build` (frontend), then `npm run build` (electron) to package and run `next start`.
