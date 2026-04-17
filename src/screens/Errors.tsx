import { AlertCircle, RefreshCw, Trash2, WifiOff, Key, Hourglass } from 'lucide-react';
import { cn } from '@/src/lib/utils';

export function Errors() {
  const alerts = [
    { icon: WifiOff, label: 'Network Critical', text: 'Inbox connection lost 4m ago' },
    { icon: Key, label: 'Auth Failure', text: 'Anthropic API key expired' },
    { icon: Hourglass, label: 'Process Timeout', text: 'Batch job #12 stalled' },
  ];

  const failures = [
    { file: 'cv-8821.pdf', stage: 'Extraction', code: 'parse_failed', time: '2m ago', retries: 1, expanded: true },
    { file: 'eng_lead_v4.docx', stage: 'Vector_Embed', code: 'rate_limit_exceeded', time: '14m ago', retries: 3 },
    { file: 'candidate_0092.pdf', stage: 'Validation', code: 'schema_mismatch', time: '22m ago', retries: 0 },
    { file: 'admin_staff_july.zip', stage: 'Ingestion', code: 'unsupported_archive', time: '1h ago', retries: 1 },
    { file: 'cv_john_doe.pdf', stage: 'AI_Analysis', code: 'timeout_504', time: '2h ago', retries: 5 },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h1 className="text-xl font-bold tracking-tight text-on-surface flex items-center gap-3">
          <AlertCircle className="text-error w-6 h-6 fill-error/20" />
          SYSTEM_ERRORS_OVERRIDE
        </h1>
        <div className="flex gap-2">
          <button className="bg-surface-container-high hover:bg-surface-container-highest text-on-surface text-[10px] font-mono px-3 py-1.5 rounded uppercase tracking-wider transition-all border border-outline-variant/30 flex items-center gap-2">
            <RefreshCw className="w-3 h-3" /> [RETRY_ALL_FAILED]
          </button>
          <button className="bg-surface-container-high hover:bg-surface-container-highest text-on-surface text-[10px] font-mono px-3 py-1.5 rounded uppercase tracking-wider transition-all border border-outline-variant/30 flex items-center gap-2">
            <Trash2 className="w-3 h-3" /> [CLEAR_LOGS]
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {alerts.map((alert) => (
          <div key={alert.label} className="bg-error-container/10 border border-error/30 p-4 rounded flex items-start gap-4">
            <div className="mt-1 flex-shrink-0 text-error">
              <alert.icon className="w-5 h-5" />
            </div>
            <div>
              <div className="text-[10px] font-mono uppercase text-error-dim tracking-widest mb-1">{alert.label}</div>
              <div className="text-sm font-semibold text-on-surface">{alert.text}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-surface-container-low rounded border border-outline-variant/10 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead className="bg-surface-container-high">
            <tr>
              <th className="px-4 py-3 text-[10px] font-mono uppercase tracking-widest text-on-surface-variant">CV / FILENAME</th>
              <th className="px-4 py-3 text-[10px] font-mono uppercase tracking-widest text-on-surface-variant">STAGE</th>
              <th className="px-4 py-3 text-[10px] font-mono uppercase tracking-widest text-on-surface-variant">ERROR_CODE</th>
              <th className="px-4 py-3 text-[10px] font-mono uppercase tracking-widest text-on-surface-variant">TIMESTAMP</th>
              <th className="px-4 py-3 text-[10px] font-mono uppercase tracking-widest text-on-surface-variant text-center">RETRIES</th>
              <th className="px-4 py-3 text-[10px] font-mono uppercase tracking-widest text-on-surface-variant text-right">ACTION</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant/5">
            {failures.map((fail, i) => (
              <React.Fragment key={i}>
                <tr className="hover:bg-surface-container-high/50 transition-colors cursor-pointer group">
                  <td className="px-4 py-3 text-sm font-medium text-on-surface font-mono">{fail.file}</td>
                  <td className="px-4 py-3">
                    <span className="text-[10px] font-mono bg-surface-container-highest px-2 py-0.5 rounded text-outline border border-outline-variant/20 whitespace-nowrap">
                      {fail.stage}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs font-mono text-error uppercase">{fail.code}</td>
                  <td className="px-4 py-3 text-xs font-mono text-on-surface-variant whitespace-nowrap">{fail.time}</td>
                  <td className="px-4 py-3 text-xs font-mono text-center text-on-surface-variant">{fail.retries}</td>
                  <td className="px-4 py-3 text-right">
                    <button className="text-xs font-mono text-primary hover:underline whitespace-nowrap">[RETRY]</button>
                  </td>
                </tr>
                {fail.expanded && (
                  <tr className="bg-surface-container-lowest/50">
                    <td className="px-4 py-0" colSpan={6}>
                      <div className="py-4 font-mono text-[11px] leading-relaxed text-on-surface-variant bg-surface-container-lowest my-2 rounded border border-outline-variant/10 px-4 max-w-full overflow-hidden">
                        <div className="flex gap-2">
                          <span className="text-error">[CRIT]</span> Traceback (most recent call last):
                        </div>
                        <div className="pl-4">File "/app/parsers/pdf_core.py", line 442, in extract_text</div>
                        <div className="pl-4 text-error">ValueError: PDF structure corrupted at offset 0x000F42 - failed to locate /Root dictionary.</div>
                        <div className="mt-2 text-outline">Attempting re-sync from S3 storage... Failed. Status: 403 Forbidden.</div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
        <div className="bg-surface-container px-4 py-3 border-t border-outline-variant/10 flex flex-col sm:flex-row justify-between items-center gap-4">
          <div className="text-[10px] font-mono text-outline uppercase tracking-widest whitespace-nowrap">
            Showing 5 failures from last 24 hours
          </div>
          <div className="flex gap-4">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-error" />
              <span className="text-[10px] font-mono text-on-surface-variant uppercase whitespace-nowrap">Critical: 02</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-tertiary" />
              <span className="text-[10px] font-mono text-on-surface-variant uppercase whitespace-nowrap">Warning: 14</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-surface-container p-4 rounded border border-outline-variant/5">
            <h3 className="text-[10px] font-mono text-outline uppercase tracking-widest mb-3">Service Health</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-xs font-medium">AWS_S3_STORAGE</span>
                <span className="text-[10px] font-mono text-primary">ONLINE</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs font-medium">REDIS_QUEUE</span>
                <span className="text-[10px] font-mono text-primary">ONLINE</span>
              </div>
              <div className="flex justify-between items-center text-error">
                <span className="text-xs font-medium">ANTHROPIC_LLM</span>
                <span className="text-[10px] font-mono">DEGRADED</span>
              </div>
            </div>
          </div>

          <div className="relative group rounded overflow-hidden aspect-square flex items-center justify-center bg-surface-container-high border border-outline-variant/10">
            <img 
              className="absolute inset-0 w-full h-full object-cover opacity-20" 
              src="https://picsum.photos/seed/circuits/400/400?blur=4" 
              alt="Circuits"
              referrerPolicy="no-referrer"
            />
            <div className="relative text-center">
              <div className="text-3xl font-mono font-bold text-on-surface">94.2%</div>
              <div className="text-[9px] font-mono text-outline uppercase tracking-[0.2em] mt-1">Success Rate</div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-3 bg-surface-container-low p-4 rounded border border-outline-variant/5">
          <h3 className="text-[10px] font-mono text-outline uppercase tracking-widest mb-4">LIVE_RETRY_QUEUE</h3>
          <div className="space-y-2 font-mono text-[10px] whitespace-pre-wrap">
            <div className="text-on-surface-variant"><span className="text-outline">14:22:01</span> <span className="text-primary">[RETRY_INIT]</span> Job ID #8821 queued for background extraction...</div>
            <div className="text-on-surface-variant"><span className="text-outline">14:21:55</span> <span className="text-tertiary">[WARN]</span> Connection pool nearing capacity (92%). Throttling non-essential tasks.</div>
            <div className="text-on-surface-variant"><span className="text-outline">14:20:12</span> <span className="text-error">[FAIL]</span> cv-8821.pdf parsing failed: corrupted_header. Automatic retry scheduled in 5m.</div>
            <div className="text-on-surface-variant"><span className="text-outline">14:18:44</span> <span className="text-primary">[INFO]</span> Database migration task #42 completed in 1.4s.</div>
            <div className="text-on-surface-variant"><span className="text-outline">14:15:30</span> <span className="text-outline">[IDLE]</span> Worker node #3 assigned to standby status.</div>
          </div>
          <div className="mt-4 pt-4 border-t border-outline-variant/10">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
              <span className="text-[10px] font-mono text-primary uppercase">Listening for events...</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

import React from 'react';
