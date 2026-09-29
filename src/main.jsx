import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { CalendarDays, Check, CirclePlus, ListChecks, Pencil, Search, Sparkles, Trash2, X } from "lucide-react";
import "./styles.css";

const starter = [
  { id: 1, title: "Review FastAPI route structure", completed: true, priority: "medium", due_date: null },
  { id: 2, title: "Polish the project README", completed: false, priority: "high", due_date: new Date().toISOString().slice(0, 10) },
  { id: 3, title: "Prepare a short demo walkthrough", completed: false, priority: "low", due_date: null },
];
const readLocal = () => JSON.parse(localStorage.getItem("momentum-tasks") || "null") || starter;
const request = async (path, options) => {
  const response = await fetch(`/api${path}`, { headers: { "Content-Type": "application/json" }, ...options });
  if (!response.ok) throw new Error("API request failed");
  return response.status === 204 ? null : response.json();
};

function App() {
  const [tasks, setTasks] = useState([]);
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState("medium");
  const [dueDate, setDueDate] = useState("");
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [notice, setNotice] = useState("");
  const [offline, setOffline] = useState(false);

  useEffect(() => { request("/tasks").then(setTasks).catch(() => { setOffline(true); setTasks(readLocal()); }); }, []);
  useEffect(() => { if (offline && tasks.length) localStorage.setItem("momentum-tasks", JSON.stringify(tasks)); }, [tasks, offline]);

  const visible = useMemo(() => tasks.filter((task) => {
    const statusMatch = filter === "all" || (filter === "done" ? task.completed : !task.completed);
    return statusMatch && task.title.toLowerCase().includes(query.toLowerCase());
  }), [tasks, filter, query]);
  const completed = tasks.filter((task) => task.completed).length;
  const progress = tasks.length ? Math.round(completed / tasks.length * 100) : 0;
  const flash = (message) => { setNotice(message); window.setTimeout(() => setNotice(""), 2000); };

  async function createTask(event) {
    event.preventDefault();
    const cleanTitle = title.trim();
    if (!cleanTitle) return;
    const payload = { title: cleanTitle, priority, due_date: dueDate || null };
    try {
      const created = offline ? { ...payload, id: Date.now(), completed: false } : await request("/tasks", { method: "POST", body: JSON.stringify(payload) });
      setTasks((current) => [created, ...current]);
      setTitle(""); setDueDate(""); setPriority("medium"); flash("Task added");
    } catch { flash("Could not add that task"); }
  }

  async function updateTask(task, changes) {
    const previous = tasks;
    setTasks(tasks.map((item) => item.id === task.id ? { ...item, ...changes } : item));
    try { if (!offline) await request(`/tasks/${task.id}`, { method: "PATCH", body: JSON.stringify(changes) }); }
    catch { setTasks(previous); flash("Update failed"); }
  }

  async function removeTask(task) {
    const previous = tasks;
    setTasks(tasks.filter((item) => item.id !== task.id)); setDeleteTarget(null);
    try { if (!offline) await request(`/tasks/${task.id}`, { method: "DELETE" }); flash("Task deleted"); }
    catch { setTasks(previous); flash("Delete failed"); }
  }

  useEffect(() => {
    const context = document.modelContext;
    if (!context?.registerTool) return;
    const lifecycle = new AbortController();
    Promise.resolve(context.registerTool({
      name: "create_task", title: "Create task", description: "Create a new task in Momentum.",
      inputSchema: { type: "object", properties: { title: { type: "string" }, priority: { enum: ["low", "medium", "high"] } }, required: ["title"], additionalProperties: false },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      async execute(input) {
        const payload = { title: input.title.trim(), priority: input.priority || "medium", due_date: null };
        if (!payload.title) throw new Error("Title is required");
        const created = offline ? { ...payload, id: Date.now(), completed: false } : await request("/tasks", { method: "POST", body: JSON.stringify(payload) });
        setTasks((current) => [created, ...current]);
        return { id: created.id, title: created.title, status: "created" };
      },
    }, { signal: lifecycle.signal })).catch(() => {});
    return () => lifecycle.abort();
  }, [offline]);

  return <main className="app-shell">
    <header className="topbar"><a className="brand" href="#top"><span className="brand-mark"><Check size={18} strokeWidth={3}/></span>Momentum</a><div className="date-chip"><CalendarDays size={16}/> {new Intl.DateTimeFormat("en", { weekday: "short", month: "short", day: "numeric" }).format(new Date())}</div></header>
    <section className="workspace" id="top">
      <aside className="summary-card">
        <div className="eyebrow"><Sparkles size={15}/> Today’s focus</div>
        <h1>Make progress,<br/><em>one task at a time.</em></h1>
        <p className="intro">Keep the important things visible and turn a busy day into a clear plan.</p>
        <div className="progress-copy"><span>{completed} of {tasks.length} complete</span><strong>{progress}%</strong></div>
        <div className="progress-track"><span style={{ width: `${progress}%` }}/></div>
        <div className="stats"><div><strong>{tasks.length - completed}</strong><span>Left to do</span></div><div><strong>{completed}</strong><span>Completed</span></div></div>
        <p className="storage-note">{offline ? "Demo mode · saved on this device" : "Synced with FastAPI"}</p>
      </aside>
      <section className="task-panel" aria-label="Task manager">
        <form className="composer" onSubmit={createTask}>
          <label htmlFor="task-title">What needs to be done?</label>
          <div className="composer-row"><input id="task-title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Add a new task…" maxLength={120}/><button className="add-button" disabled={!title.trim()}><CirclePlus size={19}/> Add task</button></div>
          <div className="task-options"><label>Priority <select value={priority} onChange={(e) => setPriority(e.target.value)}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select></label><label>Due date <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)}/></label></div>
        </form>
        <div className="toolbar">
          <div className="filters" role="group" aria-label="Filter tasks">{[["all","All"],["active","Active"],["done","Completed"]].map(([value,label]) => <button key={value} className={filter === value ? "active" : ""} onClick={() => setFilter(value)}>{label}</button>)}</div>
          <label className="search"><Search size={16}/><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search tasks" aria-label="Search tasks"/></label>
        </div>
        <div className="task-list" aria-live="polite">
          {visible.length ? visible.map((task) => <article className={`task ${task.completed ? "is-done" : ""}`} key={task.id}>
            <button className="check-button" onClick={() => updateTask(task, { completed: !task.completed })} aria-label={task.completed ? "Mark active" : "Mark complete"}>{task.completed && <Check size={16} strokeWidth={3}/>}</button>
            <div className="task-content">{editing?.id === task.id ? <form className="edit-form" onSubmit={(e) => { e.preventDefault(); updateTask(task, { title: editing.title.trim() || task.title }); setEditing(null); }}><input autoFocus value={editing.title} onChange={(e) => setEditing({ ...editing, title: e.target.value })}/><button>Save</button><button type="button" onClick={() => setEditing(null)}>Cancel</button></form> : <h2>{task.title}</h2>}<div className="meta"><span className={`priority ${task.priority}`}>{task.priority}</span>{task.due_date && <span><CalendarDays size={14}/> {new Intl.DateTimeFormat("en", { month: "short", day: "numeric" }).format(new Date(`${task.due_date}T12:00:00`))}</span>}</div></div>
            <div className="task-actions"><button onClick={() => setEditing({ id: task.id, title: task.title })} aria-label={`Edit ${task.title}`}><Pencil size={17}/></button><button className="danger" onClick={() => setDeleteTarget(task)} aria-label={`Delete ${task.title}`}><Trash2 size={17}/></button></div>
          </article>) : <div className="empty"><ListChecks size={35}/><h2>No tasks here</h2><p>{query ? "Try a different search." : "Add a task above and make a start."}</p></div>}
        </div>
      </section>
    </section>
    {deleteTarget && <div className="modal-backdrop" onMouseDown={() => setDeleteTarget(null)}><section className="modal" role="dialog" aria-modal="true" aria-labelledby="delete-title" onMouseDown={(e) => e.stopPropagation()}><button className="modal-close" onClick={() => setDeleteTarget(null)} aria-label="Close"><X size={19}/></button><div className="modal-icon"><Trash2 size={22}/></div><h2 id="delete-title">Delete this task?</h2><p>“{deleteTarget.title}” will be removed permanently.</p><div><button className="secondary" onClick={() => setDeleteTarget(null)}>Keep task</button><button className="delete-button" onClick={() => removeTask(deleteTarget)}>Delete</button></div></section></div>}
    {notice && <div className="toast" role="status"><Check size={16}/> {notice}</div>}
  </main>;
}

createRoot(document.getElementById("root")).render(<React.StrictMode><App/></React.StrictMode>);
