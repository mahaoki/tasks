'use client';

import { useEffect, useState, FormEvent } from 'react';
import withAuth from '@/components/withAuth';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface Role {
  name: string;
}

interface User {
  id: string;
  email: string;
  full_name: string | null;
  roles: Role[];
}

function UsersAdminPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  const [form, setForm] = useState({
    id: '' as string | null,
    email: '',
    full_name: '',
    roles: ['user'] as string[],
  });

  useEffect(() => {
    void fetchUsers();
    void fetchRoles();
  }, []);

  async function fetchUsers() {
    const res = await api.get('/users');
    setUsers(res.data);
  }

  async function fetchRoles() {
    const res = await api.get('/roles');
    setRoles(res.data.map((r: Role) => r.name));
  }

  function startEdit(user: User) {
    setForm({
      id: user.id,
      email: user.email,
      full_name: user.full_name || '',
      roles: user.roles.map((r) => r.name),
    });
  }

  function resetForm() {
    setForm({ id: '', email: '', full_name: '', roles: ['user'] });
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (form.id) {
      await api.patch(`/users/${form.id}`, {
        full_name: form.full_name,
        roles: form.roles,
      });
    } else {
      await api.post('/users', {
        email: form.email,
        full_name: form.full_name,
        roles: form.roles,
        sectors: [],
      });
    }
    resetForm();
    await fetchUsers();
  }

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-bold">User Management</h1>
      <form onSubmit={onSubmit} className="space-y-2 max-w-md">
        {!form.id && (
          <Input
            placeholder="Email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
        )}
        <Input
          placeholder="Full name"
          value={form.full_name}
          onChange={(e) => setForm({ ...form, full_name: e.target.value })}
        />
        <select
          multiple
          className="border rounded p-2 w-full"
          value={form.roles}
          onChange={(e) =>
            setForm({
              ...form,
              roles: Array.from(e.target.selectedOptions).map((o) => o.value),
            })
          }
        >
          {roles.map((role) => (
            <option key={role} value={role}>
              {role}
            </option>
          ))}
        </select>
        <Button type="submit">{form.id ? 'Update' : 'Create'}</Button>
        {form.id && (
          <Button type="button" variant="ghost" onClick={resetForm}>
            Cancel
          </Button>
        )}
      </form>
      <ul className="space-y-1">
        {users.map((u) => (
          <li key={u.id} className="flex justify-between items-center">
            <span>{u.email}</span>
            <Button type="button" variant="outline" onClick={() => startEdit(u)}>
              Edit
            </Button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default withAuth(UsersAdminPage);
