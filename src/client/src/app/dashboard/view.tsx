"use client"

import * as React from "react"
import {
	ColumnDef,
	ColumnFiltersState,
	SortingState,
	VisibilityState,
	flexRender,
	getCoreRowModel,
	getFilteredRowModel,
	getPaginationRowModel,
	getSortedRowModel,
	useReactTable,
} from "@tanstack/react-table"
import { ArrowUpDown, ChevronDown } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
	DropdownMenu,
	DropdownMenuCheckboxItem,
	DropdownMenuContent,
	DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "@/components/ui/table"

import { ScheduledTask, Slot } from "../api/models"
import { API } from "../api/api"
import { useNavigate } from "react-router"


// eslint-disable-next-line react-refresh/only-export-components
export const columns: ColumnDef<ScheduledTask>[] = [
	{
		id: "select",
		header: ({ table }) => (
		<Checkbox
		checked={
			table.getIsAllPageRowsSelected() ||
			(table.getIsSomePageRowsSelected() && "indeterminate")
		}
		onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
		aria-label="Select all"
		/>
	),
		cell: ({ row }) => (
			<Checkbox
			checked={row.getIsSelected()}
			onCheckedChange={(value) => row.toggleSelected(!!value)}
			aria-label="Select row"
			/>
		),
		enableSorting: false,
		enableHiding: false,
	},
	{
		accessorKey: "id",
		header: ({column}) => {
			return (
				<Button
					variant="ghost"
					onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
				>
					ID
					<ArrowUpDown />
				</Button>
				)
		},
		cell: ({ row }) => (
			<div className="capitalize">{row.getValue("id")}</div>
		),
		enableSorting: true,
		enableHiding: true
	},
	{
		accessorKey: "requested_date",
		header: ({column}) => {
			return (
				<Button
					variant="ghost"
					onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
				>
					Date
					<ArrowUpDown />
				</Button>
				)
		},
		cell: ({ row }) => <div>{row.getValue("requested_date")}</div>,
		enableHiding: true,
		enableSorting: true
	},
    {
		accessorKey: "slots",
		header: "Start",
		cell: ({ row }) => <div>{(row.getValue("slots") as Slot[])[0].starts_at}</div>,
		enableHiding: true
	},
	{
		accessorKey: "slots",
		header: "End",
		cell: ({ row }) => <div>{(row.getValue("slots") as Slot[])[0].ends_at}</div>,
		enableHiding: true
	},
	{
		accessorKey: "priority",
		header: ({column}) => {
			return (
				<Button
					variant="ghost"
					onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
				>
					Priority
					<ArrowUpDown />
				</Button>
				)
		},
		cell: ({ row }) => <div>{row.getValue("priority")}</div>,
		enableHiding: true,
		enableSorting: true
	},
	{
		accessorKey: "department",
		header: "Department",
		cell: ({ row }) => <div>{row.getValue("department")}</div>,
		enableHiding: true
	},
	{
		accessorKey: "den",
		header: "DEN",
		cell: ({ row }) => <div>{row.getValue("den")}</div>,
		enableHiding: true
	},
	{
		accessorKey: "nature_of_work",
		header: "Nature of Work",
		cell: ({ row }) => <div>{row.getValue("nature_of_work")}</div>,
		enableHiding: true
	},
	{
		accessorKey: "block",
		header: "Block",
		cell: ({ row }) => <div>{row.getValue("block")}</div>,
		enableHiding: true
	},
	{
		accessorKey: "section_id",
		header: "Section ID",
		cell: ({ row }) => <div>{row.getValue("section_id")}</div>,
		enableHiding: true
	},
	{
		accessorKey: "location",
		header: "Location",
		cell: ({ row }) => <div>{row.getValue("location")}</div>,
		enableHiding: true
	},
	{
		accessorKey: "preferred_starts_at",
		header: "Preferred Start",
		cell: ({ row }) => <div>{row.getValue("preferred_starts_at")}</div>,
		enableHiding: true
	},
	{
		accessorKey: "preferred_ends_at",
		header: "Preferred End",
		cell: ({ row }) => <div>{row.getValue("preferred_ends_at")}</div>,
		enableHiding: true
	}
]

