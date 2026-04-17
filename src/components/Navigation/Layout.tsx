import { ReactNode } from 'react';
import { TopNavBar } from './TopNavBar';
import { SideNavBar } from './SideNavBar';

interface LayoutProps {
  children: ReactNode;
  showSidebar?: boolean;
}

export function Layout({ children, showSidebar = true }: LayoutProps) {
  return (
    <div className="min-h-screen bg-surface selection:bg-primary/30">
      <TopNavBar />
      {showSidebar && <SideNavBar />}
      <main className={showSidebar ? "lg:ml-64 pt-14 min-h-screen" : "pt-14 min-h-screen"}>
        <div className="p-6 max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
