import { Bell, Settings, User } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { cn } from '@/src/lib/utils';

export function TopNavBar() {
  const navLinks = [
    { name: 'Dashboard', path: '/' },
    { name: 'New Contacts', path: '/contacts' },
    { name: 'Errors', path: '/errors' },
    { name: 'Alerts', path: '/alerts' },
  ];

  return (
    <nav className="fixed top-0 w-full z-50 bg-slate-900/95 backdrop-blur-md border-b border-slate-800/50 flex items-center justify-between px-6 h-14">
      <div className="flex items-center gap-8">
        <span className="text-lg font-black tracking-tighter text-slate-100 uppercase">TACTICAL_INTEL</span>
        <div className="hidden md:flex items-center gap-6">
          {navLinks.map((link) => (
            <NavLink
              key={link.path}
              to={link.path}
              className={({ isActive }) =>
                cn(
                  "text-sm font-sans tracking-tight transition-colors duration-150",
                  isActive 
                    ? "text-slate-100 border-b-2 border-slate-100 pb-1 font-bold" 
                    : "text-slate-400 font-medium hover:text-slate-200"
                )
              }
            >
              {link.name}
            </NavLink>
          ))}
        </div>
      </div>
      
      <div className="flex items-center gap-4">
        <div className="relative group p-2 cursor-pointer text-slate-400 hover:text-slate-200 transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 block h-2 w-2 rounded-full bg-error border-2 border-slate-900"></span>
        </div>
        <div className="p-2 cursor-pointer text-slate-400 hover:text-slate-200 transition-colors">
          <Settings className="w-5 h-5" />
        </div>
        <div className="h-8 w-8 rounded-full bg-surface-container-highest border border-outline-variant flex items-center justify-center overflow-hidden">
          <img 
            alt="Operator" 
            className="w-full h-full object-cover" 
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuCj4G9HxLEujKI-wgjb-SfgPepbF3pB0-bfvNjphMuBB_NQFEIyUMUJwNa5_La5ntUzewkZGNmy2N8Jv2Qh1u3YWKAEgYcwRGrwxrNV9DVd-R5JUfp67KeIuL8cXDUTNTmGoZS0TcODJWVfxN3g7wK3C5jKZ8wXF12N8tPtG7aUU60m8vOL7zESaqEoW3PHDNISIZwEaG262Fakut3aaxlqlX2MpQKqbHVjcQqXHYU0dNCK3APq4XR2mLFuF9WJWhkPmDDUbkf1scY"
            referrerPolicy="no-referrer"
          />
        </div>
      </div>
    </nav>
  );
}
