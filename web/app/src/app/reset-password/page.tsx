'use client';

import { useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Form } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Alert } from '@/components/ui/alert';

export default function ResetPasswordPage() {
  const search = useSearchParams();
  const token = search.get('token');
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await api.post('/auth/reset-password', { token, password });
      router.push('/login');
    } catch {
      setError('Falha ao redefinir senha');
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Form onSubmit={handleSubmit} className="w-80">
        {error && <Alert>{error}</Alert>}
        <Input
          placeholder="Nova senha"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <Button type="submit">Redefinir</Button>
      </Form>
    </div>
  );
}
