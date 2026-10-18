"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import {
  Boxes,
  Boxes as BoxesIcon,
  Download,
  Plus,
  RefreshCw,
  Search,
  Server,
  Activity,
  Layers,
  HeartPulse,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/StatCard";
import { Dialog, DialogContent } from "@/components/ui/Dialog";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { EmptyState } from "@/components/ui/EmptyState";
import { Sidebar, TabId } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { CommandPalette } from "@/components/layout/CommandPalette";
import { MasterControl } from "@/components/dashboard/MasterControl";
import { ProjectCard } from "@/components/dashboard/ProjectCard";
import { EventsTimeline } from "@/components/dashboard/EventsTimeline";
import { LogViewer } from "@/components/dashboard/LogViewer";

import {
  createApplication,
  deleteApplication,
  getEvents,
  getOverview,
  getSettings,
  listApplications,
  getComponentLogs,
  startComponent,
  stopComponent,
  restartComponent,
  startApplication,
  stopApplication,
  startAll,
  stopAll,
  startFavorites,
  loadSamples,
  deleteSamples,
  openFolder,
  openEditor,
  markAllEventsRead,
  exportData,
  clearComponentLogs,
} from "@/lib/api";
import type { Application, EventItem, OverviewData, Settings as HangarSettings } from "@/lib/types";
import { wsClient } from "@/lib/ws";

