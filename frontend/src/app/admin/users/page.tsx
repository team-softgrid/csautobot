"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from "react";
import { useRouter } from "next/navigation";
import {
  Pencil,
  Plus,
  RefreshCw,
  Save,
  Shield,
  Trash2,
  UserCog,
  Users,
  X,
} from "lucide-react";

type Role = "user" | "admin";

type User = {
  id: number;
  username: string;
  role: Role;
  created_at: number;
};

type UserForm = {
  username: string;
  password: string;
  role: Role;
};

const emptyForm: UserForm = {
  username: "",
  password: "",
  role: "user",
};

function formatDate(epochSeconds: number): string {
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(epochSeconds * 1000));
}

async function readError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    const { detail } = payload;

    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          if (typeof item === "object" && item !== null && "msg" in item) {
            return String((item as { msg?: unknown }).msg);
          }
          return String(item);
        })
        .join(", ");
    }
  } catch {
    // Keep the response status fallback below.
  }

  if (response.status === 401) {
    return "로그인이 만료되었습니다.";
  }
  if (response.status === 403) {
    return "관리자 권한이 필요합니다.";
  }
  return "요청 처리 중 오류가 발생했습니다.";
}

export default function UsersPage() {
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [currentUserId, setCurrentUserId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [form, setForm] = useState<UserForm>(emptyForm);

  const adminCount = useMemo(
    () => users.filter((user) => user.role === "admin").length,
    [users],
  );

  const clearSessionAndRedirect = useCallback(async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    router.replace("/login");
  }, [router]);

  const fetchCurrentUser = useCallback(async () => {
    const response = await fetch("/api/auth/me", { cache: "no-store" });

    if (response.status === 401) {
      await clearSessionAndRedirect();
      return;
    }

    if (response.ok) {
      const user = (await response.json()) as User;
      setCurrentUserId(user.id);
    }
  }, [clearSessionAndRedirect]);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch("/api/users", { cache: "no-store" });

      if (response.status === 401) {
        await clearSessionAndRedirect();
        return;
      }

      if (!response.ok) {
        throw new Error(await readError(response));
      }

      const data = (await response.json()) as User[];
      setUsers(data);
    } catch (fetchError) {
      setError(
        fetchError instanceof Error
          ? fetchError.message
          : "사용자 목록을 불러오지 못했습니다.",
      );
    } finally {
      setLoading(false);
    }
  }, [clearSessionAndRedirect]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void fetchCurrentUser();
      void fetchUsers();
    }, 0);

    return () => window.clearTimeout(timer);
  }, [fetchCurrentUser, fetchUsers]);

  const openCreateModal = () => {
    setEditingUser(null);
    setForm(emptyForm);
    setError("");
    setNotice("");
    setIsModalOpen(true);
  };

  const openEditModal = (user: User) => {
    setEditingUser(user);
    setForm({
      username: user.username,
      password: "",
      role: user.role,
    });
    setError("");
    setNotice("");
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingUser(null);
    setForm(emptyForm);
    setSaving(false);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    setNotice("");

    try {
      const isEditing = editingUser !== null;
      const url = isEditing ? `/api/users/${editingUser.id}` : "/api/users";
      const payload = isEditing
        ? {
            role: form.role,
            ...(form.password ? { password: form.password } : {}),
          }
        : {
            username: form.username.trim(),
            password: form.password,
            role: form.role,
          };

      const response = await fetch(url, {
        method: isEditing ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(await readError(response));
      }

      closeModal();
      setNotice(isEditing ? "사용자 정보가 수정되었습니다." : "사용자가 추가되었습니다.");
      await fetchUsers();
    } catch (saveError) {
      setError(
        saveError instanceof Error
          ? saveError.message
          : "사용자를 저장하지 못했습니다.",
      );
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (user: User) => {
    if (!confirm(`${user.username} 사용자를 삭제하시겠습니까?`)) {
      return;
    }

    setError("");
    setNotice("");

    try {
      const response = await fetch(`/api/users/${user.id}`, { method: "DELETE" });

      if (!response.ok) {
        throw new Error(await readError(response));
      }

      setNotice("사용자가 삭제되었습니다.");
      await fetchUsers();
    } catch (deleteError) {
      setError(
        deleteError instanceof Error
          ? deleteError.message
          : "사용자를 삭제하지 못했습니다.",
      );
    }
  };

  return (
    <div className="space-y-6" style={{ animation: "fadeIn 0.5s ease-out" }}>
      <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-cyan-400/25 bg-cyan-400/10 px-3 py-1 text-xs font-semibold text-cyan-300">
            <UserCog size={14} />
            관리자 설정
          </div>
          <h2 className="m-0 text-3xl font-bold text-slate-50">사용자 관리</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
            관리자와 일반 사용자 계정을 등록하고 권한을 조정합니다.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => void fetchUsers()}
            className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-slate-700 text-slate-300 transition hover:border-cyan-400/50 hover:text-cyan-300"
            title="새로고침"
            aria-label="새로고침"
          >
            <RefreshCw size={18} />
          </button>
          <button
            type="button"
            onClick={openCreateModal}
            className="inline-flex h-10 items-center gap-2 rounded-lg bg-cyan-500 px-4 text-sm font-bold text-slate-950 transition hover:bg-cyan-400"
          >
            <Plus size={18} />
            사용자 추가
          </button>
        </div>
      </header>

      <section className="grid gap-4 md:grid-cols-3">
        <div className="glass-panel p-5">
          <div className="text-sm text-slate-400">전체 사용자</div>
          <div className="mt-2 flex items-center gap-2 text-2xl font-bold text-slate-50">
            <Users size={22} className="text-cyan-300" />
            {users.length}
          </div>
        </div>
        <div className="glass-panel p-5">
          <div className="text-sm text-slate-400">관리자</div>
          <div className="mt-2 flex items-center gap-2 text-2xl font-bold text-slate-50">
            <Shield size={22} className="text-emerald-300" />
            {adminCount}
          </div>
        </div>
        <div className="glass-panel p-5">
          <div className="text-sm text-slate-400">일반 사용자</div>
          <div className="mt-2 text-2xl font-bold text-slate-50">
            {users.length - adminCount}
          </div>
        </div>
      </section>

      {notice && (
        <div className="rounded-lg border border-emerald-400/25 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-200">
          {notice}
        </div>
      )}
      {error && (
        <div className="rounded-lg border border-red-400/25 bg-red-400/10 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      <section className="glass-panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] border-collapse text-sm">
            <thead>
              <tr className="border-b border-white/10 bg-white/[0.03] text-left text-xs uppercase tracking-wide text-slate-400">
                <th className="px-5 py-4 font-semibold">ID</th>
                <th className="px-5 py-4 font-semibold">아이디</th>
                <th className="px-5 py-4 font-semibold">권한</th>
                <th className="px-5 py-4 font-semibold">생성일</th>
                <th className="px-5 py-4 text-right font-semibold">작업</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-5 py-10 text-center text-slate-400">
                    사용자 목록을 불러오는 중입니다.
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-5 py-10 text-center text-slate-400">
                    등록된 사용자가 없습니다.
                  </td>
                </tr>
              ) : (
                users.map((user) => (
                  <tr
                    key={user.id}
                    className="border-b border-white/5 text-slate-200 transition last:border-0 hover:bg-white/[0.03]"
                  >
                    <td className="px-5 py-4 text-slate-400">{user.id}</td>
                    <td className="px-5 py-4 font-semibold text-slate-50">
                      {user.username}
                      {user.id === currentUserId && (
                        <span className="ml-2 rounded-full bg-cyan-400/10 px-2 py-0.5 text-xs font-semibold text-cyan-300">
                          현재 계정
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-4">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-bold ${
                          user.role === "admin"
                            ? "bg-emerald-400/10 text-emerald-300"
                            : "bg-slate-600/40 text-slate-200"
                        }`}
                      >
                        {user.role === "admin" && <Shield size={12} />}
                        {user.role === "admin" ? "관리자" : "사용자"}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-slate-400">
                      {formatDate(user.created_at)}
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => openEditModal(user)}
                          className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-700 text-slate-300 transition hover:border-cyan-400/50 hover:text-cyan-300"
                          title="수정"
                          aria-label={`${user.username} 수정`}
                        >
                          <Pencil size={16} />
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleDelete(user)}
                          disabled={user.id === currentUserId}
                          className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-red-400/20 text-red-300 transition hover:border-red-300/60 hover:bg-red-400/10 disabled:cursor-not-allowed disabled:opacity-40"
                          title={
                            user.id === currentUserId
                              ? "현재 계정은 삭제할 수 없습니다"
                              : "삭제"
                          }
                          aria-label={`${user.username} 삭제`}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {isModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/75 px-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl border border-white/10 bg-slate-900 p-6 shadow-2xl">
            <div className="mb-5 flex items-center justify-between">
              <h3 className="m-0 text-lg font-bold text-slate-50">
                {editingUser ? "사용자 수정" : "사용자 추가"}
              </h3>
              <button
                type="button"
                onClick={closeModal}
                className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 transition hover:bg-white/5 hover:text-slate-100"
                title="닫기"
                aria-label="닫기"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label
                  htmlFor="username"
                  className="mb-2 block text-sm font-semibold text-slate-300"
                >
                  아이디
                </label>
                <input
                  id="username"
                  type="text"
                  minLength={3}
                  maxLength={64}
                  pattern="[a-zA-Z0-9_-]+"
                  required={!editingUser}
                  disabled={editingUser !== null}
                  value={form.username}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      username: event.target.value,
                    }))
                  }
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-slate-50 outline-none transition placeholder:text-slate-600 focus:border-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
                  placeholder="영문, 숫자, _, -"
                />
              </div>

              <div>
                <label
                  htmlFor="password"
                  className="mb-2 block text-sm font-semibold text-slate-300"
                >
                  비밀번호 {editingUser ? "(변경 시 입력)" : ""}
                </label>
                <input
                  id="password"
                  type="password"
                  minLength={8}
                  required={!editingUser}
                  value={form.password}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      password: event.target.value,
                    }))
                  }
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-slate-50 outline-none transition placeholder:text-slate-600 focus:border-cyan-400"
                  placeholder="8자 이상"
                />
              </div>

              <div>
                <label
                  htmlFor="role"
                  className="mb-2 block text-sm font-semibold text-slate-300"
                >
                  권한
                </label>
                <select
                  id="role"
                  value={form.role}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      role: event.target.value as Role,
                    }))
                  }
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-slate-50 outline-none transition focus:border-cyan-400"
                >
                  <option value="user">사용자</option>
                  <option value="admin">관리자</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={closeModal}
                  className="inline-flex h-10 items-center rounded-lg border border-slate-700 px-4 text-sm font-semibold text-slate-300 transition hover:border-slate-500 hover:text-slate-50"
                >
                  취소
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="inline-flex h-10 items-center gap-2 rounded-lg bg-cyan-500 px-4 text-sm font-bold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <Save size={16} />
                  {saving ? "저장 중" : "저장"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
