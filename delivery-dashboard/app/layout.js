import './globals.css'

export const metadata = {
  title: 'Delivery Dashboard',
  description: 'Shipment management and logistics tracking system',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  )
}
