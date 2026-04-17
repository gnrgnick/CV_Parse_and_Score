import { useCallback, useEffect, useRef, useState } from 'react';
import { ExternalLink, User, UserMinus, Upload, Loader2, AlertCircle, RefreshCw } from 'lucide-react';
import { cn } from '@/src/lib/utils';
import { API_URL, listRuns, processCV, type RunSummary } from '@/src/lib/api';

const REFRESH_INTERVAL_MS = 30_000;

export function NewContacts() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [lastFetchedAt, setLastFetchedAt] = useState<Date | null>(null);

  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadNote, setUploadNote] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchRuns = useCallback(async () => {
    try {
      const data = await listRuns(50);
      setRuns(data);
      setListError(null);
      setLastFetchedAt(new Date());
    } catch (err) {
      setListError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRuns();
    const id = setInterval(fetchRuns, REFRESH_INTERVAL_MS);
    return () => clearInterval(id);
  }, [fetchRuns]);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setUploadError(null);
    setUploadNote(null);
    try {
      const result = await processCV(file);
      const label = result.status === 'succeeded'
        ? 'Scored'
        : result.status === 'flagged_for_review'
          ? 'Flagged'
          : 'Failed';
      const total = result.score_total != null ? `${result.score_total}/210` : '—';
      setUploadNote(`${label}: ${file.name} → ${total} (${result.location_band})`);
      await fetchRuns();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : String(err));
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-on-surface flex items-center gap-3">
            NEW_CONTACTS
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 bg-primary-container text-on-primary-container rounded text-[10px] font-mono tracking-widest uppercase">
              <span className={cn(
                'w-1.5 h-1.5 rounded-full',
                listError ? 'bg-error' : 'bg-primary animate-pulse',
              )} />
              {listError ? 'Connection error' : lastFetchedAt ? `Updated ${relativeTime(lastFetchedAt)}` : 'Loading…'}
            </span>
          </h1>
          <p className="text-[10px] text-on-surface-variant font-mono uppercase mt-1 tracking-widest leading-none">
            Live feed from {hostFromUrl(API_URL)} · auto-refresh 30s
          </p>
        </div>

        <button
          onClick={() => fetchRuns()}
          disabled={loading}
          className="bg-surface-container-highest px-3 py-1.5 rounded border border-outline-variant text-[11px] font-mono uppercase tracking-wider hover:bg-surface-bright transition-colors flex items-center gap-2 disabled:opacity-50"
        >
          <RefreshCw className={cn('w-3 h-3', loading && 'animate-spin')} />
          Refresh
        </button>
      </div>

      <UploadPanel
        fileInputRef={fileInputRef}
        uploading={uploading}
        uploadError={uploadError}
        uploadNote={uploadNote}
        onFile={handleUpload}
      />

      {listError && (
        <div className="bg-error-container/20 border border-error/30 rounded p-4 flex items-start gap-3">
          <AlertCircle className="w-4 h-4 text-error flex-shrink-0 mt-0.5" />
          <div>
            <div className="text-[11px] font-mono uppercase text-error tracking-widest font-bold">
              Feed unavailable
            </div>
            <div className="text-[11px] font-mono text-on-surface-variant mt-1 break-all">
              {listError}
            </div>
          </div>
        </div>
      )}

      <div className="bg-surface-container-low rounded-xl overflow-hidden border border-outline-variant/10">
        <div className="hidden lg:grid grid-cols-12 px-4 py-3 bg-surface-container text-[10px] font-mono uppercase text-outline tracking-widest border-b border-outline-variant/20">
          <div className="col-span-4">Candidate_Identity</div>
          <div className="col-span-2 text-center">Score_Index</div>
          <div className="col-span-2 text-center">Status_Band</div>
          <div className="col-span-3">Primary_Specialisms</div>
          <div className="col-span-1 text-right">Action</div>
        </div>

        {loading && runs.length === 0 ? (
          <EmptyState message="Loading feed…" icon={<Loader2 className="w-5 h-5 animate-spin" />} />
        ) : runs.length === 0 && !listError ? (
          <EmptyState
            message="No runs yet. Upload a CV above to get started."
            icon={<Upload className="w-5 h-5" />}
          />
        ) : (
          <div className="divide-y divide-outline-variant/10">
            {runs.map((run) => <RunRow key={run.run_id} run={run} />)}
          </div>
        )}
      </div>
    </div>
  );
}

interface UploadPanelProps {
  fileInputRef: React.RefObject<HTMLInputElement>;
  uploading: boolean;
  uploadError: string | null;
  uploadNote: string | null;
  onFile: (file: File) => void | Promise<void>;
}