export function HangarDashboard() {
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [applications, setApplications] = useState<Application[]>([]);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [settings, setSettings] = useState<HangarSettings | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [selectedComponent, setSelectedComponent] = useState<string>("");
  const [theme, setTheme] = useState<"light" | "dark" | "system">("system");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [addOpen, setAddOpen] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  // Remove Project modal state
  const [removeTarget, setRemoveTarget] = useState<Application | null>(null);
  const [removeOpen, setRemoveOpen] = useState(false);
  const [stopFirst, setStopFirst] = useState(true);
  const [removeLoading, setRemoveLoading] = useState(false);

  // Search in Applications tab
  const [appSearch, setAppSearch] = useState("");

  const [addForm, setAddForm] = useState({
    name: "",
    description: "",
    path: "",
    tags: "",
    componentName: "",
    kind: "backend" as "backend" | "frontend" | "database" | "worker",
    cwd: "",
    startCmd: "",
    stopCmd: "",
    port: "",
    url: "",
    tier: "2",
    startOnLaunch: false,
    autorestart: true,
    healthType: "tcp" as "tcp" | "http" | "process" | "command" | "file",
  });

  const loadDashboard = useCallback(async () => {
    try {
      setError(null);
      const [overviewData, appsData, eventsData, settingsData] = await Promise.all([
        getOverview().catch(() => null),
        listApplications().catch(() => []),
        getEvents({ limit: 16 }).catch(() => []),
        getSettings().catch(() => null),
      ]);

      setOverview(overviewData);
      setApplications(appsData);
      setEvents(eventsData);
      setSettings(settingsData);

      if (!selectedComponent && appsData.length > 0) {
        const firstComponent = appsData.flatMap((app) => app.components).at(0)?.id ?? "";
        setSelectedComponent(firstComponent);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch dashboard data.");
    } finally {
      setLoading(false);
    }
  }, [selectedComponent]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  // WebSocket Live Updates
  useEffect(() => {
    wsClient.connect();
    const unsubConn = wsClient.onConnectionChange((st) => setWsConnected(st === "connected"));

    // Subscribe to status updates
    const unsubStatus = wsClient.subscribe("status", (data: any) => {
      if (data.component_id && data.component_status) {
        setApplications((prev) =>
          prev.map((app) => {
            const hasComp = app.components.some((c) => c.id === data.component_id);
            if (!hasComp) return app;
            return {
              ...app,
              status: data.application_status || app.status,
              components: app.components.map((c) =>
                c.id === data.component_id
                  ? { ...c, status: data.component_status, status_reason: data.component_status_reason }
                  : c
              ),
            };
          })
        );
      }
    });

    // Subscribe to events
    const unsubEvents = wsClient.subscribe("events", (newEvent: any) => {
      if (!newEvent || !newEvent.id) return;
      setEvents((prev) => [newEvent, ...(prev || []).filter((e) => e && e.id !== newEvent.id).slice(0, 30)]);
    });

    return () => {
      unsubConn();
      unsubStatus();
      unsubEvents();
    };
  }, []);

  // Live log subscription
  useEffect(() => {
    if (!selectedComponent) {
      setLogs([]);
      return;
    }

    const loadLogs = async () => {
      try {
        const res = await getComponentLogs(selectedComponent, { lines: 100 });
        setLogs(res.lines ?? []);
      } catch {
        setLogs([]);
      }
    };
    loadLogs();

    // Subscribe to live log stream for selected component
    const unsubLogs = wsClient.subscribe(`logs:${selectedComponent}`, (msg: any) => {
      if (msg.type === "log_batch" && Array.isArray(msg.lines)) {
        const newLines = msg.lines.map((l: any) => l.line);
        setLogs((prev) => [...prev.slice(-300), ...newLines]);
      }
    });

    return () => {
      unsubLogs();
    };
  }, [selectedComponent]);

  // Theme Sync
  useEffect(() => {
    const root = document.documentElement;
    if (theme === "system") {
      const isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      root.classList.toggle("dark", isDark);
      return;
    }
    root.classList.toggle("dark", theme === "dark");
  }, [theme]);

  const componentOptions = useMemo(
    () => applications.flatMap((app) => app.components.map((component) => ({ ...component, appName: app.name }))),
    [applications]
  );

  const filteredApplications = useMemo(() => {
    if (!appSearch.trim()) return applications;
    const q = appSearch.trim().toLowerCase();
    return applications.filter(
      (a) =>
        a.name.toLowerCase().includes(q) ||
        a.path.toLowerCase().includes(q) ||
        a.components.some((c) => c.name.toLowerCase().includes(q)) ||
        a.tags.some((t) => t.toLowerCase().includes(q))
    );
  }, [applications, appSearch]);

  const showFeedback = (msg: string) => {
    setActionMessage(msg);
    setTimeout(() => setActionMessage(null), 3500);
  };

  // Actions
  const handleToggleComponent = async (componentId: string, shouldStart: boolean) => {
    try {
      if (shouldStart) {
        showFeedback("Starting component...");
        await startComponent(componentId);
      } else {
        showFeedback("Stopping component...");
        await stopComponent(componentId);
      }
      setTimeout(loadDashboard, 600);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to toggle component.");
    }
  };

  const handleRestartComponent = async (componentId: string) => {
    try {
      showFeedback("Restarting component...");
      await restartComponent(componentId);
      setTimeout(loadDashboard, 800);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to restart component.");
    }
  };

  const handleStartApp = async (appId: string) => {
    try {
      showFeedback("Starting all application components in safe order...");
      await startApplication(appId);
      setTimeout(loadDashboard, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start application.");
    }
  };

  const handleStopApp = async (appId: string) => {
    try {
      showFeedback("Stopping all application components in reverse order...");
      await stopApplication(appId);
      setTimeout(loadDashboard, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to stop application.");
    }
  };

  const handleStartAll = async () => {
    try {
      showFeedback("Starting all applications...");
      await startAll();
      setTimeout(loadDashboard, 1200);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start all.");
    }
  };

  const handleStopAll = async () => {
    try {
      showFeedback("Stopping all applications...");
      await stopAll();
      setTimeout(loadDashboard, 1200);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to stop all.");
    }
  };

  const handleStartFavorites = async () => {
    try {
      showFeedback("Starting favorite applications...");
      await startFavorites();
      setTimeout(loadDashboard, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start favorites.");
    }
  };

  const handleLoadSamples = async () => {
    try {
      showFeedback("Loading Sample Shop and Sample Blog apps...");
      await loadSamples();
      await loadDashboard();
      showFeedback("Sample applications loaded!");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sample apps.");
    }
  };

  const handleDeleteSamples = async () => {
    try {
      showFeedback("Removing sample applications...");
      await deleteSamples();
      await loadDashboard();
      showFeedback("Sample applications removed.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete samples.");
    }
  };

  const handleOpenFolder = async (appId: string) => {
    try {
      await openFolder(appId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to open folder.");
    }
  };

  const handleOpenEditor = async (appId: string) => {
    try {
      await openEditor(appId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to open in editor.");
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllEventsRead();
      setEvents((prev) => prev.map((e) => ({ ...e, read: true })));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to mark events read.");
    }
  };

  const handleClearLogs = async () => {
    if (!selectedComponent) return;
    try {
      await clearComponentLogs(selectedComponent);
      setLogs([]);
      showFeedback("Logs cleared.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to clear logs.");
    }
  };

  const handleRemoveApplication = async () => {
    if (!removeTarget) return;
    setRemoveLoading(true);
    try {
      await deleteApplication(removeTarget.id, stopFirst);
      setRemoveOpen(false);
      setRemoveTarget(null);
      await loadDashboard();
      showFeedback(`"${removeTarget.name}" removed from Hangar.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove application.");
    } finally {
      setRemoveLoading(false);
    }
  };

  const handleCreateApplication = async () => {
    if (!addForm.name.trim() || !addForm.path.trim() || !addForm.componentName.trim() || !addForm.startCmd.trim()) {
      setError("Name, project path, component name, and start command are required.");
      return;
    }

    const portNum = addForm.port.trim() ? Number(addForm.port.trim()) : null;
    const urlStr = addForm.url.trim() || (portNum ? `http://localhost:${portNum}` : null);

    const componentPayload = {
      name: addForm.componentName.trim(),
      kind: addForm.kind,
      cwd: addForm.cwd.trim() || addForm.path.trim(),
      start_cmd: addForm.startCmd.trim(),
      stop_cmd: addForm.stopCmd.trim() || null,
      env: {},
      port: portNum,
      url: urlStr,
      health: {
        type: addForm.healthType,
        target: portNum ? String(portNum) : null,
        interval_s: 5,
        timeout_s: 3,
        startup_grace_s: 30,
      },
      tier: Number(addForm.tier),
      autorestart: addForm.autorestart,
      max_restarts: 5,
      start_on_launch: addForm.startOnLaunch,
    };

    try {
      setError(null);
      await createApplication({
        name: addForm.name.trim(),
        description: addForm.description.trim(),
        icon: "Boxes",
        path: addForm.path.trim(),
        tags: addForm.tags
          .split(",")
          .map((tag) => tag.trim())
          .filter(Boolean),
        favorite: false,
        sort: 0,
        start_mode: "ordered",
        components: [componentPayload],
      });

      setAddOpen(false);
      setAddForm({
        name: "",
        description: "",
        path: "",
        tags: "",
        componentName: "",
        kind: "backend",
        cwd: "",
        startCmd: "",
        stopCmd: "",
        port: "",
        url: "",
        tier: "2",
        startOnLaunch: false,
        autorestart: true,
        healthType: "tcp",
      });
      await loadDashboard();
      showFeedback("Application created successfully!");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create application.");
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)] transition-colors">
      <div className="mx-auto flex max-w-[1600px] gap-4 p-4 md:p-6">
        {/* Left Sidebar Rail */}
        <Sidebar
          activeTab={activeTab}
          onTabChange={setActiveTab}
          wsConnected={wsConnected}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        />

        {/* Main Workspace Area */}
        <div className="min-w-0 flex-1 flex flex-col gap-5">
          {/* Top Bar Header */}
          <Header
            activeTab={activeTab}
            onRefresh={loadDashboard}
            onLoadSamples={handleLoadSamples}
            onAddOpen={() => setAddOpen(true)}
            onOpenSearch={() => setCommandPaletteOpen(true)}
            theme={theme}
            onThemeChange={setTheme}
          />

          {/* Feedback & Error Banners */}
          {error && (
            <div className="flex items-center justify-between rounded-xl border border-[var(--status-stopped)]/40 bg-[var(--status-stopped)]/10 px-4 py-3 text-xs text-[var(--status-stopped)]">
              <span>{error}</span>
              <button type="button" onClick={() => setError(null)} className="font-bold underline ml-2">
                Dismiss
              </button>
            </div>
          )}

          {actionMessage && (
            <div className="rounded-xl border border-[var(--accent)]/40 bg-[var(--accent)]/10 px-4 py-2.5 text-xs text-[var(--accent)] font-medium">
              {actionMessage}
            </div>
          )}

          {/* Mobile Navigation Tabs (visible only on mobile) */}
          <div className="flex md:hidden overflow-x-auto gap-1 p-1 rounded-xl border border-[var(--border)] bg-[var(--surface)]">
            {(["overview", "applications", "logs", "activity", "settings"] as const).map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg capitalize whitespace-nowrap transition-colors ${
                  activeTab === tab
                    ? "bg-[var(--surface-2)] text-[var(--accent)] shadow-sm"
                    : "text-[var(--text-muted)]"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* TAB 1: OVERVIEW */}
          {activeTab === "overview" && (
            <section className="space-y-5 animate-in fade-in duration-150">
              {/* Master Control Hero Panel */}
              <MasterControl
                overview={overview}
                onStartFavorites={handleStartFavorites}
                onStartAll={handleStartAll}
                onStopAll={handleStopAll}
              />

              {/* 4 Flight-Control Stat Cards */}
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <StatCard
                  label="Registered Projects"
                  value={overview?.total_applications ?? applications.length}
                  hint="Local project directories tracked"
                  icon={<BoxesIcon className="h-5 w-5" />}
                />
                <StatCard
                  label="Total Components"
                  value={overview?.total_components ?? 0}
                  hint="Frontends, backends, and databases"
                  icon={<Layers className="h-5 w-5" />}
                />
                <StatCard
                  label="Active Services"
                  value={overview?.running_components ?? 0}
                  hint="Healthy running processes"
                  accent
                  icon={<Server className="h-5 w-5" />}
                />
                <StatCard
                  label="System Health"
                  value={
                    overview?.total_components && overview.total_components > 0
                      ? `${Math.round(((overview.running_components ?? 0) / overview.total_components) * 100)}%`
                      : "100%"
                  }
                  hint="TCP/HTTP probe success rate"
                  icon={<HeartPulse className="h-5 w-5" />}
                />
              </div>

              {/* Project Rack Units */}
              <div>
                <div className="flex items-center justify-between mb-3 px-1">
                  <div>
                    <h2 className="text-lg font-bold text-[var(--text)] font-display">
                      Project Rack Bays
                    </h2>
                    <p className="text-xs text-[var(--text-muted)]">
                      Tiered process units ready for supervision
                    </p>
                  </div>
                  <Button
                    variant="secondary"
                    size="sm"
                    icon={<Plus className="h-3.5 w-3.5" />}
                    onClick={() => setAddOpen(true)}
                  >
                    Add bay
                  </Button>
                </div>

                <div className="space-y-4">
                  {applications.map((app) => (
                    <ProjectCard
                      key={app.id}
                      app={app}
                      onToggleComponent={handleToggleComponent}
                      onRestartComponent={handleRestartComponent}
                      onStartApp={handleStartApp}
                      onStopApp={handleStopApp}
                      onOpenFolder={handleOpenFolder}
                      onOpenEditor={handleOpenEditor}
                      onRemoveProject={(targetApp) => {
                        setRemoveTarget(targetApp);
                        setRemoveOpen(true);
                      }}
                    />
                  ))}

                  {applications.length === 0 && (
                    <EmptyState
                      title="No projects registered yet"
                      description="Connect your local Next.js, FastAPI, Node, or Docker projects to start supervising processes from one machine room screen."
                      actions={[
                        {
                          label: "Load built-in samples",
                          icon: <BoxesIcon className="h-4 w-4" />,
                          onClick: handleLoadSamples,
                          variant: "primary",
                        },
                        {
                          label: "Add project",
                          icon: <Plus className="h-4 w-4" />,
                          onClick: () => setAddOpen(true),
                          variant: "secondary",
                        },
                      ]}
                    />
                  )}
                </div>
              </div>

              {/* Events Stream */}
              <EventsTimeline events={events} onMarkAllRead={handleMarkAllRead} />
            </section>
          )}

          {/* TAB 2: APPLICATIONS */}
          {activeTab === "applications" && (
            <section className="space-y-5 animate-in fade-in duration-150">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="relative flex-1 max-w-md">
                  <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[var(--text-muted)]" />
                  <input
                    value={appSearch}
                    onChange={(e) => setAppSearch(e.target.value)}
                    placeholder="Filter applications by name, tag, or path..."
                    className="w-full rounded-xl border border-[var(--border)] bg-[var(--surface)] pl-9 pr-4 py-2 text-xs text-[var(--text)] outline-none focus:border-[var(--accent)] transition-colors"
                  />
                </div>

                <Button
                  variant="primary"
                  size="sm"
                  icon={<Plus className="h-4 w-4" />}
                  onClick={() => setAddOpen(true)}
                >
                  Add application
                </Button>
              </div>

              <div className="space-y-4">
                {filteredApplications.map((app) => (
                  <ProjectCard
                    key={app.id}
                    app={app}
                    onToggleComponent={handleToggleComponent}
                    onRestartComponent={handleRestartComponent}
                    onStartApp={handleStartApp}
                    onStopApp={handleStopApp}
                    onOpenFolder={handleOpenFolder}
                    onOpenEditor={handleOpenEditor}
                    onRemoveProject={(targetApp) => {
                      setRemoveTarget(targetApp);
                      setRemoveOpen(true);
                    }}
                  />
                ))}

                {filteredApplications.length === 0 && (
                  <EmptyState
                    title="No matching applications found"
                    description={
                      appSearch
                        ? `No projects match "${appSearch}". Try clearing your search.`
                        : "Click 'Add application' to register your local code, or load our Python samples."
                    }
                    actions={
                      appSearch
                        ? [
                            {
                              label: "Clear search",
                              onClick: () => setAppSearch(""),
                              variant: "secondary",
                            },
                          ]
                        : [
                            {
                              label: "Load sample apps",
                              icon: <BoxesIcon className="h-4 w-4" />,
                              onClick: handleLoadSamples,
                              variant: "primary",
                            },
                          ]
                    }
                  />
                )}
              </div>
            </section>
          )}

          {/* TAB 3: LOGS */}
          {activeTab === "logs" && (
            <section className="animate-in fade-in duration-150">
              <LogViewer
                logs={logs}
                selectedComponent={selectedComponent}
                componentOptions={componentOptions}
                onSelectComponent={setSelectedComponent}
                onClearLogs={handleClearLogs}
              />
            </section>
          )}


          {/* TAB 5: ACTIVITY */}
          {activeTab === "activity" && (
            <section className="animate-in fade-in duration-150">
              <EventsTimeline events={events} onMarkAllRead={handleMarkAllRead} maxDisplay={50} />
            </section>
          )}

          {/* TAB 6: SETTINGS */}
          {activeTab === "settings" && (
            <section className="space-y-5 animate-in fade-in duration-150">
              {/* Appearance */}
              <Card className="p-5 border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-sm)]">
                <h2 className="text-lg font-bold text-[var(--text)] font-display">Appearance</h2>
                <p className="text-xs text-[var(--text-muted)] mb-4">
                  Theme is persisted locally and applied before first paint
                </p>
                <div className="flex flex-wrap gap-3">
                  {(["light", "dark", "system"] as const).map((t) => (
                    <Button
                      key={t}
                      variant={theme === t ? "primary" : "secondary"}
                      size="sm"
                      onClick={() => setTheme(t)}
                    >
                      <span className="capitalize">{t} Theme</span>
                    </Button>
                  ))}
                </div>
              </Card>

              {/* Sample Applications */}
              <Card className="p-5 border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-sm)]">
                <h2 className="text-lg font-bold text-[var(--text)] font-display">Sample Applications</h2>
                <p className="text-xs text-[var(--text-muted)] mb-4 leading-relaxed">
                  Hangar ships with self-contained Python standard library demo projects (Sample Shop and Sample Blog) to test supervision, health checks, and crashes.
                </p>
                <div className="flex gap-2">
                  <Button variant="primary" size="sm" icon={<Boxes className="h-4 w-4" />} onClick={handleLoadSamples}>
                    Load sample apps
                  </Button>
                  <Button variant="danger" size="sm" onClick={handleDeleteSamples}>
                    Delete sample apps
                  </Button>
                </div>
              </Card>

              {/* System Configuration */}
              <Card className="p-5 border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-sm)]">
                <h2 className="text-lg font-bold text-[var(--text)] font-display">System Configuration</h2>
                <div className="mt-3 text-xs text-[var(--text-muted)] space-y-2 font-mono">
                  <div><strong className="text-[var(--text)]">Shell:</strong> {settings?.shell_override || "cmd.exe"}</div>
                  <div><strong className="text-[var(--text)]">Data folder:</strong> {settings?.hangar_home || "~/.hangar"}</div>
                  <div><strong className="text-[var(--text)]">Health interval:</strong> {settings?.health_interval_s || 5}s</div>
                  <div><strong className="text-[var(--text)]">Startup grace:</strong> {settings?.startup_grace_s || 30}s</div>
                  <div><strong className="text-[var(--text)]">Version:</strong> {settings?.version || "0.1.0"}</div>
                </div>

                <div className="pt-4 mt-4 border-t border-[var(--border)]">
                  <Button
                    variant="secondary"
                    size="sm"
                    icon={<Download className="h-4 w-4" />}
                    onClick={async () => {
                      const data = await exportData();
                      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = "hangar-config-export.json";
                      a.click();
                      URL.revokeObjectURL(url);
                    }}
                  >
                    Export configuration JSON
                  </Button>
                </div>
              </Card>
            </section>
          )}

          {/* Add Application Dialog */}
          <Dialog open={addOpen} onOpenChange={setAddOpen}>
            <DialogContent title="Add application" description="Register a local project and its primary component.">
              <div className="space-y-4 max-h-[75vh] overflow-y-auto pr-1">
                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="space-y-1 text-sm">
                    <span className="text-[var(--text-muted)]">Application name *</span>
                    <input
                      value={addForm.name}
                      onChange={(e) => setAddForm((c) => ({ ...c, name: e.target.value }))}
                      className="w-full rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2 text-[var(--text)] outline-none focus:border-[var(--accent)]"
                      placeholder="e.g. Dummy Project"
                    />
                  </label>
                  <label className="space-y-1 text-sm">
                    <span className="text-[var(--text-muted)]">Project folder path *</span>
                    <input
                      value={addForm.path}
                      onChange={(e) => setAddForm((c) => ({ ...c, path: e.target.value }))}
                      className="w-full rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2 text-[var(--text)] outline-none focus:border-[var(--accent)]"
                      placeholder="e.g. C:\Users\...\projects\dummy"
                    />
                  </label>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="space-y-1 text-sm">
                    <span className="text-[var(--text-muted)]">Description</span>
                    <input
                      value={addForm.description}
                      onChange={(e) => setAddForm((c) => ({ ...c, description: e.target.value }))}
                      className="w-full rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2 text-[var(--text)] outline-none focus:border-[var(--accent)]"
                      placeholder="Brief note about this app"
                    />
                  </label>
                  <label className="space-y-1 text-sm">
                    <span className="text-[var(--text-muted)]">Tags (comma separated)</span>
                    <input
                      value={addForm.tags}
                      onChange={(e) => setAddForm((c) => ({ ...c, tags: e.target.value }))}
                      className="w-full rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2 text-[var(--text)] outline-none focus:border-[var(--accent)]"
                      placeholder="e.g. web, api, test"
                    />
                  </label>
                </div>

                <div className="pt-2 border-t border-[var(--border)]">
                  <h4 className="text-sm font-bold mb-3 text-[var(--accent)]">Primary Component</h4>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <label className="space-y-1 text-sm sm:col-span-2">
                      <span className="text-[var(--text-muted)]">Component name *</span>
                      <input
                        value={addForm.componentName}
                        onChange={(e) => setAddForm((c) => ({ ...c, componentName: e.target.value }))}
                        className="w-full rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2 text-[var(--text)] outline-none focus:border-[var(--accent)]"
                        placeholder="e.g. dummy-server"
                      />
                    </label>
                    <label className="space-y-1 text-sm">
                      <span className="text-[var(--text-muted)]">Kind</span>
                      <select
                        value={addForm.kind}
                        onChange={(e) => setAddForm((c) => ({ ...c, kind: e.target.value as any }))}
                        className="w-full rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2 text-[var(--text)] outline-none focus:border-[var(--accent)]"
                      >
                        <option value="backend">Backend</option>
                        <option value="frontend">Frontend</option>
                        <option value="database">Database</option>
                        <option value="worker">Worker</option>
                      </select>
                    </label>
                  </div>

                  <div className="mt-3 space-y-1 text-sm">
                    <span className="text-[var(--text-muted)]">Start command *</span>
                    <input
                      value={addForm.startCmd}
                      onChange={(e) => setAddForm((c) => ({ ...c, startCmd: e.target.value }))}
                      className="w-full rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2 text-[var(--text)] font-mono outline-none focus:border-[var(--accent)]"
                      placeholder="e.g. python -m http.server 5050"
                    />
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2 mt-3">
                    <label className="space-y-1 text-sm">
                      <span className="text-[var(--text-muted)]">Listening Port (optional)</span>
                      <input
                        type="number"
                        value={addForm.port}
                        onChange={(e) => setAddForm((c) => ({ ...c, port: e.target.value }))}
                        className="w-full rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2 text-[var(--text)] outline-none focus:border-[var(--accent)]"
                        placeholder="e.g. 5050"
                      />
                    </label>
                    <label className="space-y-1 text-sm">
                      <span className="text-[var(--text-muted)]">Health check type</span>
                      <select
                        value={addForm.healthType}
                        onChange={(e) => setAddForm((c) => ({ ...c, healthType: e.target.value as any }))}
                        className="w-full rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2 text-[var(--text)] outline-none focus:border-[var(--accent)]"
                      >
                        <option value="tcp">TCP port check</option>
                        <option value="http">HTTP GET 200</option>
                        <option value="process">Process alive</option>
                      </select>
                    </label>
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-4 border-t border-[var(--border)]">
                  <Button variant="secondary" size="sm" onClick={() => setAddOpen(false)}>
                    Cancel
                  </Button>
                  <Button variant="primary" size="sm" onClick={handleCreateApplication}>
                    Save and register
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>

          {/* Remove Project Confirmation Modal (ConfirmDialog) */}
          <ConfirmDialog
            open={removeOpen}
            title="Remove project"
            danger
            loading={removeLoading}
            confirmLabel="Remove project"
            onCancel={() => {
              setRemoveOpen(false);
              setRemoveTarget(null);
            }}
            onConfirm={handleRemoveApplication}
            body={
              <div className="space-y-3">
                <p>
                  Remove <strong>&ldquo;{removeTarget?.name}&rdquo;</strong> from Hangar? This deletes
                  the dashboard registration and its past log files.
                </p>
                <p className="font-semibold text-xs text-[var(--text-muted)]">
                  Your project folder, source code, and local data are NEVER touched or lost.
                </p>

                {removeTarget && removeTarget.status !== "stopped" && (
                  <label className="flex items-center gap-2.5 rounded-xl border border-[var(--border)] bg-[var(--surface-2)] p-3 text-xs cursor-pointer">
                    <input
                      type="checkbox"
                      checked={stopFirst}
                      onChange={(e) => setStopFirst(e.target.checked)}
                      className="h-4 w-4 rounded border-[var(--border)] accent-[var(--accent)]"
                    />
                    <span className="font-medium text-[var(--text)]">
                      Stop running processes first
                    </span>
                  </label>
                )}
              </div>
            }
          />

          {/* Command Palette Modal (Ctrl+K) */}
          <CommandPalette
            open={commandPaletteOpen}
            onClose={() => setCommandPaletteOpen(false)}
            applications={applications}
            onNavigateTab={setActiveTab}
            onStartAll={handleStartAll}
            onStopAll={handleStopAll}
          />
        </div>
      </div>
    </div>
  );
}
