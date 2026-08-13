"use client";

import { useEffect, useState } from "react";
import { FileText, Download, Search, Filter, ShieldAlert, CheckCircle2, Clock, RefreshCw } from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, Button, ErrorCard, LoadingCard, Toast } from "../../components/ui";
import { api } from "../../lib/api";

export default function AuditPage() {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [severityFilter, setSeverityFilter] = useState("ALL");

  const loadData = async () => {
    try {
      setLoading(true);
      const params = {};
      if (searchQuery) params.query = searchQuery;
      if (severityFilter !== "ALL") params.severity = severityFilter;

      const [logsData, statsData] = await Promise.all([
        api.searchAuditLogs(params),
        api.getAuditStats(),
      ]);

      setLogs(logsData || []);
      setStats(statsData || null);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [severityFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadData();
  };

  const handleExport = (format) => {
    window.open(`${api.API_BASE_URL || "http://localhost:8000/api/v1"}/audit/export?format=${format}`, "_blank");
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <PageTitle
          title="Enterprise Audit Logs & Compliance"
          subtitle="Immutable, tamper-resistant audit trail recording all platform actions for SOC 2, ISO 27001, and GDPR compliance."
          action={
            <div className="flex gap-2">
              <Button variant="zinc" onClick={() => handleExport("csv")}>
                <Download className="h-4 w-4" /> Export CSV
              </Button>
              <Button variant="zinc" onClick={() => handleExport("json")}>
                <FileText className="h-4 w-4" /> Export JSON
              </Button>
            </div>
          }
        />

        {/* Audit Telemetry Summary Cards */}
        {stats && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="surface rounded-2xl border border-white/10 p-5 bg-[#111827] shadow-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Total Audit Events</span>
                <Clock className="h-4 w-4 text-indigo-400" />
              </div>
              <p className="text-2xl font-extrabold text-white mt-2">{stats.total_audit_events || 0}</p>
            </div>

            <div className="surface rounded-2xl border border-white/10 p-5 bg-[#111827] shadow-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Critical Security Events</span>
                <ShieldAlert className="h-4 w-4 text-rose-400" />
              </div>
              <p className="text-2xl font-extrabold text-rose-400 mt-2">{stats.severity_counts?.CRITICAL || 0}</p>
            </div>

            <div className="surface rounded-2xl border border-white/10 p-5 bg-[#111827] shadow-xl">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Active User Actors</span>
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              </div>
              <p className="text-2xl font-extrabold text-emerald-300 mt-2">
                {Object.keys(stats.top_users || {}).length}
              </p>
            </div>
          </div>
        )}

        {/* Search & Filter Bar */}
        <form onSubmit={handleSearchSubmit} className="surface rounded-2xl border border-white/10 p-4 bg-[#111827] shadow-xl flex flex-wrap gap-3 items-center">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search action, resource, or user..."
              className="w-full rounded-xl border border-white/10 bg-black/40 py-2 pl-9 pr-4 text-xs text-white outline-none focus:border-indigo-500"
            />
          </div>

          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
          >
            <option value="ALL">All Severities</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>

          <Button type="submit" variant="zinc">
            Filter
          </Button>
        </form>

        {loading ? (
          <LoadingCard title="Loading Audit Trail..." />
        ) : error ? (
          <ErrorCard title="Audit Load Error" message={error} onRetry={loadData} />
        ) : (
          <div className="surface rounded-2xl border border-white/10 bg-[#111827] shadow-xl overflow-hidden">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="border-b border-white/10 bg-white/[0.02] uppercase text-[10px] text-slate-400 font-bold">
                <tr>
                  <th className="p-4">Timestamp</th>
                  <th className="p-4">User</th>
                  <th className="p-4">Action</th>
                  <th className="p-4">Resource</th>
                  <th className="p-4">Severity</th>
                  <th className="p-4">IP Address</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10 font-mono text-[11px]">
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-slate-500">
                      No matching audit log entries found.
                    </td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr key={log.id} className="hover:bg-white/[0.02] transition">
                      <td className="p-4 text-slate-400">
                        {new Date(log.timestamp * 1000).toLocaleString()}
                      </td>
                      <td className="p-4 font-semibold text-white">{log.user_name}</td>
                      <td className="p-4 font-bold text-indigo-300">{log.action}</td>
                      <td className="p-4 text-slate-300 truncate max-w-[200px]">{log.resource}</td>
                      <td className="p-4">
                        <Badge variant={log.severity === "CRITICAL" ? "rose" : log.severity === "WARNING" ? "amber" : "emerald"}>
                          {log.severity}
                        </Badge>
                      </td>
                      <td className="p-4 text-slate-400">{log.ip_address}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppShell>
  );
}
