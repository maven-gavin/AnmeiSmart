import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";
import { Toaster } from 'react-hot-toast';
import { StagewiseToolbar } from '@stagewise/toolbar-next';
import ReactPlugin from '@stagewise-plugins/react';

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "安美智享 - 医美智能服务平台",
  description: "安美智享 - 专为医美机构定制的AI智能服务平台",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <AuthProvider>
          <main className="min-h-screen bg-gray-50">
            {children}
          </main>
          <Toaster 
            position="top-center"
            toastOptions={{
              duration: 3000,
              style: {
                background: '#FFF',
                color: '#374151',
                borderRadius: '8px',
                border: '1px solid #E5E7EB',
                fontSize: '14px',
              },
              success: {
                iconTheme: {
                  primary: '#F97316', // 橘色
                  secondary: '#FFF',
                },
              },
              error: {
                iconTheme: {
                  primary: '#EF4444',
                  secondary: '#FFF',
                },
              },
            }}
          />
          <StagewiseToolbar 
            config={{
              plugins: [ReactPlugin],
            }}
          />
        </AuthProvider>
      </body>
    </html>
  );
}