function UploadPanel({ fileInputRef, uploading, uploadError, uploadNote, onFile }: UploadPanelProps) {
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) onFile(file);
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      className={cn(
        'bg-surface-container-low border rounded-xl p-6 transition-colors',
        dragOver ? 'border-primary' : 'border-outline-variant/10',
      )}
    >
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-widest text-outline mb-1">
            Submit_CV
          </div>
          <div className="text-sm text-on-surface">
            Drop a <span className="font-mono">.pdf</span> or <span className="font-mono">.docx</span> here, or choose a file.
          </div>
          <div className="text-[10px] font-mono text-on-surface-variant mt-1">
            Haiku extracts → Python location filter → Sonnet scores → row lands in the feed.
          </div>
        </div>

        <div className="flex items-center gap-3">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) onFile(file);
            }}
            disabled={uploading}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className={cn(
              'bg-primary text-on-primary px-4 py-2 rounded text-[11px] font-bold uppercase tracking-widest flex items-center gap-2 transition-all',
              uploading ? 'opacity-50 cursor-wait' : 'hover:brightness-110',
            )}
          >
            {uploading ? (
              <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Processing…</>
            ) : (
              <><Upload className="w-3.5 h-3.5" /> Upload_CV</>
            )}
          </button>
        </div>
      </div>

      {uploadError && (
        <div className="mt-4 text-[11px] font-mono text-error flex items-start gap-2">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
          <span className="break-all">{uploadError}</span>
        </div>
      )}
      {uploadNote && !uploadError && (
        <div className="mt-4 text-[11px] font-mono text-primary">{uploadNote}</div>
      )}
    </div>
  );
}

function RunRow({ run }: { run: RunSummary }) {
  const failed = run.status === 'failed';
  const flagged = run.status === 'flagged_for_review';
  const priority = run.score_total != null && run.score_total >= 168; // 80% of 210

  const scoreColor = failed
    ? 'text-error'
    : priority
      ? 'text-primary'
      : 'text-on-surface';

  const bandColor =
    run.location_band === 'PASS' ? 'bg-primary-container text-primary border-primary/20'
    : run.location_band === 'REVIEW' || run.location_band === 'NO_DATA' ? 'bg-secondary-container text-secondary border-secondary/20'
    : 'bg-error-container text-error border-error/20';

  return (
    <div className="grid grid-cols-1 md:grid-cols-12 px-4 py-4 items-center hover:bg-surface-container-high transition-colors group cursor-pointer border-b border-outline-variant/10 lg:border-none">
      <div className="col-span-4 flex items-center gap-3">
        <div className="w-10 h-10 bg-surface-container-highest flex items-center justify-center rounded border border-outline-variant/30 flex-shrink-0">
          {failed ? <UserMinus className="w-5 h-5 text-outline" /> : <User className="w-5 h-5 text-outline" />}
        </div>
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-bold text-on-surface">
              {run.candidate_name ?? <span className="italic text-outline">name_unknown</span>}
            </span>
            {priority && (
              <span className="px-1.5 py-0.5 bg-tertiary-container text-on-tertiary-container text-[9px] font-mono font-bold rounded">
                PRIORITY
              </span>
            )}
            {flagged && (
              <span className="px-1.5 py-0.5 bg-secondary-container text-secondary text-[9px] font-mono font-bold rounded">
                REVIEW
              </span>
            )}
            {run.is_reapplication && (
              <span className="px-1.5 py-0.5 bg-surface-container-highest text-on-surface-variant text-[9px] font-mono rounded">
                REAPPLICATION
              </span>
            )}
          </div>
          <div className="text-[11px] font-mono text-outline mt-0.5 uppercase">
            RUN_{String(run.run_id).padStart(6, '0')}
          </div>
        </div>
      </div>

      <div className="col-span-2 text-center py-2 lg:py-0">
        <div className={cn('text-sm font-mono font-bold', scoreColor)}>
          {run.score_total != null ? `${run.score_total}/210` : '—'}
        </div>
        <div className="text-[9px] font-mono text-outline uppercase mt-1">
          Match: {matchPercentage(run.score_total)}
        </div>
      </div>

      <div className="col-span-2 flex justify-center py-2 lg:py-0">
        {run.location_band && (
          <span className={cn(
            'px-2.5 py-1 font-mono text-[10px] font-bold rounded border',
            bandColor,
          )}>
            {run.location_band}
          </span>
        )}
      </div>

      <div className="col-span-3 py-2 lg:py-0">
        <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono text-on-surface-variant">
          {run.top_categories.map((cat) => (
            <span key={cat.label} className="bg-surface-container px-1.5 py-0.5 rounded">
              {cat.label} {cat.score}/{cat.max}
            </span>
          ))}
        </div>
        <div className="text-[10px] font-mono text-outline mt-1 italic">
          {relativeTime(new Date(run.started_at))}
        </div>
      </div>

      <div className="col-span-1 text-right">
        <button
          className="p-2 hover:bg-surface-container-highest rounded text-outline group-hover:text-primary transition-colors"
          title="Open details (coming soon)"
        >
          <ExternalLink className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

function EmptyState({ message, icon }: { message: string; icon: React.ReactNode }) {
  return (
    <div className="py-16 flex flex-col items-center justify-center text-outline gap-3">
      {icon}
      <div className="text-[11px] font-mono uppercase tracking-widest">{message}</div>
    </div>
  );
}

function matchPercentage(score: number | null): string {
  if (score == null) return 'n/a';
  return `${((score / 210) * 100).toFixed(1)}%`;
}

function hostFromUrl(url: string): string {
  try {
    return new URL(url).host;
  } catch {
    return url;
  }
}

function relativeTime(date: Date): string {
  const seconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}
