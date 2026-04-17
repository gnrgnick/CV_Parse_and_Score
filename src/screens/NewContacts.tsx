import { ExternalLink, Filter, Calendar, User, UserMinus } from 'lucide-react';
import { cn } from '@/src/lib/utils';

export function NewContacts() {
  const contacts = [
    { name: 'Dr. Alistair Vance', priority: true, id: 'ID_88429_ENG', score: '198/210', match: '94.2%', band: 'PASS', specialisms: ['Secondary 28/30', 'SEN 18/20'], time: '3m ago' },
    { name: 'Sarah McAllister', priority: false, id: 'ID_77312_MATH', score: '164/210', match: '78.1%', band: 'PASS', specialisms: ['Primary 26/30', 'ESL 14/20'], time: '12m ago' },
    { name: "Thomas O'Neil", priority: false, id: 'ID_66201_HIST', score: '132/210', match: '62.8%', band: 'REVIEW', specialisms: ['History 22/30', 'Admin 10/20'], time: '25m ago' },
    { name: 'Imogen Clarke', priority: false, id: 'ID_99014_SCI', score: '42/210', match: '20.0%', band: 'FAIL', specialisms: ['Science 08/30', 'Exp 05/20'], time: '48m ago', failed: true },
    { name: 'Benjamin Foster', priority: true, id: 'ID_55102_PE', score: '186/210', match: '88.5%', band: 'PASS', specialisms: ['Secondary 27/30', 'Leadership 16/20'], time: '1h ago' },
  ];

  const stats = [
    { label: 'Total_Scanned_Today', value: '1,204', sub: '+12.5% VS PREV_PERIOD', trend: 'up' },
    { label: 'Awaiting_Review', value: '142', sub: 'AVG_WAIT: 4.2M', tertiary: true },
    { label: 'Auto_Rejection_Rate', value: '34%', sub: 'MATCHING_DS_ALGO_V4' },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h1 className="text-2xl font-bold tracking-tight text-on-surface flex items-center gap-3">
          NEW_CONTACTS
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 bg-primary-container text-on-primary-container rounded text-[10px] font-mono tracking-widest uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            Updated 14s ago
          </span>
        </h1>

        <div className="flex flex-wrap items-center gap-3 bg-surface-container-low p-1.5 rounded-lg border border-outline-variant/10">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-surface-container-high rounded border border-outline-variant/20">
            <span className="text-[10px] font-mono uppercase text-outline">Score_Range</span>
            <div className="w-24 h-1 bg-outline-variant/30 rounded-full relative">
              <div className="absolute left-1/4 right-0 h-full bg-primary rounded-full"></div>
              <div className="absolute left-1/4 top-1/2 -translate-y-1/2 w-2 h-2 bg-on-surface rounded-full"></div>
            </div>
            <span className="text-[10px] font-mono text-primary">50-100</span>
          </div>
          
          <div className="relative">
            <select className="appearance-none bg-surface-container-high border border-outline-variant/20 text-on-surface text-[10px] font-mono uppercase px-3 py-1.5 pr-8 rounded outline-none cursor-pointer">
              <option>BAND: ALL</option>
              <option>BAND: PASS</option>
              <option>BAND: REVIEW</option>
              <option>BAND: FAIL</option>
            </select>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 bg-surface-container-high rounded border border-outline-variant/20">
            <Calendar className="w-3 h-3 text-outline" />
            <span className="text-[10px] font-mono uppercase text-on-surface">Last 24H</span>
          </div>

          <button className="bg-primary text-on-primary px-4 py-1.5 rounded text-[10px] font-bold uppercase tracking-widest hover:brightness-110 transition-all flex items-center gap-2">
            <Filter className="w-3 h-3" />
            Apply_Filters
          </button>
        </div>
      </div>

      <div className="bg-surface-container-low rounded-xl overflow-hidden border border-outline-variant/10">
        <div className="hidden lg:grid grid-cols-12 px-4 py-3 bg-surface-container text-[10px] font-mono uppercase text-outline tracking-widest border-b border-outline-variant/20">
          <div className="col-span-4">Candidate_Identity</div>
          <div className="col-span-2 text-center">Score_Index</div>
          <div className="col-span-2 text-center">Status_Band</div>
          <div className="col-span-3">Primary_Specialisms</div>
          <div className="col-span-1 text-right">Action</div>
        </div>

        <div className="divide-y divide-outline-variant/10">
          {contacts.map((contact) => (
            <div key={contact.id} className="grid grid-cols-1 md:grid-cols-12 px-4 py-4 items-center hover:bg-surface-container-high transition-colors group cursor-pointer border-b border-outline-variant/10 lg:border-none">
              <div className="col-span-4 flex items-center gap-3">
                <div className="w-10 h-10 bg-surface-container-highest flex items-center justify-center rounded border border-outline-variant/30 flex-shrink-0">
                  {contact.failed ? <UserMinus className="w-5 h-5 text-outline" /> : <User className="w-5 h-5 text-outline" />}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-on-surface">{contact.name}</span>
                    {contact.priority && (
                      <span className="px-1.5 py-0.5 bg-tertiary-container text-on-tertiary-container text-[9px] font-mono font-bold rounded">PRIORITY</span>
                    )}
                  </div>
                  <div className="text-[11px] font-mono text-outline mt-0.5 uppercase">{contact.id}</div>
                </div>
              </div>

              <div className="col-span-2 text-center py-2 lg:py-0">
                <div className={cn("text-sm font-mono font-bold", contact.failed ? "text-error" : contact.priority ? "text-primary" : "text-on-surface")}>
                  {contact.score}
                </div>
                <div className="text-[9px] font-mono text-outline uppercase mt-1">Match: {contact.match}</div>
              </div>

              <div className="col-span-2 flex justify-center py-2 lg:py-0">
                <span className={cn(
                  "px-2.5 py-1 font-mono text-[10px] font-bold rounded border",
                  contact.band === 'PASS' ? "bg-primary-container text-primary border-primary/20" :
                  contact.band === 'REVIEW' ? "bg-secondary-container text-secondary border-secondary/20" :
                  "bg-error-container text-error border-error/20"
                )}>
                  {contact.band}
                </span>
              </div>

              <div className="col-span-3 py-2 lg:py-0">
                <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono text-on-surface-variant">
                  {contact.specialisms.map((spec, sIdx) => (
                    <span key={sIdx} className="bg-surface-container px-1.5 py-0.5 rounded">
                      {spec}
                    </span>
                  ))}
                </div>
                <div className="text-[10px] font-mono text-outline mt-1 italic">{contact.time}</div>
              </div>

              <div className="col-span-1 text-right">
                <button className="p-2 hover:bg-surface-container-highest rounded text-outline group-hover:text-primary transition-colors">
                  <ExternalLink className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mt-6">
        {stats.map((stat, i) => (
          <div key={i} className="bg-surface-container-low border border-outline-variant/10 p-4 rounded-xl">
            <div className="text-[10px] font-mono text-outline uppercase tracking-widest mb-1">{stat.label}</div>
            <div className={cn("text-2xl font-mono font-bold", stat.tertiary ? "text-tertiary" : "text-on-surface")}>
              {stat.value}
            </div>
            <div className={cn("flex items-center gap-1 text-[10px] mt-2", stat.trend === 'up' ? "text-primary" : "text-outline")}>
              {stat.sub}
            </div>
          </div>
        ))}
        <div className="bg-surface-container-low border border-outline-variant/10 p-4 rounded-xl flex flex-col justify-center">
          <button className="w-full h-full border border-dashed border-outline-variant/30 rounded-lg flex items-center justify-center gap-2 text-outline hover:border-primary hover:text-primary transition-all group p-2">
            <span className="text-xl group-hover:rotate-90 transition-transform tracking-tight leading-none">+</span>
            <span className="text-[10px] font-mono uppercase font-bold">Export_Feed_Data</span>
          </button>
        </div>
      </div>
    </div>
  );
}
