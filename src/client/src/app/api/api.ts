import type { PartialRequestedTask, RequestedTask, ScheduledTask } from "./models";
import { serialize, parse } from "tinyduration"

const PREFIX = "https://ftcb.in/api/"

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const deserialize_task = (data: any): RequestedTask => {
    const requested_duration = parse(data.requested_duration);
    requested_duration.hours = requested_duration.hours? requested_duration.hours : 0;
    requested_duration.minutes = requested_duration.minutes? requested_duration.minutes : 0;
    return {
        ...data,
        requested_duration: {
            minutes: requested_duration.hours * 60 + requested_duration.minutes
        }
    }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const deserialize_scheduled_task = (data: any): ScheduledTask => {
    const requested_duration = parse(data.requested_duration);
    requested_duration.hours = requested_duration.hours? requested_duration.hours : 0;
    requested_duration.minutes = requested_duration.minutes? requested_duration.minutes : 0;
    return {
        ...data,
        requested_duration: {
            minutes: requested_duration.hours * 60 + requested_duration.minutes
        }
    }
}

const get = async (route: string) => {
    const res = await fetch(PREFIX + route);
    return await res.json();
}

const del = async (route: string) => {
    const res = await fetch(PREFIX + route, { method: "DELETE" });
    return await res.json();
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const put = async (route: string, data: any) => {
    const res = await fetch(PREFIX + route, {
        method: "PUT",
        body: JSON.stringify(data)
    });
    return await res.json();
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const post = async (route: string, data: any) => {
    const res = await fetch(PREFIX + route, {
        method: "POST",
        body: JSON.stringify(data)
    });
    try{
        return await res.json();
    } catch{
        return res;
    }
}

export const API = {
    getRequestedTasks:  async () => {
        const data = await get("requested_task");
        return data.map((raw_task: unknown) => deserialize_task(raw_task));
    },
    getScheduledTasks:  async () => {
        const data = await get("scheduled_task");
        return data.map((raw_task: unknown) => deserialize_scheduled_task(raw_task));
    },

    scheduleTasks: async (ids: number[]) => {
        const data = await post("requested_task/schedule", ids);
        return data;
    },

    requestTask: async (task: PartialRequestedTask) => {
        const res = await post("requested_task", {
            ...task,
            requested_duration: serialize(task.requested_duration)
        });
        return deserialize_task(res);
    },

    deleteTask: async (task_id: number) => {
        const res = await del(`requested_task/${task_id}`);
        return deserialize_task(res);
    },

    updateTask: async (task: RequestedTask) => {
        const res = await put("requested_task", {
            ...task,
            requested_duration: serialize(task.requested_duration)
        });
        return deserialize_task(res);
    }
};
