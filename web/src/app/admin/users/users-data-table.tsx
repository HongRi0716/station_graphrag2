'use client';

import {
  ColumnDef,
  ColumnFiltersState,
  getCoreRowModel,
  getFacetedRowModel,
  getFacetedUniqueValues,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
  VisibilityState,
} from '@tanstack/react-table';
import * as React from 'react';

import { Button } from '@/components/ui/button';

import { Checkbox } from '@/components/ui/checkbox';

import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

import { User } from '@/api';

import { DataGrid, DataGridPagination } from '@/components/data-grid';
import { useAppContext } from '@/components/providers/app-provider';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { apiClient } from '@/lib/api/client';
import { cn } from '@/lib/utils';
import {
  BatteryMedium,
  Check,
  ChevronDown,
  Columns3,
  EllipsisVertical,
  Key,
  ScrollText,
  Trash,
} from 'lucide-react';
import { useFormatter, useTranslations } from 'next-intl';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FaGithub, FaGoogle } from 'react-icons/fa6';
import { UserQuotaAction } from './user-quota-action';

export function UsersDataTable({ data }: { data: User[] }) {
  const admin_users = useTranslations('admin_users');
  const { user } = useAppContext();
  const router = useRouter();
  const [rowSelection, setRowSelection] = React.useState({});
  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({});
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    [],
  );
  const format = useFormatter();
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [pagination, setPagination] = React.useState({
    pageIndex: 0,
    pageSize: 20,
  });
  const [searchValue, setSearchValue] = React.useState<string>('');
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);
  const [userToDelete, setUserToDelete] = React.useState<User | null>(null);
  const [isDeleting, setIsDeleting] = React.useState(false);

  const handleDeleteClick = (user: User) => {
    setUserToDelete(user);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!userToDelete || !userToDelete.id) return;

    setIsDeleting(true);
    try {
      await apiClient.defaultApi.usersUserIdDelete({ userId: userToDelete.id });
      setDeleteDialogOpen(false);
      setUserToDelete(null);
      // Refresh the page to reload user list
      router.refresh();
    } catch (error) {
      console.error('Failed to delete user:', error);
      alert(
        `删除用户失败: ${error instanceof Error ? error.message : String(error)}`,
      );
    } finally {
      setIsDeleting(false);
    }
  };

  const columns: ColumnDef<User>[] = React.useMemo(() => {
    const cols: ColumnDef<User>[] = [
      {
        id: 'select',
        header: ({ table }) => (
          <div className="flex items-center justify-center">
            <Checkbox
              checked={
                table.getIsAllPageRowsSelected() ||
                (table.getIsSomePageRowsSelected() && 'indeterminate')
              }
              onCheckedChange={(value) =>
                table.toggleAllPageRowsSelected(!!value)
              }
              aria-label="Select all"
            />
          </div>
        ),
        cell: ({ row }) => (
          <div className="flex items-center justify-center">
            <Checkbox
              checked={row.getIsSelected()}
              onCheckedChange={(value) => row.toggleSelected(!!value)}
              aria-label="Select row"
            />
          </div>
        ),
      },
      {
        accessorKey: 'username',
        header: admin_users('user_name'),
        cell: ({ row }) => {
          return (
            <div className="text-left">
              <div>
                {row.original.username}{' '}
                {user?.id === row.original.id && (
                  <Badge variant="destructive">Me</Badge>
                )}
              </div>
              <div className="text-muted-foreground">{row.original.email}</div>
            </div>
          );
        },
      },
      {
        accessorKey: 'id',
        header: 'ID',
      },
      {
        accessorKey: 'role',
        header: admin_users('user_role'),
        cell: ({ row }) => {
          return (
            <Badge
              className="w-18"
              variant={row.original.role === 'admin' ? 'default' : 'secondary'}
            >
              {row.original.role}
            </Badge>
          );
        },
      },
      {
        accessorKey: 'is_active',
        header: admin_users('user_status'),
        cell: ({ row }) => {
          return (
            <Check
              className={cn(
                'size-4',
                row.original.is_active ? 'text-green-500' : 'text-red-500',
              )}
            />
          );
        },
      },
      {
        accessorKey: 'registration_source',
        header: admin_users('user_source'),
        cell: ({ row }) => {
          let icon;
          switch (row.original.registration_source) {
            case 'google':
              icon = <FaGoogle className="size-4" />;
              break;
            case 'github':
              icon = <FaGithub className="size-4" />;
              break;
            default:
              icon = <Key className="size-4" />;
          }
          return (
            <Tooltip>
              <TooltipTrigger>{icon}</TooltipTrigger>
              <TooltipContent>
                {row.original.registration_source}
              </TooltipContent>
            </Tooltip>
          );
        },
      },
      {
        accessorKey: 'date_joined',
        header: admin_users('user_creation_time'),
        cell: ({ row }) =>
          row.original.date_joined
            ? format.dateTime(new Date(row.original.date_joined), 'medium')
            : '--',
      },
      {
        id: 'actions',
        enableHiding: false,
        cell: ({ row }) => (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="data-[state=open]:bg-muted text-muted-foreground flex size-8"
                size="icon"
              >
                <EllipsisVertical />
                <span className="sr-only">Open menu</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-32">
              <UserQuotaAction user={row.original}>
                <DropdownMenuItem>
                  <BatteryMedium />
                  {admin_users('user_quotas')}
                </DropdownMenuItem>
              </UserQuotaAction>
              <DropdownMenuItem asChild>
                <Link href={`/admin/audit-logs?userId=${row.original.id}`}>
                  <ScrollText /> {admin_users('user_logs')}
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                variant="destructive"
                onClick={() => handleDeleteClick(row.original)}
                disabled={user?.id === row.original.id}
              >
                <Trash /> {admin_users('user_delete')}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ),
      },
    ];
    return cols;
  }, [admin_users, format, user?.id]);

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      columnVisibility,
      rowSelection,
      columnFilters,
      pagination,
      globalFilter: searchValue,
    },
    getRowId: (row) => String(row.id),
    enableRowSelection: true,
    onRowSelectionChange: setRowSelection,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: setColumnVisibility,
    onPaginationChange: setPagination,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFacetedRowModel: getFacetedRowModel(),
    getFacetedUniqueValues: getFacetedUniqueValues(),
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex flex-row items-center gap-2">
          <Input
            placeholder={admin_users('search')}
            value={searchValue}
            onChange={(e) => setSearchValue(e.currentTarget.value)}
          />
        </div>
        <div className="flex items-center gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                <Columns3 />
                <ChevronDown />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              {table
                .getAllColumns()
                .filter(
                  (column) =>
                    typeof column.accessorFn !== 'undefined' &&
                    column.getCanHide(),
                )
                .map((column) => {
                  return (
                    <DropdownMenuCheckboxItem
                      key={column.id}
                      className="capitalize"
                      checked={column.getIsVisible()}
                      onCheckedChange={(value) =>
                        column.toggleVisibility(!!value)
                      }
                    >
                      {String(column.columnDef.header)}
                    </DropdownMenuCheckboxItem>
                  );
                })}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
      <DataGrid table={table} />
      <DataGridPagination table={table} />

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除用户</AlertDialogTitle>
            <AlertDialogDescription>
              此操作无法撤销。这将永久删除用户{' '}
              <strong>{userToDelete?.username || userToDelete?.email}</strong>{' '}
              及其所有数据。
              {userToDelete?.role === 'admin' && (
                <div className="mt-2 text-amber-600">
                  警告：您正在删除一个管理员用户。
                </div>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? '删除中...' : '确认删除'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
