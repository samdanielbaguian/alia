'use client';

import DashboardLayout from '../../layout/DashboardLayout';

export default function TrackingPage() {
  return (
    <DashboardLayout>
      <div className="page-header">
        <h1>📍 Tracking</h1>
        <p>Real-time shipment and delivery tracking</p>
      </div>

      <div className="content">
        <div className="card">
          <h2>Shipment Tracking</h2>
          <p>Features coming soon:</p>
          <ul>
            <li>Search by tracking number</li>
            <li>Real-time location updates</li>
            <li>Delivery timeline</li>
            <li>Notifications</li>
          </ul>
        </div>
      </div>
    </DashboardLayout>
  );
}
