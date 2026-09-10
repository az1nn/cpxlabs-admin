MATCH (s:Spec {repository: $repository})
WHERE coalesce(s.enforced, false) = true
  AND NOT EXISTS { MATCH (s)-[:DECOMPOSED_INTO]->(:Task) }
RETURN 'enforced-spec-no-task' AS rule,
       s.canonicalId AS entity,
       s.sourcePath AS sourcePath,
       'Enforced spec has no decomposed tasks' AS message
UNION ALL
MATCH (t:Task {repository: $repository, status: 'done'})
WHERE NOT EXISTS { MATCH (t)-[:IMPLEMENTED_BY]->(:CodeArtifact) }
RETURN 'completed-task-no-code' AS rule,
       t.canonicalId AS entity,
       t.sourcePath AS sourcePath,
       'Completed task has no implementation artifact' AS message
UNION ALL
MATCH (t:Task {repository: $repository, status: 'done'})
WHERE NOT EXISTS { MATCH (t)-[:VALIDATED_BY]->(:Test) }
RETURN 'completed-task-no-test' AS rule,
       t.canonicalId AS entity,
       t.sourcePath AS sourcePath,
       'Completed task has no validation artifact' AS message
UNION ALL
MATCH (r:Requirement {repository: $repository, critical: true})-[:REALIZED_BY]->(s:Spec)
WHERE NOT EXISTS {
  MATCH (s)-[:DECOMPOSED_INTO]->(:Task)-[:VALIDATED_BY]->(:Test)
}
RETURN 'critical-requirement-no-test' AS rule,
       r.canonicalId AS entity,
       r.sourcePath AS sourcePath,
       'Critical requirement has no test evidence through its spec tasks' AS message
UNION ALL
MATCH (a:ADR {repository: $repository})
WHERE NOT EXISTS { MATCH (:Spec)-[:CONSTRAINED_BY]->(a) }
RETURN 'adr-no-consumer' AS rule,
       a.canonicalId AS entity,
       a.sourcePath AS sourcePath,
       'ADR has no explicit Spec consumer' AS message
ORDER BY rule, entity
