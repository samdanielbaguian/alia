'use client';

import DashboardLayout from '../../layout/DashboardLayout';

export default function DeliveriesPage() {
  return (
    <DashboardLayout>
      <div className="page-header">
        <h1>🚗 Deliveries</h1>
        <p>Track and manage delivery operations</p>
      </div>

      <div className="content">
        <div className="card">
          <h2>Delivery Management</h2>
          <p>Features coming soon:</p>
          <ul>
            <li>View all deliveries</li>
            <li>Assign shipments to drivers</li>
            <li>Monitor delivery progress</li>
            <li>Mark deliveries complete</li>
          </ul>
        </div>
      </div>
    </DashboardLayout>
  );
}
