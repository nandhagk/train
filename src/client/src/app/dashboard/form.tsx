"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { API } from "../api/api"


const formSchema = z.object({
  department: z.string().nonempty("Department must not be empty!"),
  den: z.string().nonempty("DEN must not be empty!"),
  nature_of_work: z.string().nonempty("Nature of work must not be empty!"),
  block: z.string().nonempty("Block must be well defined!"),
  location: z.string().nonempty(),
  preferred_starts_at: z.string(),
  preferred_ends_at: z.string(),
  requested_date: z.coerce.date(),
  requested_duration: z.coerce.number().int({message:"Duration must be a non negative integer!"}).nonnegative({message:"Duration must be a non negative integer!"}),
  priority: z.coerce.number().int({message:"Priority must be a positive integer!"}).gt(0, {message:"Priority must be a positive integer!"}),
  section_id: z.coerce.number().int("Section ID must be a positive integer!").gt(0, "Section ID must be a positive integer!")
})

export function TaskRequestForm() {
    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
			department: "Engineering",
			den: "IDK",
			nature_of_work: "Bizness",
			block: "AJR-KLM",
			location: "Lights",
			preferred_starts_at: "00:00",
			preferred_ends_at: "23:59",
			requested_date: new Date(Date.now()),
			requested_duration: 0,
			priority: 1,
			section_id: 1
        },
      })
    function onSubmit(values: z.infer<typeof formSchema>) {
		// Do something with the form values.
		// ✅ This will be type-safe and validated.
		console.log(values)
		API.requestTask({
			...values,
			preferred_starts_at: values.preferred_starts_at + ":00",
			preferred_ends_at: values.preferred_ends_at + ":00",
			requested_date: values.requested_date.toISOString().split("T")[0],
			requested_duration: {minutes:values.requested_duration}
		}).then((response: unknown) => {alert("Succesfully inserted data!"); console.log(response)}).catch((err) => {
			alert("Could not request task!");
			console.log(err);
		});
    }

  return (
    <Form {...form}>
	<form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        <FormField
			control={form.control}
			name="department"
			render={({ field }) => (
				<FormItem>
				<FormLabel>Department</FormLabel>
				<FormControl>
					<Input {...field} />
				</FormControl>
				<FormMessage />
				</FormItem>
			)}
        />
        <FormField
			control={form.control}
			name="den"
			render={({ field }) => (
				<FormItem>
				<FormLabel>DEN</FormLabel>
				<FormControl>
					<Input {...field} />
				</FormControl>
				<FormMessage />
				</FormItem>
			)}
        />
        <FormField
			control={form.control}
			name="nature_of_work"
			render={({ field }) => (
				<FormItem>
				<FormLabel>Nature of Work</FormLabel>
				<FormControl>
					<Input {...field} />
				</FormControl>
				<FormMessage />
				</FormItem>
			)}
        />
        <FormField
			control={form.control}
			name="block"
			render={({ field }) => (
				<FormItem>
				<FormLabel>Block</FormLabel>
				<FormControl>
					<Input {...field} />
				</FormControl>
				<FormMessage />
				</FormItem>
			)}
        />
        <FormField
			control={form.control}
			name="location"
			render={({ field }) => (
				<FormItem>
				<FormLabel>Location</FormLabel>
				<FormControl>
					<Input {...field} />
				</FormControl>
				<FormMessage />
				</FormItem>
			)}
        />
        <FormField
			control={form.control}
			name="preferred_starts_at"
			render={({ field }) => (
				<FormItem>
				<FormLabel>Preferred Start</FormLabel>
				<FormControl>
					<Input {...field} type="time"/>
				</FormControl>
				<FormMessage />
				</FormItem>
			)}
        />
        <FormField
			control={form.control}
			name="preferred_ends_at"
			render={({ field }) => (
				<FormItem>
				<FormLabel>Preferred End</FormLabel>
				<FormControl>
					<Input {...field} type="time"/>
				</FormControl>
				<FormMessage />
				</FormItem>
			)}
        />
        <FormField
			control={form.control}
			name="requested_date"
			render={({ field }) => (
				<FormItem>
				<FormLabel>Requested Date</FormLabel>
				<FormControl>
					{/* https://github.com/shadcn-ui/ui/issues/2385 */}
					<Input {...field} type="date" value={
                      field.value instanceof Date
                        ? field.value.toISOString().split('T')[0]
                        : field.value
                    }/>
				</FormControl>
				<FormMessage />
				</FormItem>
			)}
        />
        <FormField
			control={form.control}
			name="requested_duration"
			render={({ field }) => (
				<FormItem>
				<FormLabel>Requested Duration (Minutes)</FormLabel>
				<FormControl>
					<Input {...field} type="number"/>
				</FormControl>
				<FormMessage />
				</FormItem>
			)}
        />
        <FormField
			control={form.control}
			name="priority"
			render={({ field }) => (
				<FormItem>
				<FormLabel>Priority</FormLabel>
				<FormControl>
					<Input {...field} type="number"/>
				</FormControl>
				<FormMessage />
				</FormItem>
			)}
        />
        <FormField
			control={form.control}
			name="section_id"
			render={({ field }) => (
				<FormItem>
				<FormLabel>Section ID</FormLabel>
				<FormControl>
					<Input {...field} type="number"/>
				</FormControl>
				<FormMessage />
				</FormItem>
			)}
        />
		<Button type="submit">Submit</Button>
	</form>
    </Form>
  )
}
