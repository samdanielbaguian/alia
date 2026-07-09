'use client';

import DashboardLayout from '../../layout/DashboardLayout';

export default function ShipmentsPage() {
  return (
    <DashboardLayout>
      <div className="page-header">
        <h1>📦 Shipments</h1>
        <p>Create, manage, and monitor all shipments</p>
      </div>
      
      <div className="content">
        <div className="card">
          <h2>Shipment Management</h2>
          <p>Features coming soon:</p>
          <ul>
            <li>Create new shipments</li>
            <li>View all shipments</li>
            <li>Update shipment status</li>
            <li>Bulk operations</li>
          </ul>
        </div>
      </div>
    </DashboardLayout>
  );
}
