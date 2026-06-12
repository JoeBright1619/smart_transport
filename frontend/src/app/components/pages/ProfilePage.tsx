import { useEffect, useState } from 'react';
import { UserCircle, Pencil, Check, X } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { useAuth } from '../../lib/auth-context';
import { getUser, updateUser } from '../../services/users.service';
import type { UserRead } from '../../lib/api-types';

type EditingField = 'fullName' | 'phone' | null;

export function ProfilePage() {
  const { user, updateProfile } = useAuth();
  const [serverUser, setServerUser] = useState<UserRead | null>(null);
  const [editing, setEditing] = useState<EditingField>(null);
  const [draft, setDraft] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!user) return;
    getUser(user.id).then(setServerUser).catch(() => {});
  }, [user?.id]);

  if (!user) return null;

  const display = serverUser ?? user;

  function startEdit(field: EditingField, current: string) {
    setEditing(field);
    setDraft(current ?? '');
  }

  function cancelEdit() {
    setEditing(null);
    setDraft('');
  }

  async function saveEdit() {
    if (!editing) return;
    setSaving(true);
    try {
      const patch =
        editing === 'fullName'
          ? { fullName: draft.trim() }
          : { phone: draft.trim() || undefined };
      const updated = await updateUser(user.id, patch);
      setServerUser(updated);
      updateProfile({ fullName: updated.fullName, phone: updated.phone ?? undefined });
      setEditing(null);
      toast.success('Saved');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Unable to save');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-lg space-y-6">
      <div>
        <h1 className="text-2xl font-bold">My Profile</h1>
        <p className="text-slate-600">Your account details</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UserCircle className="size-5" />
            Personal Information
          </CardTitle>
        </CardHeader>
        <CardContent className="divide-y">
          <ProfileRow
            label="Full name"
            value={display.fullName}
            field="fullName"
            editing={editing}
            draft={draft}
            saving={saving}
            onEdit={startEdit}
            onDraftChange={setDraft}
            onSave={() => void saveEdit()}
            onCancel={cancelEdit}
          />
          <ProfileRow
            label="Email address"
            value={display.email}
            editing={editing}
            draft={draft}
            saving={saving}
            onEdit={startEdit}
            onDraftChange={setDraft}
            onSave={() => void saveEdit()}
            onCancel={cancelEdit}
          />
          <ProfileRow
            label="Phone number"
            value={display.phone ?? ''}
            field="phone"
            placeholder="e.g. +250 7XX XXX XXX"
            editing={editing}
            draft={draft}
            saving={saving}
            onEdit={startEdit}
            onDraftChange={setDraft}
            onSave={() => void saveEdit()}
            onCancel={cancelEdit}
          />
          <ProfileRow
            label="Role"
            value={user.role.charAt(0).toUpperCase() + user.role.slice(1)}
            editing={editing}
            draft={draft}
            saving={saving}
            onEdit={startEdit}
            onDraftChange={setDraft}
            onSave={() => void saveEdit()}
            onCancel={cancelEdit}
          />
        </CardContent>
      </Card>
    </div>
  );
}

type ProfileRowProps = {
  label: string;
  value: string;
  field?: EditingField;
  placeholder?: string;
  editing: EditingField;
  draft: string;
  saving: boolean;
  onEdit: (field: EditingField, current: string) => void;
  onDraftChange: (v: string) => void;
  onSave: () => void;
  onCancel: () => void;
};

function ProfileRow({
  label,
  value,
  field,
  placeholder,
  editing,
  draft,
  saving,
  onEdit,
  onDraftChange,
  onSave,
  onCancel,
}: ProfileRowProps) {
  const isEditing = field !== undefined && editing === field;

  return (
    <div className="flex items-center gap-3 py-3">
      <div className="flex-1 min-w-0">
        <p className="text-xs text-slate-400 mb-0.5">{label}</p>
        {isEditing ? (
          <Input
            autoFocus
            value={draft}
            onChange={(e) => onDraftChange(e.target.value)}
            placeholder={placeholder}
            className="h-8 text-sm"
            onKeyDown={(e) => {
              if (e.key === 'Enter') onSave();
              if (e.key === 'Escape') onCancel();
            }}
          />
        ) : (
          <p className="text-sm font-medium text-slate-800 truncate">
            {value || <span className="text-slate-400 italic">Not set</span>}
          </p>
        )}
      </div>

      {isEditing ? (
        <div className="flex shrink-0 gap-1">
          <Button
            size="icon"
            variant="ghost"
            className="size-8 text-emerald-600 hover:text-emerald-700"
            onClick={onSave}
            disabled={saving}
          >
            <Check className="size-4" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className="size-8 text-slate-400 hover:text-slate-600"
            onClick={onCancel}
            disabled={saving}
          >
            <X className="size-4" />
          </Button>
        </div>
      ) : field !== undefined ? (
        <Button
          size="icon"
          variant="ghost"
          className="size-8 shrink-0 text-slate-400 hover:text-slate-600"
          onClick={() => onEdit(field, value)}
          disabled={editing !== null}
        >
          <Pencil className="size-3.5" />
        </Button>
      ) : null}
    </div>
  );
}
