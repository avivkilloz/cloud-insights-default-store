def run(inputs, ctx):
    import concurrent.futures
    connections = inputs.get("connections", [])
    if not connections:
        return {"rows": [], "error": None}

    all_rows = []
    errors = []

    def fetch_jobs(conn_id):
        name = ctx.name(conn_id)
        try:
            resp = ctx.aws(conn_id, "iot", "ListJobs", paginate=True)
            return name, resp.get("jobs", []), None
        except Exception as e:
            return name, [], str(e)

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(connections)) as executor:
        futures = {executor.submit(fetch_jobs, c): c for c in connections}
        for fut in concurrent.futures.as_completed(futures):
            name, jobs, err = fut.result()
            if err:
                errors.append(f"{name}: {err}")
                continue
            for job in jobs:
                details = job.get("jobProcessDetails", {})
                all_rows.append({
                    "Environment": name,
                    "Job ID": job.get("jobId"),
                    "Status": job.get("status"),
                    "Created": job.get("createdAt"),
                    "Last updated": job.get("lastUpdatedAt"),
                    "Completed": job.get("completedAt"),
                    "Queued": details.get("numberOfQueuedThings", 0),
                    "In progress": details.get("numberOfInProgressThings", 0),
                    "Succeeded": details.get("numberOfSucceededThings", 0),
                    "Failed": details.get("numberOfFailedThings", 0),
                    "Canceled": details.get("numberOfCanceledThings", 0),
                    "Timed out": details.get("numberOfTimedOutThings", 0),
                    "Rejected": details.get("numberOfRejectedThings", 0),
                    "Removed": details.get("numberOfRemovedThings", 0),
                })

    result = {"rows": all_rows}
    if errors:
        result["error"] = "\n".join(errors)
    return result
