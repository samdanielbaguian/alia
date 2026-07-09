'use client';

import DashboardLayout from '../../layout/DashboardLayout';

export default function DriversPage() {
  return (
    <DashboardLayout>
      <div className="page-header">
        <h1>👤 Drivers</h1>
        <p>Manage delivery drivers and their assignments</p>
      </div>

      <div className="content">
        <div className="card">
          <h2>Driver Management</h2>
          <p>Features coming soon:</p>
          <ul>
            <li>Add new drivers</li>
            <li>View driver details</li>
            <li>Monitor driver performance</li>
            <li>Assign deliveries</li>
          </ul>
        </div>
      </div>
    </DashboardLayout>
  );
}
