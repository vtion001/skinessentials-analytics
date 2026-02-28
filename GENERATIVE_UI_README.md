# Data Analyst - Generative UI Setup

This directory contains the Data Analyst agent with Generative UI capabilities using React and Tambo.

## Quick Start

### 1. Install API Server Dependencies

```bash
cd /Users/archerterminez/agents/data-analyst
pip3 install --break-system-packages fastapi uvicorn pydantic-settings
```

### 2. Start the API Server

```bash
cd /Users/archerterminez/agents/data-analyst
python3 api_server.py
```

The API will run on `http://localhost:8000`

### 3. Install Frontend Dependencies

```bash
cd /Users/archerterminez/agents/data-analyst/frontend
npm install
```

### 4. Start the Frontend

```bash
npm run dev
```

The frontend will run on `http://localhost:3000`

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   FastAPI       │────▶│   Data Analyst  │
│   (React/Tambo) │     │   Server        │     │   Agent         │
│   Port: 3000    │     │   Port: 8000    │     │   (Python)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/analyze` | Run analysis |
| GET | `/api/report/{site}` | Get latest report |
| GET | `/api/trends/{site}` | Get trend analysis |
| GET | `/api/ui/overview` | Overview for UI |
| GET | `/api/ui/channels/{channel}` | Channel data |

## Usage

1. Start the API server
2. Start the frontend
3. Enter a website URL in the frontend
4. Click "Analyze"
5. View interactive dashboards

## Generative UI Features

The frontend includes:
- **Dynamic Score Cards** - AI-selected metrics
- **Interactive Charts** - Recharts-powered
- **Chat Interface** - Ask questions about your data
- **Real-time Updates** - React Query for data fetching

## Tambo Integration

To fully enable generative UI with Tambo:

1. Get an Anthropic API key
2. Create a `.env` file in frontend:
   ```
   VITE_ANTHROPIC_API_KEY=your-api-key
   ```
3. Update `App.jsx` to use `GenerativeApp` component

## File Structure

```
data-analyst/
├── api_server.py          # FastAPI server
├── data_analyst.py        # Main agent
├── frontend/
│   ├── package.json       # Frontend dependencies
│   ├── vite.config.js     # Vite config
│   ├── index.html         # Entry HTML
│   └── src/
│       ├── main.jsx       # React entry
│       ├── App.jsx        # Main dashboard
│       ├── index.css      # Tailwind CSS
│       └── components/
│           └── GenerativeUI.jsx  # Tambo components
```

## Environment Variables

For the API server:
```
GSC_CREDENTIALS_PATH=path/to/credentials.json
GA4_PROPERTY_ID=your-property-id
META_ACCESS_TOKEN=your-token
```

For the frontend:
```
VITE_API_URL=http://localhost:8000
VITE_ANTHROPIC_API_KEY=your-key
```
