import { Radar, Terminal, ListOrdered, History, Settings, Activity } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { cn } from '@/src/lib/utils';

export function SideNavBar() {
  const menuItems = [
    { name: 'Live Feed', icon: Radar, path: '/feed' },
    { name: 'System Logs', icon: Terminal, path: '/logs' },
    { name: 'Queue', icon: ListOrdered, path: '/queue' },
    { name: 'Archive', icon: History, path: '/archive' },
    { name: 'Settings', icon: Settings, path: '/settings' },
  ];

  return (
    <aside className="fixed left-0 top-14 h-[calc(100vh-3.5rem)] w-64 bg-slate-950 flex flex-col py-4 px-2 z-40 hidden lg:flex border-r border-slate-900/50">
      <div className="px-4 mb-8">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
          <div>
            <div className="text-slate-100 font-bold font-mono text-xs uppercase tracking-widest">OPERATOR_01</div>
            <div className="text-slate-500 font-mono text-[10px] uppercase tracking-widest">Terminal Active</div>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-1">
        {menuItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-4 py-3 font-mono text-xs uppercase tracking-widest transition-all duration-100",
                isActive
                  ? "bg-slate-800 text-slate-100 border-l-4 border-slate-400"
                  : "text-slate-500 hover:text-slate-300 hover:bg-slate-900/50"
              )
            }
          >
            <item.icon className="w-4 h-4" />
            <span>{item.name}</span>
          </NavLink>
        ))}
      </div>

      <div className="mt-auto px-4 py-4 border-t border-slate-900">
        <div className="bg-surface-container-low p-3 rounded-lg border border-outline-variant/10">
          <div className="text-[10px] text-outline uppercase font-bold mb-1 flex items-center justify-between">
            <span>System Load</span>
            <span className="font-mono">24%</span>
          </div>
          <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
            <div className="bg-primary h-full w-[24%]" />
          </div>
        </div>
      </div>
    </aside>
  );
}
