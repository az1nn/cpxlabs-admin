MATCH (n {repository: $repository})
RETURN 'node' AS kind, labels(n)[0] AS name, count(*) AS count
UNION ALL
MATCH ()-[r]->()
WHERE r.repository = $repository
RETURN 'relationship' AS kind, type(r) AS name, count(*) AS count
ORDER BY kind, name
