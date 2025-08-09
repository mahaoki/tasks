'use client';

import { useState } from 'react';
import api from '@/lib/api';
import { Form } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Alert } from '@/components/ui/alert';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await api.post('/auth/forgot-password', { email });
      setSent(true);
    } catch {
      setError('Falha ao enviar e-mail');
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Form onSubmit={handleSubmit} className="w-80">
        {sent ? (
          <Alert>E-mail enviado com instruções</Alert>
        ) : (
          <>
            {error && <Alert>{error}</Alert>}
            <Input
              placeholder="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <Button type="submit">Enviar</Button>
          </>
        )}
      </Form>
    </div>
  );
}
