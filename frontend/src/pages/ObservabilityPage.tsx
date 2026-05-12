import React from 'react';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';
import { ObservabilityHub } from '@/components/ObservabilityHub';

const ObservabilityPage: React.FC = () => {
  return (
    <div className="flex flex-col h-screen">
      <div className="border-b px-6 py-3 bg-background">
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href="/">SimHPC</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage>Kernel Observatory</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </div>
      <div className="flex-1 overflow-hidden">
        <ObservabilityHub />
      </div>
    </div>
  );
};

export default ObservabilityPage;
