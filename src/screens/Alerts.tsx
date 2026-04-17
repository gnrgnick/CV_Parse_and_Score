import { RefreshCw, Plus, MoreVertical, FlaskConical, History } from 'lucide-react';
import { cn } from '@/src/lib/utils';

export function Alerts() {
  const alertConfigs = [
    { name: 'Processor stalled 15+ min', label: 'CRITICAL_HARDWARE', channel: 'Both', recipients: 'admin@tactical.io, ops_duty@cell.net', active: true },
    { name: 'Unauthorized Login Attempt', label: 'SECURITY_BREACH', channel: 'SMS', recipients: '+44 7700 900231', active: true },
    { name: 'Queue depth > 1000', label: 'THROUGHPUT_DELAY', channel: 'Email', recipients: 'dev_team@tactical.io', active: false },
  ];

  const logs = [
    { time: '2023-10-24 14:22:01', event: 'Queue depth exceeded (1242/1000)', channel: 'EMAIL', status: 'DELIVERED', type: 'success' },
    { time: '2023-10-24 14:15:44', event: 'Auth failure: IP 192.168.1.44', channel: 'SMS', status: 'FAILED_CARRIER', type: 'error' },
    { time: '2023-10-24 13:58:12', event: 'Manual Test: Stalled Processor', channel: 'BOTH', status: 'DELIVERED', type: 'success' },
    { time: '2023-10-24 13:30:05', event: 'Queue depth normal recovery', channel: '--', status: 'LOG_ONLY', type: 'idle' },
    { time: '2023-10-24 12:45:18', event: 'Weekly status summary generated', channel: 'EMAIL', status: 'DELIVERED', type: 'success' },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-on-surface">System Alert Configuration</h1>
          <p className="text-on-surface-variant text-sm mt-1">Define triggers, delivery channels, and notification routing parameters.</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 bg-surface-container-highest border border-outline-variant px-4 py-2 text-xs font-mono uppercase tracking-widest hover:bg-surface-bright transition-colors">
            <RefreshCw className="w-4 h-4" /> [SYNC_CONFIG]
          </button>
          <button className="flex items-center gap-2 bg-primary text-on-primary px-4 py-2 text-xs font-bold uppercase tracking-widest hover:opacity-90 transition-opacity">
            <Plus className="w-4 h-4" /> NEW_ALERT
          </button>
        </div>
      </div>

      <section className="bg-surface-container-low border border-outline-variant/20 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container border-b border-outline-variant/30">
                <th className="px-6 py-4 text-[10px] font-mono uppercase tracking-[0.2em] text-on-surface-variant">Status</th>
                <th className="px-6 py-4 text-[10px] font-mono uppercase tracking-[0.2em] text-on-surface-variant">Alert Name</th>
                <th className="px-6 py-4 text-[10px] font-mono uppercase tracking-[0.2em] text-on-surface-variant">Channel</th>
                <th className="px-6 py-4 text-[10px] font-mono uppercase tracking-[0.2em] text-on-surface-variant">Recipients</th>
                <th className="px-6 py-4 text-right text-[10px] font-mono uppercase tracking-[0.2em] text-on-surface-variant">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/10">
              {alertConfigs.map((config, i) => (
                <tr key={i} className="hover:bg-surface-container-high transition-colors group">
                  <td className="px-6 py-4">
                    <div className={cn(
                      "w-9 h-5 rounded-full relative transition-colors cursor-pointer",
                      config.active ? "bg-primary-container" : "bg-surface-container-highest"
                    )}>
                      <div className={cn(
                        "absolute top-[2px] w-4 h-4 rounded-full transition-all",
                        config.active ? "bg-primary left-[18px]" : "bg-on-surface-variant left-[2px]"
                      )} />
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col">
                      <span className="font-semibold text-on-surface">{config.name}</span>
                      <span className="text-[10px] font-mono text-outline uppercase tracking-wider">{config.label}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <select className="bg-surface-container-lowest border-b border-outline-variant text-xs font-mono text-on-surface py-1 outline-none focus:border-primary transition-colors pr-8 cursor-pointer">
                      <option selected={config.channel === 'SMS'}>SMS</option>
                      <option selected={config.channel === 'Email'}>Email</option>
                      <option selected={config.channel === 'Both'}>Both</option>
                    </select>
                  </td>
                  <td className="px-6 py-4">
                    <input 
                      className="w-full bg-transparent border-b border-transparent focus:border-outline-variant text-xs font-mono text-outline px-0 py-1 outline-none transition-all focus:text-on-surface" 
                      defaultValue={config.recipients}
                    />
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="text-outline hover:text-primary transition-colors">
                      <MoreVertical className="w-5 h-5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-surface-container border border-outline-variant/20 rounded-lg p-6 flex flex-col">
          <h3 className="text-xs font-mono uppercase tracking-widest text-primary mb-4 flex items-center gap-2">
            <FlaskConical className="w-4 h-4" /> Diagnostics
          </h3>
          <p className="text-sm text-on-surface-variant mb-6 leading-relaxed flex-1">
            Trigger a synthetic alert event to verify notification routing and delivery status across all configured channels.
          </p>
          <div className="space-y-4">
            <div>
              <label className="block text-[10px] font-mono text-outline uppercase tracking-wider mb-2">Target Template</label>
              <select className="w-full bg-surface-container-lowest border border-outline-variant text-xs font-mono text-on-surface p-2 rounded outline-none focus:ring-1 focus:ring-primary">
                {alertConfigs.map((c, i) => (
                  <option key={i}>{c.name}</option>
                ))}
              </select>
            </div>
            <button className="w-full bg-primary-container text-on-primary-container py-3 rounded text-[10px] font-mono uppercase font-bold tracking-widest hover:bg-primary-dim hover:text-on-primary transition-all active:scale-[0.98]">
              SEND_TEST_ALERT
            </button>
          </div>
        </div>

        <div className="md:col-span-2 bg-surface-container border border-outline-variant/20 rounded-lg flex flex-col h-[400px]">
          <div className="px-6 py-4 border-b border-outline-variant/20 flex justify-between items-center bg-surface-container-high/50">
            <h3 className="text-xs font-mono uppercase tracking-widest text-on-surface-variant flex items-center gap-2">
              <History className="w-4 h-4" /> Recent_Alerts_Log
            </h3>
            <span className="text-[10px] font-mono text-primary animate-pulse tracking-tighter uppercase whitespace-nowrap">Live Feed</span>
          </div>
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            <table className="w-full text-left border-collapse">
              <thead className="sticky top-0 bg-surface-container-high z-10">
                <tr className="border-b border-outline-variant/10">
                  <th className="px-6 py-2 text-[9px] font-mono uppercase text-outline">Timestamp</th>
                  <th className="px-6 py-2 text-[9px] font-mono uppercase text-outline">Event</th>
                  <th className="px-6 py-2 text-[9px] font-mono uppercase text-outline">Channel</th>
                  <th className="px-6 py-2 text-[9px] font-mono uppercase text-outline">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/5">
                {logs.map((log, i) => (
                  <tr key={i} className={cn(
                    "hover:bg-surface-container-highest transition-colors",
                    i > 2 && "opacity-60"
                  )}>
                    <td className="px-6 py-3 font-mono text-[11px] text-on-surface-variant whitespace-nowrap">{log.time}</td>
                    <td className={cn("px-6 py-3 text-xs", log.type === 'error' ? "text-error font-semibold" : "text-on-surface")}>
                      {log.event}
                    </td>
                    <td className="px-6 py-3">
                      {log.channel !== '--' && (
                        <span className="bg-surface-container-highest px-2 py-0.5 rounded text-[10px] font-mono text-tertiary-dim">
                          {log.channel}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-3">
                      <div className={cn(
                        "flex items-center gap-1.5 text-[10px] font-mono",
                        log.type === 'success' ? "text-primary" : log.type === 'error' ? "text-error" : "text-outline"
                      )}>
                        {log.type !== 'idle' && <span className={cn("w-1.5 h-1.5 rounded-full", log.type === 'success' ? "bg-primary" : "bg-error")} />}
                        {log.status}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
