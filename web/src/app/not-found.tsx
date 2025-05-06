import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4 text-center">
      <div className="mb-6 text-9xl font-bold text-orange-500">404</div>
      <h1 className="mb-4 text-2xl font-bold text-gray-900">页面未找到</h1>
      <p className="mb-8 max-w-md text-gray-600">
        很抱歉，您访问的页面可能已被移除、名称已更改或暂时不可用。
      </p>
      <Link
        href="/"
        className="rounded-lg bg-orange-500 px-6 py-3 font-medium text-white transition duration-300 hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2"
      >
        返回首页
      </Link>
    </div>
  );
} 