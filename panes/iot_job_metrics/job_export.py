def run(inputs, ctx):
    import json
    
    # Get the connections input and the selected row data
    connections_input = inputs.get('connections', [])
    job_id = inputs.get('jobId')
    
    results = []
    errors = []
    
    # Handle both single selection and multi-selection via the table's select mechanism
    # When action is triggered from toolbar with selected rows, inputs contain the row data
    if isinstance(connections_input, list):
        # Multi-environment case - process each
        for conn in connections_input:
            if not conn:
                continue
            try:
                _fetch_job_details(ctx, conn, job_id, results, errors)
            except Exception as e:
                errors.append({'connection': conn, 'job_id': job_id, 'error': str(e)})
    else:
        # Single connection case
        connection = connections_input
        try:
            _fetch_job_details(ctx, connection, job_id, results, errors)
        except Exception as e:
            errors.append({'connection': connection, 'job_id': job_id, 'error': str(e)})
    
    return {'jobDetails': results, 'error': errors if errors else None}

def _fetch_job_details(ctx, connection, job_id, results, errors):
    """Fetch job details and append to results."""
    if not connection or not job_id:
        return
        
    # Get full job details
    job_result = ctx.aws(connection, 'iot', 'DescribeJob', params={'jobId': job_id})
    job = job_result.get('job', {})
    job_details = job.get('jobProcessDetails', {})
    
    results.append({
        'job_id': job.get('jobId'),
        'status': job.get('status'),
        'target_selection': job.get('targetSelection'),
        'queued': job_details.get('numberOfQueuedThings', 0),
        'in_progress': job_details.get('numberOfInProgressThings', 0),
        'succeeded': job_details.get('numberOfSucceededThings', 0),
        'failed': job_details.get('numberOfFailedThings', 0),
        'canceled': job_details.get('numberOfCanceledThings', 0),
        'rejected': job_details.get('numberOfRejectedThings', 0),
        'timed_out': job_details.get('numberOfTimedOutThings', 0),
        'removed': job_details.get('numberOfRemovedThings', 0),
        'created_at': job.get('createdAt'),
        'last_updated_at': job.get('lastUpdatedAt'),
        'completed_at': job.get('completedAt'),
        'description': job.get('description'),
        'is_concurrent': job.get('isConcurrent', False),
    })
