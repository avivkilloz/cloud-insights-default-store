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
    rows.sort(key=lambda r: (str(r.get("Status") or ""), r["Thing"]))
    return {"executions": rows}
