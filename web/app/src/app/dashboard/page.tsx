'use client';

import { Badge } from '@/components/ui/badge';
import withAuth from '@/components/withAuth';

function DashboardPage() {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold flex items-center gap-2">
        Dashboard <Badge>Beta</Badge>
      </h1>
    </div>
  );
}

export default withAuth(DashboardPage);
