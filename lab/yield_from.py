
id_batches = [[2, 3, 5], [7, 11], []]
def query_ids():
    "Presume this function returns paginated queries of ids."
    return id_batches.pop(0)

def batch_iter(producer):
    "Yields ids until none are left."
    while True:
        if results := producer():
            yield from results
        else:
            break

# Iterate directly over batched values:
for item in batch_iter(query_ids):
    print(item)
