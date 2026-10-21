def run(inputs, ctx):
    connection = inputs.get("connection")
    job_id = inputs.get("jobId")
    
    if not connection or not job_id:
        return {"error": "Missing connection or jobId"}
    
    result = ctx.aws(connection, "iot", "DescribeJob", {"jobId": job_id})
    job = result.get("job", {})
    
    # Build targets list
    targets = []
    for target in job.get("targets", []):
        target_type = "unknown"
        name = target
        
        if "/thing/" in target or target.endswith("/*"):
            target_type = "thing"
            name = target.split("/")[-1]
        elif "/thinggroup/" in target:
            target_type = "thing_group"
            name = target.split("/")[-1]
        
        targets.append({
            "name": name,
            "type": target_type,
            "arn": target
        })
    
    # Get job document content
    job_document = None
    document_source = result.get("documentSource")
    if document_source:
        # documentSource may be a presigned S3 URL - fetch it
        if document_source.startswith("http://") or document_source.startswith("https://"):
            try:
                resp = ctx.http(None, document_source, method="GET")
                if resp.status == 200:
                    job_document = resp.json()
                else:
                    job_document = {"error": f"Could not fetch document: {resp.status}"}
            except Exception as e:
                job_document = {"error": str(e)}
        else:
            # It's the document itself as a string (JSON)
            try:
                import json
                job_document = json.loads(document_source)
            except:
                job_document = document_source
    
    if job_document is None:
        # Fall back to document field in job
        job_document = job.get("document")
    
    return {
        "rows": [{
            "job_id": job.get("jobId"),
            "status": job.get("status"),
            "target_selection": job.get("targetSelection"),
            "description": job.get("description", ""),
            "is_concurrent": job.get("isConcurrent", False),
            "job_document": job_document,
            "job_process_details": job.get("jobProcessDetails", {}),
            "targets": targets,
            "created_at": job.get("createdAt"),
            "last_updated_at": job.get("lastUpdatedAt"),
            "completed_at": job.get("completedAt")
        }]
    }
