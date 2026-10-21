def run(inputs, ctx):
    import json
    
    connection = inputs["connection"]["id"] if isinstance(inputs["connection"], dict) else inputs["connection"]
    job_id = inputs["jobId"]
    
    # Get job details
    job_resp = ctx.aws(connection, "iot", "DescribeJob", params={"jobId": job_id})
    job = job_resp.get("job", {})
    
    # Get job document
    try:
        doc_resp = ctx.aws(connection, "iot", "GetJobDocument", params={"jobId": job_id})
        job_document = doc_resp.get("document", {})
    except Exception:
        job_document = {}
    
    # Build targets list from the job's targets
    targets = []
    for target in job.get("targets", []):
        # Parse target ARN to determine type
        if target.startswith("arn:aws:iot"):
            if ":thinggroup/" in target:
                parts = target.split("thinggroup/")
                name = parts[-1].split(":")[0] if ":" in parts[-1] else parts[-1]
                targets.append({"name": name, "type": "Thing Group", "query": None})
            elif ":thing/" in target:
                parts = target.split("thing/")
                name = parts[-1]
                targets.append({"name": name, "type": "Thing", "query": None})
        elif target.startswith("arn:aws:iam"):
            targets.append({"name": target.split("/")[-1], "type": "ARN", "query": None})
        else:
            targets.append({"name": target, "type": "Unknown", "query": None})
    
    # Add thing group query if available
    for t in targets:
        if t["type"] == "Thing Group" and job.get("thingGroupId"):
            t["query"] = job.get("thingGroupId")
    
    processing = job.get("jobProcessDetails", {})
    
    return {
        "detail": {
            "job_id": job.get("jobId"),
            "status": job.get("status"),
            "target_selection": job.get("targetSelection"),
            "description": job.get("description"),
            "is_concurrent": job.get("isConcurrent", False),
            "job_document": job_document,
            "targets": targets,
            "processing": {
                "queued": processing.get("numberOfQueuedThings", 0),
                "in_progress": processing.get("numberOfInProgressThings", 0),
                "succeeded": processing.get("numberOfSucceededThings", 0),
                "failed": processing.get("numberOfFailedThings", 0),
                "canceled": processing.get("numberOfCanceledThings", 0),
                "rejected": processing.get("numberOfRejectedThings", 0),
                "timed_out": processing.get("numberOfTimedOutThings", 0),
                "removed": processing.get("numberOfRemovedThings", 0),
            }
        }
    }
