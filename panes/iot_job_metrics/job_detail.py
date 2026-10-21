def run(inputs, ctx):
    connection = inputs["connection"]
    job_id = inputs["jobId"]
    
    response = ctx.aws(connection, "iot", "DescribeJob", params={"jobId": job_id})
    job = response.get("job", {})
    proc = job.get("jobProcessDetails", {})
    
    targets = []
    for target_arn in job.get("targets", []):
        target_info = {"arn": target_arn, "type": "thing", "name": target_arn}
        
        if ":thinggroup/" in target_arn:
            parts = target_arn.split(":")
            if len(parts) >= 6:
                resource = parts[-1]
                if "/" in resource:
                    _, group_name = resource.split("/", 1)
                    target_info["name"] = group_name
                    
                    try:
                        group = ctx.aws(connection, "iot", "DescribeThingGroup",
                                       params={"thingGroupName": group_name})
                        query = group.get("queryString")
                        if query:
                            target_info["type"] = "dynamic group"
                            target_info["query"] = query
                        else:
                            target_info["type"] = "static group"
                    except Exception as e:
                        target_info["type"] = "group (error)"
                        target_info["error"] = str(e)
        
        targets.append(target_info)
    
    return {
        "job_id": job.get("jobId"),
        "status": job.get("status"),
        "target_selection": job.get("targetSelection"),
        "description": job.get("description"),
        "is_concurrent": job.get("isConcurrent"),
        "processing": {
            "queued": proc.get("numberOfQueuedThings", 0),
            "in_progress": proc.get("numberOfInProgressThings", 0),
            "succeeded": proc.get("numberOfSucceededThings", 0),
            "failed": proc.get("numberOfFailedThings", 0),
            "canceled": proc.get("numberOfCanceledThings", 0),
            "rejected": proc.get("numberOfRejectedThings", 0),
            "timed_out": proc.get("numberOfTimedOutThings", 0),
            "removed": proc.get("numberOfRemovedThings", 0)
        },
        "targets": targets
    }
