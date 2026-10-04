import { Shield, ShieldCheck } from 'lucide-react';

export function SecurityPage() {
  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <Shield size={20} className="text-blue-600" />
          <h2 className="text-base font-semibold text-slate-900">Security Dashboard</h2>
        </div>
        <div className="grid grid-cols-3 gap-4">
          {[
            { icon: ShieldCheck, label: 'Prompt Injection', status: 'MONITORING', color: 'text-emerald-600' },
            { icon: ShieldCheck, label: 'Retrieval Poisoning', status: 'MONITORING', color: 'text-emerald-600' },
            { icon: ShieldCheck, label: 'Evidence Integrity', status: 'MONITORING', color: 'text-emerald-600' },
          ].map(({ icon: Icon, label, status, color }) => (
            <div key={label} className="p-4 rounded-lg border border-slate-200">
              <Icon size={18} className={color} />
              <h3 className="text-sm font-medium text-slate-900 mt-2">{label}</h3>
              <span className={`text-xs font-medium ${color}`}>{status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
