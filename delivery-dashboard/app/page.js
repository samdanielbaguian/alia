'use client';

import Link from 'next/link';
import styles from '../styles/home.module.css';

export default function Home() {
  return (
    <main className={styles.container}>
      <div className={styles.header}>
        <h1>🚚 Delivery Management System</h1>
        <p>Shipment tracking and logistics management</p>
      </div>

      <div className={styles.grid}>
        <Link href="/dashboard/shipments" className={styles.card}>
          <div>
            <h2>📦 Shipments</h2>
            <p>Manage and track all shipments</p>
          </div>
        </Link>

        <Link href="/dashboard/deliveries" className={styles.card}>
          <div>
            <h2>🚗 Deliveries</h2>
            <p>View delivery progress and status</p>
          </div>
        </Link>

        <Link href="/dashboard/drivers" className={styles.card}>
          <div>
            <h2>👤 Drivers</h2>
            <p>Manage delivery drivers and assignments</p>
          </div>
        </Link>

        <Link href="/dashboard/tracking" className={styles.card}>
          <div>
            <h2>📍 Tracking</h2>
            <p>Real-time shipment tracking</p>
          </div>
        </Link>
      </div>

      <footer className={styles.footer}>
        <p>Delivery Management System v1.0 | Separate from main app</p>
      </footer>
    </main>
  );
}
