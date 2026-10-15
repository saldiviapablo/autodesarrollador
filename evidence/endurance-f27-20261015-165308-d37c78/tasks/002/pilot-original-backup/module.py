"""Incomplete execution-report utility; synthetic data only."""
def round_seconds(value):
    return format(round(float(value), 2), '.2f')

def normalize(records):
    raise NotImplementedError('missing validation and normalization')

def summarize(records):
    raise NotImplementedError('missing report aggregation')

def markdown(summary):
    raise NotImplementedError('missing report renderer')
