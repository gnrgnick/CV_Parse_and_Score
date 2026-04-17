import { motion } from 'motion/react';
import { Download, Activity, Clock, Database, CreditCard, Heart } from 'lucide-react';
import { cn } from '@/src/lib/utils';

export function Dashboard() {
  const stats = [
    { label: 'Queue Depth', value: '3', sub: '+1 from prev hour', color: 'primary' },
    { label: 'CVs Processed', value: '47', sub: 'Daily target: 200', color: 'primary' },
    { label: 'Avg Proc. Time', value: '2m 14s', sub: '▲ 0.4s lag detected', color: 'error' },
    { label: 'API Spend (Day)', value: '£3.47', sub: 'Est. day end: £12.40', color: 'primary' },
    { label: 'API Spend (Mo)', value: '£82.19', sub: 'Budget cap: £500.00', color: 'primary' },
    { label: 'Inbox Heartbeat', value: '12s ago', sub: 'Connection: Stable', color: 'primary', heartbeat: true },
  ];

  const chartData = [12, 18, 10, 15, 28, 20, 12, 22, 14, 18, 8, 16];

  const activities = [
    { time: '14:23:07', text: 'Scored J. Nguyen — ', badge: '172/210', badgeColor: 'primary' },
    { time: '14:19:42', text: 'New Inbox sync initialized' },
    { time: '14:15:11', text: 'Scored M. Thompson — ', badge: '145/210', badgeColor: 'secondary' },
    { time: '14:02:59', text: 'API_ERROR: Rate limit warning (OpenAI)', error: true },
    { time: '13:58:34', text: 'Scored K. Ali — ', badge: '198/210', badgeColor: 'primary' },
    { time: '13:42:10', text: 'System integrity check: PASS' },
    { time: '13:30:05', text: 'Scored L. Zhang — ', badge: '82/210', badgeColor: 'error' },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-on-surface">Service Dashboard</h1>
          <p className="text-[10px] text-on-surface-variant font-mono uppercase mt-1 tracking-widest leading-none">
            Live status protocol: Active • Cluster: EU-WEST-1
          </p>
        </div>
        <button className="bg-surface-container-highest px-3 py-1.5 rounded border border-outline-variant text-[11px] font-mono uppercase tracking-wider hover:bg-surface-bright transition-colors">
          [Export_Data]
        </button>
      </header>

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-surface-container-low p-4 rounded border-b border-outline-variant/20">
            <div className="text-[10px] text-outline uppercase font-bold tracking-widest mb-2 whitespace-nowrap">{stat.label}</div>
            <div className="flex items-center gap-2">
              <div className="text-2xl font-mono text-on-surface">{stat.value}</div>
              {stat.heartbeat && <div className="h-2 w-2 rounded-full bg-primary shadow-[0_0_8px_rgba(193,199,207,0.6)] animate-pulse" />}
            </div>
            <div className={`text-[10px] font-mono mt-1 ${stat.color === 'error' ? 'text-error/60' : 'text-primary/60'}`}>
              {stat.sub}
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="bg-surface-container p-6 rounded relative overflow-hidden">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-[10px] font-bold uppercase tracking-widest text-outline">Last 24h throughput</h2>
            <span className="font-mono text-[10px] text-on-surface-variant">Units: CV/HR</span>
          </div>
          <div className="h-64 flex items-end justify-between gap-1 border-l border-b border-outline-variant/30 pb-2 pl-2">
            {chartData.map((val, i) => (
              <motion.div
                key={i}
                initial={{ height: 0 }}
                animate={{ height: `${(val / 30) * 100}%` }}
                transition={{ duration: 1, delay: i * 0.05 }}
                className={cn(
                  "flex-1 transition-colors relative group/bar",
                  val === 28 ? "bg-primary/80 hover:bg-primary/90" : "bg-primary/20 hover:bg-primary/40"
                )}
              >
                {val === 28 && (
                  <div className="absolute -top-6 left-1/2 -translate-x-1/2 font-mono text-[9px] opacity-100">{val}</div>
                )}
                <div className="absolute -top-6 left-1/2 -translate-x-1/2 font-mono text-[9px] opacity-0 group-hover/bar:opacity-100 transition-opacity whitespace-nowrap">
                  {val}
                </div>
              </motion.div>
            ))}
          </div>
          <div className="flex justify-between mt-4 font-mono text-[10px] text-outline px-2">
            <span>00:00</span>
            <span>06:00</span>
            <span>12:00</span>
            <span>18:00</span>
            <span>23:59</span>
          </div>
          <div className="absolute inset-0 pointer-events-none opacity-[0.03] bg-[linear-gradient(rgba(255,255,255,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.1)_1px,transparent_1px)] bg-[size:20px_20px]" />
        </section>

        <section className="bg-surface-container p-6 rounded flex flex-col h-full max-h-[400px]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-[10px] font-bold uppercase tracking-widest text-outline">Recent activity log</h2>
            <div className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
              <span className="font-mono text-[10px] text-on-surface-variant uppercase tracking-tighter">Live Monitor</span>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto space-y-0.5 pr-2 custom-scrollbar">
            {activities.map((log, i) => (
              <div key={i} className="flex items-start gap-4 py-2 px-3 hover:bg-surface-container-high rounded transition-colors group">
                <span className="font-mono text-[11px] text-outline whitespace-nowrap mt-0.5">{log.time}</span>
                <div className="flex-1">
                  <span className={cn("font-mono text-[11px]", log.error ? "text-error" : "text-on-surface")}>
                    {log.text}
                  </span>
                  {log.badge && (
                    <span className={cn(
                      "px-1.5 py-0.5 rounded font-mono text-[10px] ml-1",
                      log.badgeColor === 'primary' ? "bg-primary-container text-on-primary-container" :
                      log.badgeColor === 'secondary' ? "bg-secondary-container text-on-secondary-container" :
                      "bg-error-container text-on-error-container"
                    )}>
                      {log.badge}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="bg-surface-container-low p-4 rounded-lg flex items-center justify-between border border-outline-variant/10">
        <div className="flex flex-col md:flex-row md:items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-outline font-bold uppercase">Uptime</span>
            <span className="font-mono text-xs text-on-surface">14d 02h 11m</span>
          </div>
          <div className="flex items-center gap-2 md:border-l md:border-outline-variant md:pl-6">
            <span className="text-[10px] text-outline font-bold uppercase">Nodes</span>
            <span className="font-mono text-xs text-on-surface">6/6 [ONLINE]</span>
          </div>
          <div className="flex items-center gap-2 md:border-l md:border-outline-variant md:pl-6">
            <span className="text-[10px] text-outline font-bold uppercase">Version</span>
            <span className="font-mono text-xs text-on-surface">v2.4.1-stable</span>
          </div>
        </div>
        <div className="hidden sm:block text-[10px] font-mono text-outline uppercase tracking-widest">
          [Secure_Protocol_Encrypted]
        </div>
      </section>
    </div>
  );
}
