import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";
import { WebSocketProvider } from "@/contexts/WebSocketContext";

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
          <WebSocketProvider>
            <main className="min-h-screen bg-gray-50">
              {children}
            </main>
          </WebSocketProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
