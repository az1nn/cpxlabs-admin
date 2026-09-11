MATCH (task:Task {repository: $repository, canonicalId: $taskId})
OPTIONAL MATCH (spec:Spec {repository: $repository})-[:DECOMPOSED_INTO]->(task)
OPTIONAL MATCH (requirement:Requirement {repository: $repository})-[:REALIZED_BY]->(spec)
OPTIONAL MATCH (spec)-[:CONSTRAINED_BY]->(adr:ADR {repository: $repository})
OPTIONAL MATCH (task)-[:DEPENDS_ON]->(dependency:Task {repository: $repository})
OPTIONAL MATCH (task)-[:IMPLEMENTED_BY]->(code:CodeArtifact {repository: $repository})
OPTIONAL MATCH (task)-[:VALIDATED_BY]->(test:Test {repository: $repository})
OPTIONAL MATCH (pr:PullRequest {repository: $repository})-[:IMPLEMENTS]->(task)
RETURN properties(task) AS task,
       properties(spec) AS spec,
       collect(DISTINCT properties(requirement)) AS requirements,
       collect(DISTINCT properties(adr)) AS adrs,
       collect(DISTINCT properties(dependency)) AS dependencies,
       collect(DISTINCT properties(code)) AS code,
       collect(DISTINCT properties(test)) AS tests,
       collect(DISTINCT properties(pr)) AS pullRequests
