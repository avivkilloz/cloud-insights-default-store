def run(inputs, ctx):
    connection = inputs['connection']
    job_id = inputs['jobId']
    
    # Get job details using DescribeJob
    job_result = ctx.aws(connection, 'iot', 'DescribeJob', params={'jobId': job_id})
    job = job_result.get('job', {})
    
    # Get job document separately using GetJobDocument
    try:
        doc_result = ctx.aws(connection, 'iot', 'GetJobDocument', params={'jobId': job_id})
        job_document = doc_result.get('document', None)
    except Exception:
        job_document = None
    
    # Process targets
    targets = []
    for target in job.get('targets', []):
        # Parse target ARN to extract name and determine type
        if ':thing/' in target:
            target_type = 'Thing'
            name = target.split(':thing/')[-1]
        elif ':thinggroup/' in target:
            target_type = 'Thing Group'
            name = target.split(':thinggroup/')[-1]
        else:
            target_type = 'Unknown'
            name = target
        
        targets.append({
            'name': name,
            'type': target_type,
            'arn': target
        })
    
    return {
        'job_id': job.get('jobId'),
        'job_arn': job.get('jobArn'),
        'status': job.get('status'),
        'target_selection': job.get('targetSelection'),
        'description': job.get('description'),
        'is_concurrent': job.get('isConcurrent', False),
        'created_at': job.get('createdAt'),
        'last_updated_at': job.get('lastUpdatedAt'),
        'completed_at': job.get('completedAt'),
        'job_process_details': job.get('jobProcessDetails', {}),
        'job_document': job_document,
        'targets': targets
    }
