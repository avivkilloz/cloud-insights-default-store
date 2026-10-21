def run(inputs, ctx):
    import time
    from datetime import datetime, timedelta
    
    conn = inputs["connection"]
    days = inputs.get("days", 7)
    
    # Get all Lambda functions
    lambdas_resp = ctx.aws(conn, "lambda", "ListFunctions", paginate=True)
    functions = lambdas_resp.get("Functions", [])
    
    # Time window for CloudWatch
    now = datetime.utcnow()
    start = now - timedelta(days=days)
    start_str = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    rows = []
    for func in functions:
        name = func["FunctionName"]
        
        # Get Invocations metric
        inv_resp = ctx.aws(conn, "cloudwatch", "GetMetricStatistics", {
            "Namespace": "AWS/Lambda",
            "MetricName": "Invocations",
            "Dimensions": [{"Name": "FunctionName", "Value": name}],
            "StartTime": start_str,
            "EndTime": end_str,
            "Period": days * 86400,
            "Statistics": ["Sum"]
        })
        
        # Get Errors metric
        err_resp = ctx.aws(conn, "cloudwatch", "GetMetricStatistics", {
            "Namespace": "AWS/Lambda",
            "MetricName": "Errors",
            "Dimensions": [{"Name": "FunctionName", "Value": name}],
            "StartTime": start_str,
            "EndTime": end_str,
            "Period": days * 86400,
            "Statistics": ["Sum"]
        })
        
        inv_datapoints = inv_resp.get("Datapoints", [])
        err_datapoints = err_resp.get("Datapoints", [])
        
        invocations = sum(d.get("Sum", 0) for d in inv_datapoints) if inv_datapoints else 0
        errors = sum(d.get("Sum", 0) for d in err_datapoints) if err_datapoints else 0
        
        error_rate = (errors / invocations * 100) if invocations > 0 else 0
        
        rows.append({
            "Function": name,
            "Invocations": invocations,
            "Errors": errors,
            "Error rate": round(error_rate, 2)
        })
    
    # Sort by error rate descending
    rows.sort(key=lambda r: r["Error rate"], reverse=True)
    ctx.log(f"Checked {len(rows)} Lambda functions")
    
    return {"rows": rows}
