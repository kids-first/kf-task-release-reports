task_schema = dict(AttributeDefinitions=[
        { 'AttributeName': 'task_id', 'AttributeType': 'S' },
        { 'AttributeName': 'created_at', 'AttributeType': 'N' },
    ],
    KeySchema=[
        { 'AttributeName': 'task_id', 'KeyType': 'HASH' },
    ],
    LocalSecondaryIndexes=[
        {
            'IndexName': 'local_task_id',
            'KeySchema': [
                { 'AttributeName': 'task_id', 'KeyType': 'HASH' },
                { 'AttributeName': 'created_at', 'KeyType': 'RANGE' },
            ],
            'Projection': {
                'ProjectionType': 'KEYS_ONLY',
            }
        },
    ],
    GlobalSecondaryIndexes=[
        {
            'IndexName': 'global_task_id',
            'KeySchema': [
                { 'AttributeName': 'task_id', 'KeyType': 'HASH' },
                { 'AttributeName': 'created_at', 'KeyType': 'RANGE' },
            ],
            'Projection': {
                'ProjectionType': 'KEYS_ONLY',
            },
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1
            }
        },
    ],
    ProvisionedThroughput={
        'ReadCapacityUnits': 1,
        'WriteCapacityUnits': 1
    },
    StreamSpecification={ 'StreamEnabled': False },
    SSESpecification={ 'Enabled': False }
)
