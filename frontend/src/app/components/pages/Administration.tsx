import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Users, Trash2, Edit, UserPlus, Mail } from 'lucide-react';
import { useAuth } from '../../lib/auth-context';
import { listUsers, createUser, updateUser, deleteUser } from '../../services/users.service';
import type { UserRead, TenantUserRole } from '../../lib/api-types';
import { formatDate } from '../../lib/format';
import { toast } from 'sonner';
import { useTranslation } from 'react-i18next';
import { validateEmail, validateName, validatePhone } from '../../lib/validation';
import { messageForError } from '../../lib/error-messages';

const STATUS_STYLES: Record<string, string> = {
  active: 'bg-emerald-100 text-emerald-700',
  invited: 'bg-amber-100 text-amber-700',
  pending_verification: 'bg-blue-100 text-blue-700',
};

function StatusBadge({ status }: { status: string }) {
  const { t } = useTranslation('admin');
  const cls = STATUS_STYLES[status] ?? 'bg-slate-100 text-slate-600';
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${cls}`}>
      {t(`users.status_${status}`, { defaultValue: status })}
    </span>
  );
}

export function Administration() {
  const { t } = useTranslation('admin');
  const [users, setUsers] = useState<UserRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<UserRead | null>(null);

  const { user: currentUser } = useAuth();
  const isAdmin = currentUser?.role === 'admin' || currentUser?.role === 'superadmin';

  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    role: 'dispatcher' as TenantUserRole,
    phone: '',
  });

  const [editData, setEditData] = useState({
    fullName: '',
    phone: '',
    role: 'dispatcher' as TenantUserRole,
  });

  const [inviteErrors, setInviteErrors] = useState<{
    fullName?: string;
    email?: string;
    phone?: string;
  }>({});

  const loadUsers = async () => {
    setLoading(true);
    try {
      const data = await listUsers({ pageSize: 100 });
      setUsers(data.items);
    } catch {
      toast.error(t('users.failedLoad'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadUsers(); }, []);

  const validateInvite = (): boolean => {
    const next: { fullName?: string; email?: string; phone?: string } = {};
    const nameErr = validateName(formData.fullName);
    if (nameErr) next.fullName = nameErr;
    const emailErr = validateEmail(formData.email);
    if (emailErr) next.email = emailErr;
    const phoneErr = validatePhone(formData.phone); // optional — empty is valid
    if (phoneErr) next.phone = phoneErr;
    setInviteErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateInvite()) return;
    try {
      await createUser(formData);
      setIsAddOpen(false);
      setFormData({ fullName: '', email: '', role: 'dispatcher', phone: '' });
      setInviteErrors({});
      toast.success(t('users.inviteSent'));
      loadUsers();
    } catch (err: unknown) {
      toast.error(messageForError(err));
    }
  };

  const openEdit = (u: UserRead) => {
    setEditingUser(u);
    setEditData({ fullName: u.fullName, phone: u.phone ?? '', role: u.role as TenantUserRole });
    setIsEditOpen(true);
  };

  const handleEditUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;
    try {
      await updateUser(editingUser.id, editData);
      setIsEditOpen(false);
      loadUsers();
    } catch {
      toast.error(t('users.failedUpdate'));
    }
  };

  const handleDelete = async (u: UserRead) => {
    if (!window.confirm(t('users.confirmRemove', { name: u.fullName }))) return;
    try {
      await deleteUser(u.id);
      loadUsers();
    } catch {
      toast.error(t('users.failedDelete'));
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">{t('users.title')}</h1>
          <p className="text-slate-600">{t('users.subtitle')}</p>
        </div>
        {isAdmin && (
          <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
            <DialogTrigger asChild>
              <Button>
                <UserPlus className="mr-2 size-4" />
                {t('users.inviteUser')}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{t('users.inviteTitle')}</DialogTitle>
              </DialogHeader>
              <p className="text-sm text-slate-500 -mt-1">
                {t('users.inviteHint')}
              </p>
              <form onSubmit={handleAddUser} className="space-y-4 pt-1">
                <div className="space-y-1">
                  <Input
                    placeholder={t('users.fullName')}
                    required
                    value={formData.fullName}
                    onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                    aria-invalid={!!inviteErrors.fullName}
                  />
                  {inviteErrors.fullName && (
                    <p className="text-xs text-red-600">{inviteErrors.fullName}</p>
                  )}
                </div>
                <div className="space-y-1">
                  <Input
                    type="email"
                    placeholder={t('users.workEmail')}
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    aria-invalid={!!inviteErrors.email}
                  />
                  {inviteErrors.email && (
                    <p className="text-xs text-red-600">{inviteErrors.email}</p>
                  )}
                </div>
                <div className="space-y-1">
                  <Input
                    placeholder={t('users.phoneOptional')}
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    aria-invalid={!!inviteErrors.phone}
                  />
                  {inviteErrors.phone && (
                    <p className="text-xs text-red-600">{inviteErrors.phone}</p>
                  )}
                </div>
                <Select
                  value={formData.role}
                  onValueChange={(val) => setFormData({ ...formData, role: val as TenantUserRole })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={t('users.role')} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="admin">{t('users.role_admin')}</SelectItem>
                    <SelectItem value="operator">{t('users.role_operator')}</SelectItem>
                    <SelectItem value="dispatcher">{t('users.role_dispatcher')}</SelectItem>
                  </SelectContent>
                </Select>
                <div className="pt-2 flex justify-end gap-2">
                  <Button type="button" variant="outline" onClick={() => setIsAddOpen(false)}>
                    {t('users.cancel')}
                  </Button>
                  <Button type="submit">
                    <Mail className="mr-1.5 size-4" />
                    {t('users.sendInvitation')}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="size-5" />
            {t('users.registeredUsers')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-slate-500 text-sm">{t('users.loadingUsers')}</p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t('users.colName')}</TableHead>
                    <TableHead>{t('users.colEmail')}</TableHead>
                    <TableHead>{t('users.colRole')}</TableHead>
                    <TableHead>{t('users.colStatus')}</TableHead>
                    <TableHead>{t('users.colPhone')}</TableHead>
                    <TableHead>{t('users.colJoined')}</TableHead>
                    {isAdmin && <TableHead className="text-right">{t('users.colActions')}</TableHead>}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((u) => (
                    <TableRow key={u.id}>
                      <TableCell className="font-medium">{u.fullName}</TableCell>
                      <TableCell>{u.email}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="capitalize">{t(`users.role_${u.role}`, { defaultValue: u.role })}</Badge>
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={u.status ?? 'active'} />
                      </TableCell>
                      <TableCell>{u.phone ?? '—'}</TableCell>
                      <TableCell>{formatDate(u.createdAt)}</TableCell>
                      {isAdmin && (
                        <TableCell className="text-right">
                          <Button variant="ghost" size="icon" onClick={() => openEdit(u)}>
                            <Edit className="size-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-red-500"
                            onClick={() => handleDelete(u)}
                          >
                            <Trash2 className="size-4" />
                          </Button>
                        </TableCell>
                      )}
                    </TableRow>
                  ))}
                  {users.length === 0 && (
                    <TableRow>
                      <TableCell
                        colSpan={isAdmin ? 7 : 6}
                        className="text-center text-slate-500 py-4"
                      >
                        {t('users.noUsers')}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Edit Dialog */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('users.editUser')}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleEditUser} className="space-y-4">
            <Input
              placeholder={t('users.fullName')}
              required
              value={editData.fullName}
              onChange={(e) => setEditData({ ...editData, fullName: e.target.value })}
            />
            <Input
              placeholder={t('users.phone')}
              value={editData.phone}
              onChange={(e) => setEditData({ ...editData, phone: e.target.value })}
            />
            <Select
              value={editData.role}
              onValueChange={(val) => setEditData({ ...editData, role: val as TenantUserRole })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="admin">{t('users.role_admin')}</SelectItem>
                <SelectItem value="operator">{t('users.role_operator')}</SelectItem>
                <SelectItem value="dispatcher">{t('users.role_dispatcher')}</SelectItem>
                <SelectItem value="passenger">{t('users.role_passenger')}</SelectItem>
              </SelectContent>
            </Select>
            <div className="pt-4 flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setIsEditOpen(false)}>
                {t('users.cancel')}
              </Button>
              <Button type="submit">{t('users.saveChanges')}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
