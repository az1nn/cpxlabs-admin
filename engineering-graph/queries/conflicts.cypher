MATCH (a:Task {repository: $repository})-[:IMPLEMENTED_BY|VALIDATED_BY]->(artifact)
      <-[:IMPLEMENTED_BY|VALIDATED_BY]-(b:Task {repository: $repository})
WHERE a.status = 'pending'
  AND b.status = 'pending'
  AND a.canonicalId < b.canonicalId
  AND ($specId IS NULL OR (a.specId = $specId AND b.specId = $specId))
WITH a, b, collect(DISTINCT artifact.path) AS artifacts
RETURN a.canonicalId AS left,
       b.canonicalId AS right,
       artifacts
ORDER BY left, right
