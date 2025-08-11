'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Spinner } from '@/components/ui/spinner';

export default function withAuth<T>(Component: React.ComponentType<T>) {
  return function AuthenticatedComponent(props: T) {
    const router = useRouter();
    const [checking, setChecking] = useState(true);

    useEffect(() => {
      const token = typeof window !== 'undefined' ? localStorage.getItem('accessToken') : null;
      if (!token) {
        router.replace('/login');
      } else {
        setChecking(false);
      }
    }, [router]);

    if (checking) {
      return (
        <div className="flex min-h-screen items-center justify-center">
          <Spinner />
        </div>
      );
    }

    return <Component {...props} />;
  };
}
