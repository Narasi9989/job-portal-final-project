# GoSkill Frontend

React + Vite frontend for the GoSkill Job Portal service at `http://127.0.0.1:8000`.

## Run

```bash
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Service

Start the service first:

```bash
cd ../<service-folder>
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The frontend sends JWT tokens as `Authorization: Bearer <token>` for protected requests.
