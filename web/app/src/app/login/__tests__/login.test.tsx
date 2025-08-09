import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import LoginPage from '../page';
import api from '@/lib/api';
import { useRouter } from 'next/navigation';

jest.mock('@/lib/api');
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

describe('LoginPage', () => {
  it('logins and redirects to dashboard', async () => {
    const push = jest.fn();
    (useRouter as jest.Mock).mockReturnValue({ push });
    (api.post as jest.Mock).mockResolvedValue({
      data: { accessToken: 'a', refreshToken: 'b' },
    });

    render(<LoginPage />);
    fireEvent.change(screen.getByPlaceholderText(/email/i), {
      target: { value: 'user@example.com' },
    });
    fireEvent.change(screen.getByPlaceholderText(/password/i), {
      target: { value: 'pass' },
    });
    fireEvent.click(screen.getByRole('button', { name: /login/i }));

    await waitFor(() => {
      expect(push).toHaveBeenCalledWith('/dashboard');
    });
  });
});
