'use client';

import { useEffect, useState } from 'react';
import { authService } from '@/service/authService';
import { mockCustomerProfiles } from '@/service/mockData';
import type { CustomerProfile } from '@/types/chat';

export default function CustomerProfile() {
  const [user, setUser] = useState(authService.getCurrentUser());
  const [profile, setProfile] = useState<CustomerProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    email: ''
  });

  useEffect(() => {
    // 加载用户资料
    if (user) {
      const customerProfile = mockCustomerProfiles[user.id];
      if (customerProfile) {
        setProfile(customerProfile);
        setFormData({
          name: user.name,
          phone: user.phone || '',
          email: user.email || ''
        });
      }
      setLoading(false);
    }
  }, [user]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // 模拟保存操作
    setTimeout(() => {
      setEditing(false);
      // 实际应用中这里会调用更新用户信息的API
    }, 500);
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-orange-500 border-t-transparent"></div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="p-6">
        <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
          <h3 className="mb-2 text-lg font-medium text-gray-800">未找到用户资料</h3>
          <p className="text-gray-500">请联系客服更新您的个人信息</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">个人中心</h1>
        <p className="text-gray-600">管理您的个人信息和账户设置</p>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-200 px-6 py-4">
          <div className="flex items-center">
            <div className="mr-4 h-16 w-16 overflow-hidden rounded-full">
              <img
                src={user?.avatar || '/avatars/default.png'}
                alt={user?.name}
                className="h-full w-full object-cover"
              />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-800">{user?.name}</h2>
              <p className="text-sm text-gray-500">顾客账号</p>
            </div>
            <button
              onClick={() => setEditing(!editing)}
              className="ml-auto rounded-md border border-orange-500 bg-white px-4 py-2 text-sm font-medium text-orange-500 hover:bg-orange-50"
            >
              {editing ? '取消编辑' : '编辑资料'}
            </button>
          </div>
        </div>

        <div className="p-6">
          {editing ? (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">姓名</label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">手机号</label>
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleInputChange}
                    className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">邮箱</label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
                  />
                </div>
              </div>
              <div className="flex justify-end">
                <button
                  type="submit"
                  className="rounded-md bg-orange-500 px-4 py-2 text-sm font-medium text-white hover:bg-orange-600"
                >
                  保存修改
                </button>
              </div>
            </form>
          ) : (
            <div className="space-y-6">
              <div>
                <h3 className="mb-4 text-lg font-medium text-gray-800">基本信息</h3>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="rounded-lg border border-gray-200 p-4">
                    <p className="text-sm font-medium text-gray-500">姓名</p>
                    <p className="mt-1 text-gray-800">{user?.name}</p>
                  </div>
                  <div className="rounded-lg border border-gray-200 p-4">
                    <p className="text-sm font-medium text-gray-500">年龄</p>
                    <p className="mt-1 text-gray-800">{profile.basicInfo.age}岁</p>
                  </div>
                  <div className="rounded-lg border border-gray-200 p-4">
                    <p className="text-sm font-medium text-gray-500">性别</p>
                    <p className="mt-1 text-gray-800">{profile.basicInfo.gender === 'male' ? '男' : '女'}</p>
                  </div>
                  <div className="rounded-lg border border-gray-200 p-4">
                    <p className="text-sm font-medium text-gray-500">手机号</p>
                    <p className="mt-1 text-gray-800">{profile.basicInfo.phone}</p>
                  </div>
                  <div className="rounded-lg border border-gray-200 p-4">
                    <p className="text-sm font-medium text-gray-500">邮箱</p>
                    <p className="mt-1 text-gray-800">{user?.email || '未设置'}</p>
                  </div>
                </div>
              </div>

              {profile.riskNotes && profile.riskNotes.length > 0 && (
                <div>
                  <h3 className="mb-4 text-lg font-medium text-gray-800">健康信息</h3>
                  <div className="space-y-3">
                    {profile.riskNotes.map((note, index) => (
                      <div key={index} className={`rounded-lg p-4 ${
                        note.level === 'high' ? 'bg-red-50 text-red-800' : 
                        note.level === 'medium' ? 'bg-yellow-50 text-yellow-800' : 
                        'bg-blue-50 text-blue-800'
                      }`}>
                        <p className="font-medium">{note.type}</p>
                        <p className="mt-1 text-sm">{note.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <h3 className="mb-4 text-lg font-medium text-gray-800">账户安全</h3>
                <div className="rounded-lg border border-gray-200 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-800">修改密码</p>
                      <p className="text-sm text-gray-500">定期更新密码可以提高账户安全性</p>
                    </div>
                    <button className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
                      修改
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 