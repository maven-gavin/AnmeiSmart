import RoleLayout from '@/components/layout/RoleLayout';

export default function ConsultantLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RoleLayout requiredRole="consultant">
      {children}
    </RoleLayout>
  );
} 