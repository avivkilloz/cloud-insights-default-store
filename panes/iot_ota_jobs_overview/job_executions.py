def run(inputs, ctx):
    conn_id = inputs.get("connection")
    job_id = inputs.get("jobId")
    if not conn_id or not job_id:
        return {"executions": []}

    try:
        resp = ctx.aws(conn_id, "iot", "ListJobExecutionsForJob", params={"jobId": job_id}, paginate=True)
    except Exception as e:
        return {"executions": [], "error": str(e)}

    rows = []
    for ex in resp.get("executionSummaries", []):
        s = ex.get("jobExecutionSummary", {}) or {}
        arn = ex.get("thingArn") or ""
        rows.append({
            "Thing": arn.split("/")[-1] if arn else "",
            "Status": s.get("status"),
            "Queued": s.get("queuedAt"),
            "Started": s.get("startedAt"),
            "Last updated": s.get("lastUpdatedAt"),
            "Execution #": s.get("executionNumber"),
            "Retries": s.get("retryAttempt", 0),
        })
    rows.sort(key=lambda r: (str(r.get("Status") or ""), r["Thing"]))
    return {"executions": rows}
