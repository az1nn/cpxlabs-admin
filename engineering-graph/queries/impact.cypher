MATCH (start {repository: $repository, canonicalId: $canonicalId})
MATCH path = (start)-[*1..5]-(affected)
WHERE length(path) <= $depth
  AND affected.repository = $repository
WITH affected, min(length(path)) AS distance
RETURN labels(affected)[0] AS label,
       affected.canonicalId AS canonicalId,
       affected.sourcePath AS sourcePath,
       distance
ORDER BY distance, label, canonicalId
LIMIT $limit