export function ViewSlots() {
	const [sorting, setSorting] = React.useState<SortingState>([])
	const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([])
	const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({})
	const [rowSelection, setRowSelection] = React.useState({})
	const [data, setData] = React.useState<ScheduledTask[]>([]);
	const table = useReactTable({
		data: data,
		columns,
		onSortingChange: setSorting,
		onColumnFiltersChange: setColumnFilters,
		getCoreRowModel: getCoreRowModel(),
		getPaginationRowModel: getPaginationRowModel(),
		getSortedRowModel: getSortedRowModel(),
		getFilteredRowModel: getFilteredRowModel(),
		onColumnVisibilityChange: setColumnVisibility,
		onRowSelectionChange: setRowSelection,
		state: {
			sorting,
			columnFilters,
			columnVisibility,
			rowSelection,
		},
	});


	const navigate = useNavigate();
	React.useEffect(() => {
		API.getScheduledTasks().then((tasks) => {
			setData(() => {return tasks;});
            console.log(tasks);
		}).catch(() => {
			alert("FAILED TO FETCH!")
		})
	}, [])

	const getSelectedTaskIDs = () => {
		const tasks: number[] = [];
		Object.keys(rowSelection).forEach((key) => {
			tasks.push(data[Number(key)].id);
		})
		return tasks;
	}

	return (
	<div className="w-full">
		<div className="flex items-center py-4">
		<div className="space-x-2">
			<Button variant="outline" onClick={async () => {
				await API.scheduleTasks(getSelectedTaskIDs()).then((res) => {console.log(res);  alert("Sucessfully scheduled task!")}).catch((err) => {alert("ERROR in scheduling!"); console.error(err);});
				navigate(0);
			}} disabled={Object.keys(rowSelection).length == 0}>Schedule!</Button>
			<Button variant="outline" onClick={async () => {
				for (const id of getSelectedTaskIDs()){
					console.log(id);
					await API.deleteTask(id).then((res) => {console.log(res); alert("Sucessfully deleted task!")}).catch((err) => {alert("ERROR in deleting!"); console.error(err)})
				}
				navigate(0);
			}} disabled={Object.keys(rowSelection).length == 0}>Delete!</Button>
		</div>
		<DropdownMenu>
			<DropdownMenuTrigger asChild>
			<Button variant="outline" className="ml-auto">
				Columns <ChevronDown />
			</Button>
			</DropdownMenuTrigger>
			<DropdownMenuContent className="opacity-100" align="end">
			{table
				.getAllColumns()
				.filter((column) => column.getCanHide())
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
					{column.id}
					</DropdownMenuCheckboxItem>
				)
				})}
			</DropdownMenuContent>
		</DropdownMenu>
		</div>
		<div className="rounded-md border">
		<Table>
			<TableHeader>
			{table.getHeaderGroups().map((headerGroup) => (
				<TableRow key={headerGroup.id}>
				{headerGroup.headers.map((header) => {
					return (
					<TableHead key={header.id}>
						{header.isPlaceholder
						? null
						: flexRender(
							header.column.columnDef.header,
							header.getContext()
							)}
					</TableHead>
					)
				})}
				</TableRow>
			))}
			</TableHeader>
			<TableBody>
			{table.getRowModel().rows?.length ? (
				table.getRowModel().rows.map((row) => (
				<TableRow
					key={row.id}
					data-state={row.getIsSelected() && "selected"}
				>
					{row.getVisibleCells().map((cell) => (
					<TableCell key={cell.id}>
						{flexRender(
						cell.column.columnDef.cell,
						cell.getContext()
						)}
					</TableCell>
					))}
				</TableRow>
				))
			) : (
				<TableRow>
				<TableCell
					colSpan={columns.length}
					className="h-24 text-center"
				>
					No results.
				</TableCell>
				</TableRow>
			)}
			</TableBody>
		</Table>
		</div>
		<div className="flex items-center justify-end space-x-2 py-4">
		<div className="flex-1 text-sm text-muted-foreground">
			{table.getFilteredSelectedRowModel().rows.length} of{" "}
			{table.getFilteredRowModel().rows.length} row(s) selected.
		</div>
		<div className="space-x-2">
			<Button
			variant="outline"
			size="sm"
			onClick={() => table.previousPage()}
			disabled={!table.getCanPreviousPage()}
			>
			Previous
			</Button>
			<Button
			variant="outline"
			size="sm"
			onClick={() => table.nextPage()}
			disabled={!table.getCanNextPage()}
			>
			Next
			</Button>
		</div>
		</div>
	</div>
	)
}
