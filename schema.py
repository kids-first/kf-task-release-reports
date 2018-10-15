# Responsible for storing basic logistic information about tasks
task_schema = dict(AttributeDefinitions=[
        { 'AttributeName': 'task_id', 'AttributeType': 'S' },
        { 'AttributeName': 'created_at', 'AttributeType': 'N' },
    ],
    KeySchema=[
        { 'AttributeName': 'task_id', 'KeyType': 'HASH' },
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


# Stores overview stats of the release, such as total changes per entity
release_summary_schema = dict(AttributeDefinitions=[
        { 'AttributeName': 'release_id', 'AttributeType': 'S' },
    ],
    KeySchema=[
        { 'AttributeName': 'release_id', 'KeyType': 'HASH' },
    ],
    ProvisionedThroughput={
        'ReadCapacityUnits': 1,
        'WriteCapacityUnits': 1
    },
    StreamSpecification={ 'StreamEnabled': False },
    SSESpecification={ 'Enabled': False }
)
