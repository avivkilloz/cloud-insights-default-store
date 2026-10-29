import json
import concurrent.futures

STATUSES = ("IN_PROGRESS", "COMPLETED", "CANCELED", "SCHEDULED", "DELETION_IN_PROGRESS")


def _int(value, default):
    try:
        return max(1, int(str(value).strip()))
    except Exception:
        return default


def _pretty(doc):
    if not doc:
        return ""
    try:
        return json.dumps(json.loads(doc), indent=2)
    except Exception:
        return doc


def run(inputs, ctx):
    connections = inputs.get("connections") or []
    if not connections:
        return {"rows": [], "error": None}

    status = (inputs.get("status") or "").strip().upper()
    if status and status not in STATUSES:
        return {"rows": [], "error": f"Unknown job status '{status}'. Use one of: {', '.join(STATUSES)}."}
    max_jobs = _int(inputs.get("max_jobs"), 50)

    errors = []

    def list_jobs(conn_id):
        name = ctx.name(conn_id)
        params = {"status": status} if status else {}
        try:
            resp = ctx.aws(conn_id, "iot", "ListJobs", params=params, paginate=True)
            jobs = sorted(resp.get("jobs", []), key=lambda j: str(j.get("createdAt") or ""), reverse=True)
            return conn_id, name, jobs[:max_jobs], None
        except Exception as e:
            return conn_id, name, [], str(e)

    def enrich(conn_id, name, summary):
        job_id = summary.get("jobId")
        job, document, problems = {}, "", []
        try:
            job = ctx.aws(conn_id, "iot", "DescribeJob", params={"jobId": job_id}).get("job", {}) or {}
        except Exception as e:
            problems.append(f"DescribeJob: {e}")
        try:
            document = _pretty(ctx.aws(conn_id, "iot", "GetJobDocument", params={"jobId": job_id}).get("document"))
        except Exception as e:
            problems.append(f"GetJobDocument: {e}")

        d = job.get("jobProcessDetails") or {}
        counts = {
            "Succeeded": d.get("numberOfSucceededThings", 0),
            "Failed": d.get("numberOfFailedThings", 0),
            "In progress": d.get("numberOfInProgressThings", 0),
            "Queued": d.get("numberOfQueuedThings", 0),
            "Timed out": d.get("numberOfTimedOutThings", 0),
            "Rejected": d.get("numberOfRejectedThings", 0),
            "Canceled": d.get("numberOfCanceledThings", 0),
            "Removed": d.get("numberOfRemovedThings", 0),
        }
        total = sum(counts.values())
        row = {
            "Environment": name,
            "Job ID": job_id,
            "Status": job.get("status") or summary.get("status"),
            "Target selection": job.get("targetSelection") or summary.get("targetSelection"),
            "Description": job.get("description", ""),
            "Created": job.get("createdAt") or summary.get("createdAt"),
            "Last updated": job.get("lastUpdatedAt") or summary.get("lastUpdatedAt"),
            "Completed": job.get("completedAt") or summary.get("completedAt"),
            "Total things": total,
        }
        row.update(counts)
        row["Success %"] = round(100.0 * counts["Succeeded"] / total, 1) if total else None
        row["Job document"] = document
        if problems:
            errors.append(f"{name} / {job_id}: " + "; ".join(problems))
        return row

    work = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(connections))) as ex:
        for conn_id, name, jobs, err in ex.map(list_jobs, connections):
            if err:
                errors.append(f"{name}: {err}")
            work.extend((conn_id, name, j) for j in jobs)

    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for row in ex.map(lambda w: enrich(*w), work):
            rows.append(row)

    rows.sort(key=lambda r: str(r.get("Created") or ""), reverse=True)
    result = {"rows": rows}
    if errors:
        result["error"] = "\n".join(errors)
    return result
