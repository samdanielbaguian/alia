# Delivery Dashboard - Frontend

A separate Next.js dashboard for delivery and shipment management.

## Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure API URL (Optional)
Create `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8001
```

### 3. Run Development Server
```bash
npm run dev
```

Frontend runs on: `http://localhost:3001`

## Available Scripts

- `npm run dev` - Start development server (port 3001)
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Project Structure

```
delivery-dashboard/
├── app/
│   ├── layout.js         # Root layout
│   ├── page.js           # Home page
│   └── dashboard/
│       ├── shipments/page.js
│       ├── deliveries/page.js
│       ├── drivers/page.js
│       └── tracking/page.js
├── components/           # React components (ready for expansion)
├── layout/
│   └── DashboardLayout.js # Main dashboard wrapper
├── styles/
│   ├── global.css        # Global styles
│   ├── layout.module.css # Layout styles
│   └── home.module.css   # Home page styles
├── utils/
│   └── api.js            # API client (axios)
├── public/               # Static assets
├── package.json
├── next.config.mjs
└── eslint.config.mjs
```

## Pages

### 🏠 Home Page (`/`)
- Overview and navigation to main sections
- Quick links to all modules

### 📦 Shipments (`/dashboard/shipments`)
- View all shipments
- Create new shipments
- Update shipment status
- Track shipment history

### 🚗 Deliveries (`/dashboard/deliveries`)
- View all deliveries
- Assign shipments to drivers
- Monitor delivery progress
- Handle failed deliveries

### 👤 Drivers (`/dashboard/drivers`)
- Manage driver profiles
- View driver performance
- Assign deliveries
- Track driver status

### 📍 Tracking (`/dashboard/tracking`)
- Real-time shipment tracking
- Search by tracking number
- View delivery timeline
- Get notifications

## Features

### Current (Phase 1)
- ✅ Clean, modern UI
- ✅ Navigation between modules
- ✅ API client setup (Axios)
- ✅ Responsive design

### Upcoming (Phase 2)
- 🔄 Full CRUD interfaces
- 🔄 Real-time tracking map
- 🔄 Data tables with filtering
- 🔄 Forms for creating shipments/drivers
- 🔄 State management (Zustand)

### Future (Phase 3)
- 🔄 Mobile responsive optimization
- 🔄 Dark mode
- 🔄 Advanced analytics dashboard
- 🔄 Export functionality

## API Integration

The frontend connects to the backend API at `http://localhost:8001` by default.

API client available in `utils/api.js`:
```javascript
import { shipmentAPI, deliveryAPI, driverAPI, trackingAPI } from '@/utils/api';

// Examples
const shipments = await shipmentAPI.getAll();
const driver = await driverAPI.getById(1);
const tracking = await trackingAPI.trackShipment('TRK-ABC123');
```

## Configuration

### Environment Variables

Create `.env.local` in the root:
```
NEXT_PUBLIC_API_URL=http://localhost:8001
```

## Notes

- This is a **separate, independent frontend** from the main alia dashboard
- Uses Next.js 14+ with React 18+
- Designed to connect to the delivery-backend service
- No shared state with the main app (completely isolated)
