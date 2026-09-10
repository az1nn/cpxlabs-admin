MATCH (pr:PullRequest {repository: $repository, canonicalId: $canonicalId})
OPTIONAL MATCH (pr)-[:IMPLEMENTS]->(task:Task)<-[:DECOMPOSED_INTO]-(spec:Spec)
OPTIONAL MATCH (requirement:Requirement)-[:REALIZED_BY]->(spec)
OPTIONAL MATCH (pr)-[:CHANGES]->(artifact)
RETURN properties(pr) AS pullRequest,
       collect(DISTINCT task.canonicalId) AS tasks,
       collect(DISTINCT spec.canonicalId) AS specs,
       collect(DISTINCT requirement.canonicalId) AS requirements,
       collect(DISTINCT artifact.path) AS changedArtifacts
