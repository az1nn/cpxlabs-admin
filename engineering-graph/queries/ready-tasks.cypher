MATCH (t:Task {repository: $repository})
WHERE t.status = 'pending'
  AND ($specId IS NULL OR t.specId = $specId)
OPTIONAL MATCH (t)-[:DEPENDS_ON]->(dependency:Task {repository: $repository})
WITH t, [d IN collect(DISTINCT dependency) WHERE d IS NOT NULL AND d.status <> 'done' | d.canonicalId] AS blockers
RETURN t.canonicalId AS task,
       t.sourceId AS sourceId,
       t.title AS title,
       t.priority AS priority,
       blockers,
       size(blockers) = 0 AS ready
ORDER BY ready DESC, coalesce(t.priority, 1000000), task
