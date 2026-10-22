def run(inputs, ctx):
    import concurrent.futures
    
    conn_id = inputs.get("connection")
    job_id = inputs.get("jobId")
    
    if not conn_id or not job_id:
        return {"description": None, "targets": None, "document": None, "executions": []}
    
    # Fetch job details and executions in parallel
    def fetch_detail():
        try:
            return ctx.aws(conn_id, "iot", "DescribeJob", params={"jobId": job_id})
        except Exception as e:
            return {"error": str(e)}
    
    def fetch_executions():
        try:
            resp = ctx.aws(conn_id, "iot", "ListJobExecutionsForJob", params={"jobId": job_id}, paginate=True)
            return resp.get("executionSummaries", [])
        except Exception as e:
            return []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        detail_future = executor.submit(fetch_detail)
        execs_future = executor.submit(fetch_executions)
        
        detail = detail_future.result()
        executions = execs_future.result()
    
    # Format executions for the table
    exec_rows = []
    for ex in executions:
        summary = ex.get("jobExecutionSummary", {})
        exec_rows.append({
            "Thing": ex.get("thingArn", "").split(":")[-1] if ex.get("thingArn") else "",
            "Status": summary.get("status"),
            "Queued": summary.get("queuedAt"),
            "Started": summary.get("startedAt"),
            "Last updated": summary.get("lastUpdatedAt"),
            "Retries": summary.get("retryAttempt", 0)
        })
    
    # Extract job document and targets from detail
    job = detail.get("job", {}) if isinstance(detail, dict) else {}
    
    # Targets: look for targetSelection and thing/group ARNs
    targets = []
    target_selection = job.get("targetSelection", "")
    if target_selection:
        targets.append(f"Selection: {target_selection}")
    
    # Look for targets in presignedUrlConfig or other fields
    job_doc = job.get("document", "")
    
    return {
        "description": job.get("description"),
        "targets": targets if targets else None,
        "document": job_doc if job_doc else None,
        "executions": exec_rows
    }
