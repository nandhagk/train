import { AppSidebar } from "@/components/app-sidebar"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Separator } from "@/components/ui/separator"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { useState } from "react"

import { BrowserRouter, Route, Routes } from "react-router"

import { TaskRequestForm } from "./form"
import { SchedulingTable } from "./schedule"
import { ViewSlots } from "./view"

export default function Page() {
  const [title] = useState([]);
  // console.log(title);
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 h-4" />
          <Breadcrumb>
          <BreadcrumbList>
            {title.map(
              (name) => {
                console.log(name, "!");
                return (<><BreadcrumbItem className="hidden md:block">
                  <BreadcrumbLink href="#">
                    {name}
                  </BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator className="hidden md:block" /></>);
              }
            )}
            </BreadcrumbList>
          </Breadcrumb>
        </header>
        <div className="flex flex-1 flex-col gap-4 p-4">
        <BrowserRouter>
          <Routes>
            <Route index path="/task/request" element={<TaskRequestForm/>} />
            <Route index path="/task/schedule" element={<SchedulingTable/>} />
            <Route index path="/view/scheduled_tasks" element={<ViewSlots/>} />
          </Routes>
        </BrowserRouter>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
