'use client';

import Link from 'next/link';
import styles from '../styles/layout.module.css';

export default function DashboardLayout({ children }) {
  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <div className={styles.logo}>
          <h2>🚚 Delivery</h2>
        </div>

        <nav className={styles.nav}>
          <Link href="/dashboard/shipments" className={styles.navLink}>
            📦 Shipments
          </Link>
          <Link href="/dashboard/deliveries" className={styles.navLink}>
            🚗 Deliveries
          </Link>
          <Link href="/dashboard/drivers" className={styles.navLink}>
            👤 Drivers
          </Link>
          <Link href="/dashboard/tracking" className={styles.navLink}>
            📍 Tracking
          </Link>
        </nav>

        <div className={styles.footer}>
          <p>v1.0</p>
          <small>Separate App</small>
        </div>
      </aside>

      <main className={styles.main}>
        <header className={styles.header}>
          <div className={styles.headerContent}>
            <h1>Delivery Dashboard</h1>
            <span className={styles.status}>🟢 System Active</span>
          </div>
        </header>

        <div className={styles.content}>
          {children}
        </div>
      </main>
    </div>
  );
}
